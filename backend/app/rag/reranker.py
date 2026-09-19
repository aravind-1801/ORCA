"""
ORCA RAG XGBoost Re-ranker.

Features used per candidate:
  - cosine_score    (float, from FAISS)
  - category_match  (0/1 — does candidate category match query intent?)
  - tag_overlap     (float, fraction of query tokens in candidate tags)
  - text_length     (float, normalised document length)
  - query_len       (float, normalised query token count)

Trained on synthetic data generated from the knowledge base itself —
no external labelling required.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("orca.rag.reranker")

_MODEL_DIR = Path("backend/rag/models")
_MODEL_FILE = _MODEL_DIR / "reranker.ubj"

# ── Module-level singleton ────────────────────────────────────────────────────
_booster = None   # xgboost.Booster

# Category keywords for intent-matching
_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "safety": ["safe", "danger", "warning", "life", "jacket", "storm", "cyclone",
               "vhf", "distress", "monsoon", "ban", "night", "wave", "wind",
               "பாதுகாப்பு", "எச்சரிக்கை", "സുരക്ഷ", "മുന്നറിയിപ്പ്"],
    "species": ["fish", "mackerel", "sardine", "tuna", "prawn", "catch", "species",
                "season", "மீன்", "மத்தி", "மீന்", "अयल", "ചൂര", "മത്തി"],
    "pfz": ["zone", "pfz", "incois", "chlorophyll", "fishing zone", "best zone",
            "potential", "பகுதி", "மண்டல", "സോൺ", "മേഖല"],
    "weather": ["weather", "wind", "wave", "rain", "forecast", "storm",
                "வானிலை", "காற்று", "കാലാവസ്ഥ", "കാറ്റ്"],
    "navigation": ["navigate", "course", "bearing", "gps", "harbor", "port", "anchor",
                   "திசை", "துறைமுகம்", "ദിക്ക്", "തുറമുഖ"],
    "regulations": ["license", "permit", "banned", "legal", "mesh", "EEZ", "IMBL",
                    " உரிமம்", "தடை", "ലൈസൻസ്", "നിരോധ"],
    "gear": ["net", "longline", "trawl", "FAD", "hook", "gear",
             "வலை", "இழுவை", "വല", "ട്രോൾ"],
    "tides": ["tide", "high tide", "low tide", "tidal", "current",
              "அலை", "நீரோட്ടம", "വേലിയേറ്റ"],
    "ocean": ["ocean", "sea", "temperature", "salinity", "upwelling",
              "கடல்", "வெப്பநிலை", "കടൽ", "ഊഷ്മ"],
    "harbor": ["harbor", "port", "neendakara", "kollam", "kasimedu",
               "துறைமுகம்", "கொல்லம்", "തുറമുഖ", "കൊല്ലം"],
    "general": [],  # matches everything at low weight
}


def _infer_category(query: str) -> Optional[str]:
    """Return the most likely knowledge-base category for a query string."""
    q = query.lower()
    best_cat, best_count = "general", 0
    for cat, kws in _CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in kws if kw in q)
        if count > best_count:
            best_count = count
            best_cat = cat
    return best_cat


def _tag_overlap(query_tokens: List[str], tags: List[str]) -> float:
    """Fraction of query tokens that appear in the candidate's tags."""
    if not tags or not query_tokens:
        return 0.0
    tag_text = " ".join(tags).lower()
    matches = sum(1 for t in query_tokens if t in tag_text)
    return matches / len(query_tokens)


def _build_features(
    query: str,
    candidates: List[Dict[str, Any]],
) -> np.ndarray:
    """Build feature matrix (N, 5) for XGBoost inference."""
    query_cat = _infer_category(query)
    query_tokens = [t for t in query.lower().split() if len(t) > 2]
    q_len = min(len(query_tokens) / 20.0, 1.0)

    rows = []
    for c in candidates:
        cosine = float(c.get("score", 0.0))
        cat_match = 1.0 if c.get("category") == query_cat else 0.0
        t_overlap = _tag_overlap(query_tokens, c.get("tags", []))
        text_len = min(len(c.get("text", "").split()) / 80.0, 1.0)
        rows.append([cosine, cat_match, t_overlap, text_len, q_len])

    return np.array(rows, dtype=np.float32) if rows else np.zeros((0, 5), dtype=np.float32)


