"""
ORCA RAG Pipeline Test Suite.
Tests embedding, FAISS/NumPy vector search, XGBoost/cosine reranker,
and multilingual context generation (EN, TA, ML).
"""
import pytest
import numpy as np

from backend.app.rag.knowledge_base import KNOWLEDGE_BASE
from backend.app.rag import embedder, vector_store, reranker
from backend.app.rag.pipeline import rag_pipeline, format_context


@pytest.fixture(scope="module", autouse=True)
def setup_rag_subsystem():
    """Ensure RAG embedder, vector store, and reranker are initialised."""
    corpus = [doc.get("text", "") for doc in KNOWLEDGE_BASE]
    embedder.init_embedder(corpus)

    # Build vector store
    embeddings = embedder.embed(corpus)
    vector_store.build(KNOWLEDGE_BASE, embeddings)

    # Train or load reranker
    reranker.train(KNOWLEDGE_BASE)


def test_embedder_produces_vector():
    """Verify embedder outputs 2D array with valid L2-normalized float32 vectors."""
    texts = ["Marine safety and storm warning", "High wave advisories"]
    vecs = embedder.embed(texts)
    assert isinstance(vecs, np.ndarray)
    assert vecs.shape[0] == 2
    assert vecs.shape[1] > 0
    # Test L2-norm is approximately 1.0
    for v in vecs:
        norm = np.linalg.norm(v)
        assert abs(norm - 1.0) < 1e-3, f"Vector norm {norm} is not normalized"


def test_vector_store_build_and_search():
    """Verify vector store search returns ranked candidate documents with scores."""
    q_vec = embedder.embed_query("cyclone storm safety life jacket")
    hits = vector_store.search(q_vec, top_k=5)
    assert len(hits) > 0
    assert "text" in hits[0]
    assert "score" in hits[0]
    # Check that safety or weather related chunk is among top results
    categories = [h.get("category") for h in hits]
    assert any(cat in ["safety", "weather"] for cat in categories)


def test_xgboost_reranker_trains_and_reranks():
    """Verify re-ranker assigns rerank_score and returns ordered candidates."""
    query = "Where can I catch sardines and mackerel today?"
    q_vec = embedder.embed_query(query)
    candidates = vector_store.search(q_vec, top_k=6)
    assert len(candidates) > 0

    reranked = reranker.rerank(query, candidates, top_k=3)
    assert len(reranked) <= 3
    for item in reranked:
        assert "rerank_score" in item
    # Scores should be sorted descending
    scores = [item["rerank_score"] for item in reranked]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end_english():
    """Verify end-to-end RAG query in English returns non-empty formatted context."""
    context = await rag_pipeline.query(
        query_text="What are the PFZ chlorophyll ocean indicators?",
        lang="en",
        top_k_retrieve=8,
        top_k_rerank=4,
    )
    assert isinstance(context, str)
    assert len(context) > 0
    assert "[1]" in context


@pytest.mark.asyncio
async def test_rag_pipeline_tamil():
    """Verify RAG query in Tamil returns Tamil context without English pollution."""
    query_ta = "கடலில் காற்று மற்றும் அலை பாதுகாப்பு எச்சரிக்கை"
    context = await rag_pipeline.query(
        query_text=query_ta,
        lang="ta",
        top_k_retrieve=6,
        top_k_rerank=3,
    )
    assert isinstance(context, str)
    assert len(context) > 0
    # Must contain Tamil characters
    has_tamil = any("\u0B80" <= ch <= "\u0BFF" for ch in context)
    assert has_tamil, "Tamil RAG context should contain Tamil script"


@pytest.mark.asyncio
async def test_rag_pipeline_malayalam():
    """Verify RAG query in Malayalam returns Malayalam context."""
    query_ml = "ചൂരയും അയലയും കിട്ടുന്ന മികച്ച മീൻപിടുത്ത മേഖല ഏതാണ്?"
    context = await rag_pipeline.query(
        query_text=query_ml,
        lang="ml",
        top_k_retrieve=6,
        top_k_rerank=3,
    )
    assert isinstance(context, str)
    assert len(context) > 0
    # Must contain Malayalam characters
    has_malayalam = any("\u0D00" <= ch <= "\u0D7F" for ch in context)
    assert has_malayalam, "Malayalam RAG context should contain Malayalam script"


def test_rag_pipeline_status():
    """Verify pipeline status returns healthy configuration."""
    status = rag_pipeline.status()
    assert status["enabled"] is True
    assert status["index_size"] > 0
    assert status["model_ready"] is True


def test_rag_api_search_endpoint():
    """Verify FastAPI /api/rag/search endpoint returns hits and formatted context."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    res = client.post(
        "/api/rag/search",
        json={"query": "cyclone warning signal harbor", "language": "en", "top_k": 3},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    assert len(data["hits"]) <= 3
    assert len(data["context"]) > 0


def test_ai_chat_uses_rag():
    """Verify /api/ai/chat returns rag_used=True and non-zero rag_chunks."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    res = client.post(
        "/api/ai/chat",
        json={
            "query": "Is it safe to fish today? What are the storm precautions?",
            "language": "en",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["rag_used"] is True
    assert data["rag_chunks"] > 0
