"""Integration tests for pgvector Semantic Search APIs."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_semantic_knowledge_and_agent_search_lifecycle(async_client: AsyncClient):
    """Verify semantic knowledge publishing, backfill, and similarity search endpoints."""
    uid = uuid.uuid4().hex[:6]
    slug = f"agt-vector-{uid}"

    # 1. Register specialized agent
    agent_res = await async_client.post("/api/v1/agents", json={
        "name": "VectorSearchSpecialist",
        "public_id": slug,
        "description": "Expert in pgvector, embedding distance metrics, and approximate nearest neighbor indexing.",
        "capabilities": ["pgvector", "embeddings", "hnsw", "similarity_search"],
    })
    assert agent_res.status_code == 201

    # Grant required knowledge permissions
    await async_client.post(f"/api/v1/agents/{slug}/permissions", json={"permission_name": "WRITE_KNOWLEDGE"})
    await async_client.post(f"/api/v1/agents/{slug}/permissions", json={"permission_name": "PUBLISH_PUBLIC_KNOWLEDGE"})

    # 2. Publish Knowledge Entry
    know_res = await async_client.post("/api/v1/knowledge", json={
        "summary": "HNSW index tuning for sub-millisecond vector retrieval",
        "content": "Setting ef_search to 64 and m to 16 provides optimal recall for cosine similarity queries under high concurrency.",
        "source_agent_id": slug,
        "visibility": "PUBLIC",
        "tags": ["pgvector", "hnsw", "database"],
    })
    assert know_res.status_code == 201

    # 3. Test Semantic Knowledge Search
    search_res = await async_client.post("/api/v1/search/knowledge", json={
        "query": "how to tune vector database index for fast nearest neighbor lookup",
        "limit": 5,
        "similarity_threshold": 0.20,
    })
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1
    top_result = search_data["results"][0]
    assert top_result["similarity"] >= 0.20
    assert "summary" in top_result

    # 4. Test Semantic Agent Discovery
    agent_search_res = await async_client.post("/api/v1/search/agents", json={
        "query": "agent specialized in high-performance embedding searches and HNSW",
        "limit": 5,
        "similarity_threshold": 0.15,
    })
    assert agent_search_res.status_code == 200
    agent_search_data = agent_search_res.json()
    assert agent_search_data["total"] >= 1
    assert any(a["public_id"] == slug for a in agent_search_data["results"])

    # 5. Test Backfill Endpoint
    backfill_res = await async_client.post("/api/v1/search/backfill")
    assert backfill_res.status_code == 200
    assert "knowledge_embedded" in backfill_res.json()
    assert "agents_embedded" in backfill_res.json()
