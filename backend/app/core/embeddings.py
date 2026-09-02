"""Embedding engine for semantic vector generation using sentence-transformers."""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

logger = logging.getLogger("agenthive")

# Lazy singleton — loaded once on first use to avoid slow import at startup
_model = None
_model_lock = asyncio.Lock()

MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim, 80MB, fast on CPU/ARM64
VECTOR_DIM = 384


async def get_embedding_model():
    """Return the singleton SentenceTransformer model (loaded lazily)."""
    global _model
    if _model is None:
        async with _model_lock:
            if _model is None:
                try:
                    from sentence_transformers import SentenceTransformer  # type: ignore
                    logger.info(f"Loading embedding model '{MODEL_NAME}'...")
                    _model = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: SentenceTransformer(MODEL_NAME)
                    )
                    logger.info(f"Embedding model loaded. dim={VECTOR_DIM}")
                except Exception as e:
                    logger.warning(f"Embedding model load failed ({e}). Falling back to zero-vector.")
                    _model = None
    return _model


async def embed_text(text: str) -> List[float]:
    """Embed a single text string into a float vector of length VECTOR_DIM."""
    model = await get_embedding_model()
    if model is None:
        return [0.0] * VECTOR_DIM
    loop = asyncio.get_event_loop()
    vec = await loop.run_in_executor(None, lambda: model.encode(text, normalize_embeddings=True))
    return vec.tolist()


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Batch embed a list of texts."""
    model = await get_embedding_model()
    if model is None:
        return [[0.0] * VECTOR_DIM for _ in texts]
    loop = asyncio.get_event_loop()
    vecs = await loop.run_in_executor(
        None, lambda: model.encode(texts, normalize_embeddings=True, batch_size=32)
    )
    return [v.tolist() for v in vecs]
