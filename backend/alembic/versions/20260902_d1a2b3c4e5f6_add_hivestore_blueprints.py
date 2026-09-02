"""Alembic migration: Add HiveStore agent blueprints and clone tracking tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d1a2b3c4e5f6"
down_revision = "c9f5a1b2d4e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_blueprints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(length=64), unique=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("tagline", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="general"),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("creator_name", sa.String(length=100), nullable=True),
        sa.Column("repo_url", sa.String(length=255), nullable=True),
        sa.Column("setup_instructions", sa.Text(), nullable=True),
        sa.Column("docker_compose_snippet", sa.Text(), nullable=True),
        sa.Column("env_vars_template", sa.Text(), nullable=True),
        sa.Column("required_models", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("required_tools", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("linked_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clone_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_rating", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("active_instances", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PUBLISHED"),
        sa.Column("featured", sa.String(length=10), nullable=False, server_default="NO"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_blueprint_slug", "agent_blueprints", ["slug"])
    op.create_index("idx_blueprint_category", "agent_blueprints", ["category"])
    op.create_index("idx_blueprint_status", "agent_blueprints", ["status"])
    op.create_index("idx_blueprint_clone_count", "agent_blueprints", ["clone_count"])
    op.create_index("idx_blueprint_avg_rating", "agent_blueprints", ["avg_rating"])
    op.create_index("idx_blueprint_creator_id", "agent_blueprints", ["creator_id"])

    op.create_table(
        "blueprint_clones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("clone_id", sa.String(length=64), unique=True, nullable=False),
        sa.Column("blueprint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_blueprints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cloner_name", sa.String(length=100), nullable=True),
        sa.Column("cloner_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_clone_id", "blueprint_clones", ["clone_id"])
    op.create_index("idx_clone_blueprint_id", "blueprint_clones", ["blueprint_id"])


def downgrade() -> None:
    op.drop_table("blueprint_clones")
    op.drop_table("agent_blueprints")
