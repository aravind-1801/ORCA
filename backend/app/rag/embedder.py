"""
ORCA RAG Embedder — BGE-M3 multilingual embeddings with TF-IDF fallback.
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger("orca.rag.embedder")

# ── Module-level singletons ───────────────────────────────────────────────────
_bge_model = None  # FlagEmbedding BGEM3FlagModel
_tfidf = None      # sklearn TfidfVectorizer (fallback)
_tfidf_matrix = None
_tfidf_corpus: List[str] = []
_USE_TFIDF = False  # set to True if FlagEmbedding unavailable

# Simple pure-python vocab fallback if sklearn not present
_vocab: Dict[str, int] = {}
_idf: Dict[str, float] = {}


def _try_load_bge() -> bool:
    """Attempt to import and load BGE-M3. Returns True on success."""
    global _bge_model, _USE_TFIDF
    try:
        from FlagEmbedding import BGEM3FlagModel  # type: ignore

        logger.info("Loading BAAI/bge-m3 … (first run downloads ~2.2 GB)")
        _bge_model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
        logger.info("BGE-M3 loaded successfully.")
        _USE_TFIDF = False
        return True
    except Exception as exc:
        logger.warning(
            f"FlagEmbedding / BGE-M3 not available ({exc}). "
            "Switching to TF-IDF fallback embedder."
        )
        _USE_TFIDF = True
        return False


def _ensure_bge_loaded() -> None:
    global _bge_model
    if _bge_model is None and not _USE_TFIDF:
        _try_load_bge()


# ── Pure Python Tokenizer & TF-IDF Helper ────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """Tokenize multilingual text (Latin, Tamil, Malayalam, digits)."""
    # Keeps words of length >= 2 in any unicode script
    return [w.lower() for w in re.findall(r"[\w]+", text, flags=re.UNICODE) if len(w) >= 2]


def _build_pure_tfidf(texts: List[str]) -> None:
    """Pure Python/NumPy TF-IDF builder without sklearn dependency."""
    global _vocab, _idf
    doc_tokens = [_tokenize(t) for t in texts]
    num_docs = len(texts)
    doc_freq: Dict[str, int] = {}

    for tokens in doc_tokens:
        seen = set(tokens)
        for tok in seen:
            doc_freq[tok] = doc_freq.get(tok, 0) + 1

    # Keep top 3000 terms
    sorted_terms = sorted(doc_freq.items(), key=lambda x: x[1], reverse=True)[:3000]
    _vocab = {term: idx for idx, (term, _) in enumerate(sorted_terms)}
    _idf = {
        term: math.log((num_docs + 1.0) / (df + 1.0)) + 1.0
        for term, df in sorted_terms
    }
    logger.info(f"Pure NumPy TF-IDF fallback built on {num_docs} docs, vocab={len(_vocab)}")


def _pure_tfidf_embed(texts: List[str]) -> np.ndarray:
    """Pure NumPy TF-IDF embedding vector generator."""
    dim = max(len(_vocab), 64)
    rows = []
    for text in texts:
        tokens = _tokenize(text)
        vec = np.zeros(dim, dtype=np.float32)
        tf: Dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        for t, count in tf.items():
            if t in _vocab:
                idx = _vocab[t]
                # Sublinear term frequency (1 + log(tf)) * idf
                sublinear_tf = 1.0 + math.log(count)
                vec[idx] = sublinear_tf * _idf.get(t, 1.0)

        # L2-normalize vector
        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec /= norm
        rows.append(vec)

    return np.vstack(rows) if rows else np.zeros((0, dim), dtype=np.float32)


# ── TF-IDF fallback helpers ───────────────────────────────────────────────────

def _build_tfidf(texts: List[str]) -> None:
    """Train TF-IDF vectorizer on the given corpus."""
    global _tfidf, _tfidf_matrix, _tfidf_corpus
    _tfidf_corpus = texts
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
        from sklearn.preprocessing import normalize  # type: ignore

        _tfidf = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=4096,
            strip_accents="unicode",
            sublinear_tf=True,
        )
        raw = _tfidf.fit_transform(texts)
        _tfidf_matrix = normalize(raw, norm="l2").toarray().astype(np.float32)
        logger.info(f"TF-IDF fallback built on {len(texts)} docs, vocab={len(_tfidf.vocabulary_)}")
    except Exception as e:
        logger.info(f"Using pure-python TF-IDF vectorizer: {e}")
        _build_pure_tfidf(texts)


def _tfidf_embed(texts: List[str]) -> np.ndarray:
    """Embed texts using sklearn or pure-python TF-IDF."""
    try:
        from sklearn.preprocessing import normalize  # type: ignore

        if _tfidf is not None:
            raw = _tfidf.transform(texts)
            return normalize(raw, norm="l2").toarray().astype(np.float32)
    except Exception:
        pass

    # Pure python/numpy fallback
    if _vocab:
        return _pure_tfidf_embed(texts)

    # Last resort deterministic unit vectors
    dim = 128
    out = []
    for t in texts:
        seed = int(hashlib.md5(t.encode()).hexdigest(), 16) % (2 ** 32)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(dim).astype(np.float32)
        v /= np.linalg.norm(v) + 1e-9
        out.append(v)
    return np.vstack(out)


# ── Public API ────────────────────────────────────────────────────────────────

def init_embedder(corpus_texts: List[str] | None = None) -> None:
    """
    Initialise the embedder.
    Call once at startup; pass corpus_texts so TF-IDF fallback can be trained.
    """
    loaded = _try_load_bge()
    if not loaded and corpus_texts:
        _build_tfidf(corpus_texts)


def embed(texts: List[str]) -> np.ndarray:
    """
    Embed a list of texts.
    Returns float32 array of shape (N, D), L2-normalised.
    """
    if not texts:
        return np.zeros((0, 256), dtype=np.float32)

    _ensure_bge_loaded()

    if not _USE_TFIDF and _bge_model is not None:
        try:
            output = _bge_model.encode(
                texts,
                batch_size=12,
                max_length=512,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
            vecs = np.array(output["dense_vecs"], dtype=np.float32)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            return vecs / (norms + 1e-9)
        except Exception as exc:
            logger.warning(f"BGE-M3 embed failed ({exc}), using TF-IDF.")
            if _tfidf is None and not _vocab and _tfidf_corpus:
                _build_tfidf(_tfidf_corpus)
            return _tfidf_embed(texts)

    # TF-IDF path
    return _tfidf_embed(texts)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string, returns shape (1, D)."""
    return embed([query])


def embedding_dim() -> int:
    """Return the embedding dimension currently in use."""
    if not _USE_TFIDF and _bge_model is not None:
        return 1024  # BGE-M3 dense dim
    if _tfidf_matrix is not None:
        return _tfidf_matrix.shape[1]
    if _vocab:
        return len(_vocab)
    return 256
