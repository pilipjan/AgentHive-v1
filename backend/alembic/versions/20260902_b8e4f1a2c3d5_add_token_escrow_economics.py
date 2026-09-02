"""Alembic migration: Add token escrow economics, agent wallets, and transaction ledgers."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "b8e4f1a2c3d5"
down_revision = "a7f3d9b2c1e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create agent_wallets table
    op.create_table(
        "agent_wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_type", sa.String(length=20), nullable=False, server_default="AGENT"),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True),
        sa.Column("balance", sa.Float(), nullable=False, server_default="1000.0"),
        sa.Column("locked_escrow", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_earned", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_spent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_agent_wallets_agent_id", "agent_wallets", ["agent_id"])
    op.create_index("idx_agent_wallets_user_id", "agent_wallets", ["user_id"])

    # 2. Create escrow_contracts table
    op.create_table(
        "escrow_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contract_id", sa.String(length=64), unique=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("funder_wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_wallets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="HELD"),
        sa.Column("release_tx_id", sa.String(length=64), nullable=True),
        sa.Column("refund_tx_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_escrow_contracts_contract_id", "escrow_contracts", ["contract_id"])
    op.create_index("idx_escrow_contracts_job_id", "escrow_contracts", ["job_id"])
    op.create_index("idx_escrow_contracts_status", "escrow_contracts", ["status"])

    # 3. Create escrow_transactions table
    op.create_table(
        "escrow_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tx_id", sa.String(length=64), unique=True, nullable=False),
        sa.Column("source_wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_wallets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("destination_wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_wallets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("escrow_contracts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tx_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("balance_after", sa.Float(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_escrow_tx_id", "escrow_transactions", ["tx_id"])
    op.create_index("idx_escrow_tx_type", "escrow_transactions", ["tx_type"])
    op.create_index("idx_escrow_tx_created_at", "escrow_transactions", ["created_at"])


def downgrade() -> None:
    op.drop_table("escrow_transactions")
    op.drop_table("escrow_contracts")
    op.drop_table("agent_wallets")
