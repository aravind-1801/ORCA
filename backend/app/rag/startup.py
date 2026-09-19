"""
ORCA RAG Startup Initializer.
Loads or builds FAISS index and trains/loads XGBoost reranker.
Called from FastAPI lifespan on startup.
"""
from __future__ import annotations

import logging
from backend.app.rag.knowledge_base import KNOWLEDGE_BASE
from backend.app.rag import embedder, vector_store, reranker

logger = logging.getLogger("orca.rag.startup")


def init_rag() -> None:
    """
    Initialise the RAG subsystem synchronously at startup:
    1. Initialize embedder (BGE-M3 or TF-IDF on knowledge base)
    2. Load or build FAISS vector store
    3. Load or train XGBoost reranker
    """
    logger.info("Initializing ORCA RAG subsystem...")

    # 1. Init embedder with knowledge corpus
    corpus_texts = [doc.get("text", "") for doc in KNOWLEDGE_BASE]
    embedder.init_embedder(corpus_texts)

    # 2. Vector Store: try loading; if not present or rebuild needed, build it
    if not vector_store.load():
        logger.info(f"Embedding {len(KNOWLEDGE_BASE)} documents for FAISS index...")
        embeddings = embedder.embed(corpus_texts)
        vector_store.build(KNOWLEDGE_BASE, embeddings)

    # 3. XGBoost Reranker: try loading; if not present, train on synthetic data
    if not reranker.load():
        logger.info("Training XGBoost reranker on knowledge base patterns...")
        reranker.train(KNOWLEDGE_BASE)

    logger.info("ORCA RAG subsystem initialized successfully.")
