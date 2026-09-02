"""Unit tests for embedding generator."""

import pytest
from backend.app.core.embeddings import embed_text, embed_texts, VECTOR_DIM


@pytest.mark.asyncio
async def test_embed_text_dimensions():
    """Verify single text embedding produces a normalized vector of length 384."""
    vec = await embed_text("Autonomous AI agent collaboration network")
    assert isinstance(vec, list)
    assert len(vec) == VECTOR_DIM
    assert all(isinstance(x, float) for x in vec)


@pytest.mark.asyncio
async def test_embed_texts_batch():
    """Verify batch embedding produces correct number of vectors."""
    texts = [
        "Zero-trust security memory firewall",
        "Bayesian peer verification consensus",
        "Real-time WebSocket telemetry feed",
    ]
    vecs = await embed_texts(texts)
    assert len(vecs) == 3
    for v in vecs:
        assert len(v) == VECTOR_DIM
