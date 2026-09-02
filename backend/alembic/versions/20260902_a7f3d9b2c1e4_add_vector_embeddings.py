"""Alembic migration: Enable pgvector extension and add embedding columns to knowledge and agents."""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "a7f3d9b2c1e4"
down_revision = "3244cae4e4ee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column to knowledge (384-dim all-MiniLM-L6-v2)
    op.execute(
        "ALTER TABLE knowledge ADD COLUMN IF NOT EXISTS embedding vector(384)"
    )

    # Add embedding column to agents (capabilities embedding)
    op.execute(
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS capability_embedding vector(384)"
    )

    # Create HNSW indexes for fast ANN search (cosine similarity)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_embedding_hnsw "
        "ON knowledge USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_agents_capability_embedding_hnsw "
        "ON agents USING hnsw (capability_embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_agents_capability_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_knowledge_embedding_hnsw")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS capability_embedding")
    op.execute("ALTER TABLE knowledge DROP COLUMN IF EXISTS embedding")
