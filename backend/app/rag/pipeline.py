"""
ORCA RAG Pipeline — top-level orchestrator for retrieval-augmented generation.

Flow:
    query (str, lang)
        → embedder.embed_query(query)
        → vector_store.search(top_k=10)
        → reranker.rerank(top_k=5)
        → format_context(hits, lang)  →  str (RAG context)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from backend.app.rag import embedder, vector_store, reranker

logger = logging.getLogger("orca.rag.pipeline")

_MAX_CONTEXT_CHARS = 1800   # approximate token budget for the Gemini prompt


def _select_text(doc: Dict[str, Any], lang: str) -> str:
    """Pick the right language field from a document."""
    norm = (lang or "en").lower()
    if norm.startswith("ta") or "tamil" in norm:
        return doc.get("text_ta") or doc.get("text", "")
    if norm.startswith("ml") or "malayalam" in norm:
        return doc.get("text_ml") or doc.get("text", "")
    return doc.get("text", "")


def format_context(hits: List[Dict[str, Any]], lang: str) -> str:
    """
    Convert re-ranked hits into a concise context string suitable for
    injection into a Gemini prompt.  Truncates to _MAX_CONTEXT_CHARS.
    """
    if not hits:
        return ""

    lines = []
    total = 0
    for i, hit in enumerate(hits, 1):
        cat = hit.get("category", "general").upper()
        text = _select_text(hit, lang).strip()
        snippet = f"[{i}] [{cat}] {text}"
        if total + len(snippet) > _MAX_CONTEXT_CHARS:
            break
        lines.append(snippet)
        total += len(snippet) + 1

    return "\n".join(lines)


class RagPipeline:
    """
    Singleton RAG pipeline.
    All methods are safe to call from async FastAPI handlers.
    """

    async def query(
        self,
        query_text: str,
        lang: str = "en",
        top_k_retrieve: int = 10,
        top_k_rerank: int = 5,
    ) -> str:
        """
        Full RAG query:  text → embed → retrieve → rerank → context string.
        Runs embedding in a thread-pool executor to avoid blocking the event loop.
        """
        if not vector_store.is_ready():
            logger.warning("RAG vector store not ready — returning empty context.")
            return ""

        loop = asyncio.get_event_loop()

        # 1. Embed query (can be slow for BGE-M3, run in executor)
        query_vec = await loop.run_in_executor(
            None, embedder.embed_query, query_text
        )

        # 2. Vector retrieval (FAISS is in-process, fast)
        hits = vector_store.search(query_vec, top_k=top_k_retrieve)

        # 3. XGBoost re-ranking
        ranked = reranker.rerank(query_text, hits, top_k=top_k_rerank)

        # 4. Format into context string in the right language
        context = format_context(ranked, lang)

        logger.debug(
            f"RAG: '{query_text[:60]}' → {len(hits)} retrieved, "
            f"{len(ranked)} re-ranked, context_len={len(context)}"
        )
        return context

    def search_raw(
        self,
        query_text: str,
        lang: str = "en",
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Synchronous search returning raw hit dicts (for the /api/rag/search endpoint).
        """
        if not vector_store.is_ready():
            return []

        query_vec = embedder.embed_query(query_text)
        hits = vector_store.search(query_vec, top_k=top_k * 2)
        ranked = reranker.rerank(query_text, hits, top_k=top_k)
        return ranked

    def status(self) -> Dict[str, Any]:
        """Return current RAG subsystem status."""
        return {
            "enabled": True,
            "index_size": vector_store.index_size(),
            "model_ready": vector_store.is_ready(),
            "embedding_backend": "bge-m3" if not embedder._USE_TFIDF else "tfidf-fallback",
            "reranker_ready": reranker._booster is not None,
            "top_k": 5,
        }


rag_pipeline = RagPipeline()
