"""Alembic migration: Add HiveStore agent_heartbeats and agent_reviews tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e2b3c4d5f6a7"
down_revision = "d1a2b3c4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_heartbeats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("blueprint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_blueprints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instance_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ONLINE"),
        sa.Column("uptime_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("response_time_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("version", sa.String(length=30), nullable=True, server_default="1.0.0"),
        sa.Column("host_info", sa.String(length=100), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_heartbeat_blueprint_id", "agent_heartbeats", ["blueprint_id"])
    op.create_index("idx_heartbeat_instance_id", "agent_heartbeats", ["instance_id"])
    op.create_index("idx_heartbeat_recorded_at", "agent_heartbeats", ["recorded_at"])

    op.create_table(
        "agent_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("review_id", sa.String(length=64), unique=True, nullable=False),
        sa.Column("blueprint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_blueprints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_name", sa.String(length=100), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=False),
        sa.Column("verified_clone", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("uptime_experienced", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_review_review_id", "agent_reviews", ["review_id"])
    op.create_index("idx_review_blueprint_id", "agent_reviews", ["blueprint_id"])
    op.create_index("idx_review_rating", "agent_reviews", ["rating"])


def downgrade() -> None:
    op.drop_table("agent_reviews")
    op.drop_table("agent_heartbeats")
