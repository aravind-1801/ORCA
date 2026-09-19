"""
ORCA RAG Vector Store — FAISS IndexFlatIP (cosine via L2-normalised vectors)
with built-in NumPy vector store fallback.
Persists index + metadata to disk; reloads on startup.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("orca.rag.vector_store")

# ── Index storage paths ───────────────────────────────────────────────────────
_INDEX_DIR = Path("backend/rag/index")
_INDEX_FILE = _INDEX_DIR / "orca.faiss"
_NPY_FILE = _INDEX_DIR / "orca_vectors.npy"
_META_FILE = _INDEX_DIR / "meta.json"

# ── Module-level state ────────────────────────────────────────────────────────
_index = None                  # faiss.IndexFlatIP if available
_numpy_matrix = None           # np.ndarray (N, D) fallback
_metadata: List[Dict[str, Any]] = []
_dim: int = 0
_USE_NUMPY_STORE = False


def _get_faiss():
    """Lazy import faiss."""
    try:
        import faiss  # type: ignore
        return faiss
    except Exception:
        return None


# ── Build / Save ──────────────────────────────────────────────────────────────

def build(docs: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
    """
    Build vector store from pre-computed embeddings.

    Args:
        docs: list of document dicts (doc_id, category, tags, text, text_ta, text_ml)
        embeddings: float32 array (N, D), L2-normalised
    """
    global _index, _numpy_matrix, _metadata, _dim, _USE_NUMPY_STORE

    n, d = embeddings.shape
    _dim = d
    _numpy_matrix = np.array(embeddings, dtype=np.float32)

    faiss = _get_faiss()
    if faiss is not None:
        try:
            logger.info(f"Building FAISS IndexFlatIP with {n} vectors, dim={d}")
            idx = faiss.IndexFlatIP(d)
            idx.add(embeddings)
            _index = idx
            _USE_NUMPY_STORE = False
        except Exception as exc:
            logger.warning(f"FAISS index build failed ({exc}) - falling back to NumPy matrix store.")
            _index = None
            _USE_NUMPY_STORE = True
    else:
        logger.info(f"Building NumPy vector store with {n} vectors, dim={d}")
        _index = None
        _USE_NUMPY_STORE = True

    _metadata = [
        {
            "doc_id": doc.get("doc_id", f"doc_{i}"),
            "category": doc.get("category", "general"),
            "tags": doc.get("tags", []),
            "text": doc.get("text", ""),
            "text_ta": doc.get("text_ta", ""),
            "text_ml": doc.get("text_ml", ""),
        }
        for i, doc in enumerate(docs)
    ]

    _save()
    logger.info("Vector store built and saved.")


def _save() -> None:
    """Persist index and metadata to disk."""
    global _index, _numpy_matrix, _metadata, _dim

    _INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss = _get_faiss()
    if faiss is not None and _index is not None:
        try:
            faiss.write_index(_index, str(_INDEX_FILE))
        except Exception as e:
            logger.warning(f"Could not write FAISS file: {e}")

    if _numpy_matrix is not None:
        np.save(str(_NPY_FILE), _numpy_matrix)

    meta_payload = {"dim": _dim, "docs": _metadata}
    _META_FILE.write_text(json.dumps(meta_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Saved vector index and meta ({_META_FILE})")


# ── Load ──────────────────────────────────────────────────────────────────────

def load() -> bool:
    """
    Load a persisted vector store from disk.
    Returns True if loaded successfully, False otherwise.
    """
    global _index, _numpy_matrix, _metadata, _dim, _USE_NUMPY_STORE

    if not _META_FILE.exists():
        logger.info("No persisted vector store found — will build on startup.")
        return False

    try:
        payload = json.loads(_META_FILE.read_text(encoding="utf-8"))
        _dim = payload["dim"]
        _metadata = payload["docs"]

        # Try loading FAISS first
        faiss = _get_faiss()
        if faiss is not None and _INDEX_FILE.exists():
            try:
                _index = faiss.read_index(str(_INDEX_FILE))
                _USE_NUMPY_STORE = False
                logger.info(f"Loaded FAISS index: {_index.ntotal} vectors, dim={_dim}")
                return True
            except Exception as e:
                logger.warning(f"Failed to read FAISS index ({e}), trying NumPy npy file.")

        # Fallback to numpy array
        if _NPY_FILE.exists():
            _numpy_matrix = np.load(str(_NPY_FILE))
            _USE_NUMPY_STORE = True
            logger.info(f"Loaded NumPy vector matrix: {_numpy_matrix.shape[0]} vectors, dim={_dim}")
            return True

        return False
    except Exception as exc:
        logger.warning(f"Failed to load persisted vector store: {exc}. Will rebuild.")
        _index = None
        _numpy_matrix = None
        _metadata = []
        _dim = 0
        return False


# ── Search ────────────────────────────────────────────────────────────────────

def search(
    query_vec: np.ndarray,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k nearest neighbours.

    Args:
        query_vec: float32 array (1, D) or (D,), L2-normalised
        top_k: number of results

    Returns:
        list of hit dicts with keys: doc_id, category, tags, text, text_ta, text_ml, score
    """
    vec = np.array(query_vec, dtype=np.float32)
    if vec.ndim == 1:
        vec = vec.reshape(1, -1)

    # 1. FAISS Search
    if not _USE_NUMPY_STORE and _index is not None and _index.ntotal > 0:
        k = min(top_k, _index.ntotal)
        scores, indices = _index.search(vec, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(_metadata):
                continue
            doc = dict(_metadata[idx])
            doc["score"] = float(score)
            results.append(doc)
        return results

    # 2. NumPy Cosine Search (Inner product on L2-normalised vectors)
    if _numpy_matrix is not None and len(_numpy_matrix) > 0:
        # dot product: (1, D) @ (D, N) -> (1, N)
        dots = np.dot(vec, _numpy_matrix.T)[0]
        k = min(top_k, len(_numpy_matrix))
        # Top-k indices in descending order
        top_indices = np.argsort(dots)[::-1][:k]
        results = []
        for idx in top_indices:
            doc = dict(_metadata[idx])
            doc["score"] = float(dots[idx])
            results.append(doc)
        return results

    logger.warning("Vector store not initialised — returning empty results.")
    return []


# ── Utilities ─────────────────────────────────────────────────────────────────

def index_size() -> int:
    """Return number of vectors in the index."""
    if not _USE_NUMPY_STORE and _index is not None:
        return _index.ntotal
    if _numpy_matrix is not None:
        return len(_numpy_matrix)
    return 0


def is_ready() -> bool:
    """Return True if index is initialised and non-empty."""
    return index_size() > 0
