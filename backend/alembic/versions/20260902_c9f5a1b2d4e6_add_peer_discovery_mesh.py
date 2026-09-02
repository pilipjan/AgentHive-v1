"""Alembic migration: Add peer discovery mesh and gossip packet tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "c9f5a1b2d4e6"
down_revision = "b8e4f1a2c3d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create mesh_peer_nodes table
    op.create_table(
        "mesh_peer_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("node_id", sa.String(length=64), unique=True, nullable=False),
        sa.Column("node_name", sa.String(length=100), nullable=False),
        sa.Column("endpoint_url", sa.String(length=255), nullable=False),
        sa.Column("protocol", sa.String(length=20), nullable=False, server_default="HTTPS"),
        sa.Column("discovery_method", sa.String(length=30), nullable=False, server_default="GOSSIP"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ONLINE"),
        sa.Column("capabilities", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("agent_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("latency_ms", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_ping_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_mesh_peer_node_id", "mesh_peer_nodes", ["node_id"])
    op.create_index("idx_mesh_peer_status", "mesh_peer_nodes", ["status"])
    op.create_index("idx_mesh_peer_discovery_method", "mesh_peer_nodes", ["discovery_method"])
    op.create_index("idx_mesh_peer_last_ping", "mesh_peer_nodes", ["last_ping_at"])

    # 2. Create mesh_gossip_packets table
    op.create_table(
        "mesh_gossip_packets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("packet_id", sa.String(length=64), unique=True, nullable=False),
        sa.Column("origin_node_id", sa.String(length=64), nullable=False),
        sa.Column("packet_type", sa.String(length=30), nullable=False),
        sa.Column("nodes_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("signature", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_gossip_packet_id", "mesh_gossip_packets", ["packet_id"])
    op.create_index("idx_gossip_origin_node", "mesh_gossip_packets", ["origin_node_id"])
    op.create_index("idx_gossip_packet_type", "mesh_gossip_packets", ["packet_type"])
    op.create_index("idx_gossip_created_at", "mesh_gossip_packets", ["created_at"])


def downgrade() -> None:
    op.drop_table("mesh_gossip_packets")
    op.drop_table("mesh_peer_nodes")