def _generate_synthetic_training_data(
    knowledge_docs: List[Dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Create a small synthetic (X, y) dataset for XGBoost.
    Positive pairs: query from a doc → that doc is highly relevant.
    Negative pairs: query from another category → this doc is less relevant.
    Returns X (M, 5) and y (M,) float32.
    """
    X_rows, y_rows = [], []

    for i, doc in enumerate(knowledge_docs):
        cat = doc.get("category", "general")
        tags = doc.get("tags", [])
        text = doc.get("text", "")
        query = " ".join(tags[:3]) if tags else text[:60]
        query_cat = cat

        for j, cand in enumerate(knowledge_docs):
            cosine = 1.0 if i == j else (0.6 if cand.get("category") == cat else 0.2)
            cat_match = 1.0 if cand.get("category") == query_cat else 0.0
            q_tokens = query.lower().split()
            t_overlap = _tag_overlap(q_tokens, cand.get("tags", []))
            text_len = min(len(cand.get("text", "").split()) / 80.0, 1.0)
            q_len = min(len(q_tokens) / 20.0, 1.0)

            label = 1.0 if i == j else (0.6 if cand.get("category") == cat else 0.0)

            X_rows.append([cosine, cat_match, t_overlap, text_len, q_len])
            y_rows.append(label)

            # Limit size: sample only first 15 docs to keep training fast
            if j >= 14:
                break

        if i >= 14:
            break

    return (
        np.array(X_rows, dtype=np.float32),
        np.array(y_rows, dtype=np.float32),
    )


# ── Train ─────────────────────────────────────────────────────────────────────

def train(knowledge_docs: List[Dict[str, Any]]) -> None:
    """Train XGBoost re-ranker on synthetic relevance data and save the model."""
    global _booster

    try:
        import xgboost as xgb  # type: ignore

        X, y = _generate_synthetic_training_data(knowledge_docs)
        if X.shape[0] == 0:
            logger.warning("No training data generated — skipping XGBoost training.")
            return

        dtrain = xgb.DMatrix(X, label=y)
        params = {
            "max_depth": 3,
            "eta": 0.2,
            "objective": "reg:squarederror",
            "eval_metric": "rmse",
            "nthread": 2,
            "seed": 42,
        }
        _booster = xgb.train(params, dtrain, num_boost_round=50, verbose_eval=False)

        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        _booster.save_model(str(_MODEL_FILE))
        logger.info(f"XGBoost re-ranker trained and saved to {_MODEL_FILE}")

    except ImportError:
        logger.warning("xgboost not installed — re-ranker will use cosine-only scoring.")
    except Exception as exc:
        logger.warning(f"XGBoost training failed: {exc}. Falling back to cosine ordering.")


def load() -> bool:
    """Load a persisted XGBoost model. Returns True on success."""
    global _booster
    if not _MODEL_FILE.exists():
        return False
    try:
        import xgboost as xgb  # type: ignore

        _booster = xgb.Booster()
        _booster.load_model(str(_MODEL_FILE))
        logger.info(f"XGBoost re-ranker loaded from {_MODEL_FILE}")
        return True
    except Exception as exc:
        logger.warning(f"Failed to load XGBoost model: {exc}")
        _booster = None
        return False


# ── Rerank ────────────────────────────────────────────────────────────────────

def rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Re-rank FAISS candidates using XGBoost scores (or cosine fallback).

    Args:
        query:      raw query string
        candidates: list of hit dicts from vector_store.search()
        top_k:      how many to return

    Returns:
        Sorted list of up to top_k candidates, each with an added 'rerank_score'.
    """
    if not candidates:
        return []

    if _booster is not None:
        try:
            import xgboost as xgb  # type: ignore

            X = _build_features(query, candidates)
            dmat = xgb.DMatrix(X)
            preds = _booster.predict(dmat)
            for cand, score in zip(candidates, preds):
                cand["rerank_score"] = float(score)
            ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
        except Exception as exc:
            logger.warning(f"XGBoost predict failed ({exc}) — using cosine ordering.")
            for c in candidates:
                c["rerank_score"] = c.get("score", 0.0)
            ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    else:
        # Cosine-only fallback — still assign rerank_score
        for c in candidates:
            c["rerank_score"] = c.get("score", 0.0)
        ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)

    return ranked[:top_k]
