"""Semantic Search Service — pgvector-powered similarity search across knowledge and agents."""

from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.embeddings import embed_text, embed_texts, VECTOR_DIM
from backend.app.models import Agent, Knowledge

import logging

logger = logging.getLogger("agenthive")


class SemanticSearchService:
    """Service providing pgvector ANN similarity search across knowledge and agent capability embeddings."""

    # ------------------------------------------------------------------
    # Knowledge semantic search
    # ------------------------------------------------------------------

    @classmethod
    async def search_knowledge(
        cls,
        session: AsyncSession,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.25,
        tag_filter: Optional[str] = None,
    ) -> List[dict]:
        """Return knowledge entries ranked by cosine similarity to the query embedding.

        Returns list of dicts with keys: id, summary, content, tags, source_agent_id,
        similarity, created_at.
        """
        query_vec = await embed_text(query)
        vec_literal = _format_vector(query_vec)

        tag_condition = ""
        params: dict = {"threshold": similarity_threshold, "limit_val": limit}
        if tag_filter:
            tag_condition = "AND :tag = ANY(tags)"
            params["tag"] = tag_filter.strip().lower()

        sql = text(
            f"""
            SELECT
                id,
                summary,
                content,
                tags,
                source_agent_id,
                created_at,
                1 - (embedding <=> '{vec_literal}'::vector) AS similarity
            FROM knowledge
            WHERE embedding IS NOT NULL
              {tag_condition}
              AND 1 - (embedding <=> '{vec_literal}'::vector) >= :threshold
            ORDER BY embedding <=> '{vec_literal}'::vector
            LIMIT :limit_val
            """
        )

        result = await session.execute(sql, params)
        rows = result.fetchall()
        return [
            {
                "id": str(row.id),
                "summary": row.summary,
                "content": row.content,
                "tags": row.tags or [],
                "source_agent_id": str(row.source_agent_id) if row.source_agent_id else None,
                "similarity": round(float(row.similarity), 4),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Agent semantic search
    # ------------------------------------------------------------------

    @classmethod
    async def search_agents(
        cls,
        session: AsyncSession,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.20,
        status_filter: Optional[str] = "ACTIVE",
    ) -> List[dict]:
        """Find agents whose capability embeddings are closest to the query.

        Returns list of dicts with keys: id, public_id, name, capabilities,
        reputation_score, similarity.
        """
        query_vec = await embed_text(query)
        vec_literal = _format_vector(query_vec)

        status_condition = ""
        params: dict = {"threshold": similarity_threshold, "limit_val": limit}
        if status_filter:
            status_condition = "AND status = :status"
            params["status"] = status_filter.upper()

        sql = text(
            f"""
            SELECT
                id,
                public_id,
                name,
                capabilities,
                reputation_score,
                status,
                1 - (capability_embedding <=> '{vec_literal}'::vector) AS similarity
            FROM agents
            WHERE capability_embedding IS NOT NULL
              {status_condition}
              AND 1 - (capability_embedding <=> '{vec_literal}'::vector) >= :threshold
            ORDER BY capability_embedding <=> '{vec_literal}'::vector
            LIMIT :limit_val
            """
        )

        result = await session.execute(sql, params)
        rows = result.fetchall()
        return [
            {
                "id": str(row.id),
                "public_id": row.public_id,
                "name": row.name,
                "capabilities": row.capabilities or [],
                "reputation_score": round(float(row.reputation_score), 3),
                "status": row.status,
                "similarity": round(float(row.similarity), 4),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Embedding backfill helpers
    # ------------------------------------------------------------------

    @classmethod
    async def embed_knowledge_entry(
        cls,
        session: AsyncSession,
        entry_id: uuid.UUID,
        text_to_embed: str,
    ) -> None:
        """Generate and persist an embedding for a single knowledge entry."""
        vec = await embed_text(text_to_embed)
        vec_literal = _format_vector(vec)
        await session.execute(
            text(
                f"UPDATE knowledge SET embedding = '{vec_literal}'::vector WHERE id = :id"
            ),
            {"id": entry_id},
        )

    @classmethod
    async def embed_agent_capabilities(
        cls,
        session: AsyncSession,
        agent_id: uuid.UUID,
        capabilities: List[str],
    ) -> None:
        """Generate and persist a capability embedding for an agent."""
        caps_text = " ".join(capabilities) if capabilities else "general purpose agent"
        vec = await embed_text(caps_text)
        vec_literal = _format_vector(vec)
        await session.execute(
            text(
                f"UPDATE agents SET capability_embedding = '{vec_literal}'::vector WHERE id = :id"
            ),
            {"id": agent_id},
        )

    @classmethod
    async def backfill_knowledge_embeddings(cls, session: AsyncSession) -> int:
        """Backfill embeddings for all knowledge entries that are missing one. Returns count updated."""
        result = await session.execute(
            text("SELECT id, summary, content FROM knowledge WHERE embedding IS NULL LIMIT 500")
        )
        rows = result.fetchall()
        if not rows:
            return 0

        texts = [f"{r.summary}. {r.content}" for r in rows]
        vecs = await embed_texts(texts)

        count = 0
        for row, vec in zip(rows, vecs):
            vec_literal = _format_vector(vec)
            await session.execute(
                text(f"UPDATE knowledge SET embedding = '{vec_literal}'::vector WHERE id = :id"),
                {"id": row.id},
            )
            count += 1

        await session.commit()
        return count

    @classmethod
    async def backfill_agent_embeddings(cls, session: AsyncSession) -> int:
        """Backfill capability embeddings for all agents missing one. Returns count updated."""
        result = await session.execute(
            text("SELECT id, capabilities FROM agents WHERE capability_embedding IS NULL LIMIT 500")
        )
        rows = result.fetchall()
        if not rows:
            return 0

        texts = [
            " ".join(r.capabilities) if r.capabilities else "general purpose agent"
            for r in rows
        ]
        vecs = await embed_texts(texts)

        count = 0
        for row, vec in zip(rows, vecs):
            vec_literal = _format_vector(vec)
            await session.execute(
                text(f"UPDATE agents SET capability_embedding = '{vec_literal}'::vector WHERE id = :id"),
                {"id": row.id},
            )
            count += 1

        await session.commit()
        return count


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _format_vector(vec: List[float]) -> str:
    """Format a float list as a pgvector literal string '[0.1, 0.2, ...]'."""
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
