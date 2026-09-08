"""phase8_12_platform

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-06 21:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # 1. priority_items
    if "priority_items" not in tables:
        op.create_table(
            "priority_items",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("object_type", sa.String(length=32), nullable=False),
            sa.Column("object_id", sa.String(length=128), nullable=False),
            sa.Column("wallet_address", sa.String(length=128), nullable=True),
            sa.Column("blockchain", sa.String(length=32), server_default="Ethereum", nullable=False),
            sa.Column("chain_id", sa.Integer(), server_default="11155111", nullable=False),
            sa.Column("priority_score", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("priority_category", sa.String(length=16), server_default="LOW", nullable=False),
            sa.Column("risk_score", sa.Float(), nullable=True),
            sa.Column("reasons", sa.JSON(), nullable=False),
            sa.Column("supporting_evidence", sa.JSON(), nullable=False),
            sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id"), nullable=True),
            sa.Column("assigned_to", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=32), server_default="NEW", nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index("idx_priority_wallet", "priority_items", ["wallet_address"], if_not_exists=True)
        op.create_index("idx_priority_score", "priority_items", ["priority_score"], if_not_exists=True)
        op.create_index("idx_priority_case", "priority_items", ["case_id"], if_not_exists=True)

    # 2. investigation_timeline
    if "investigation_timeline" not in tables:
        op.create_table(
            "investigation_timeline",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id"), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("title", sa.String(length=256), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("actor", sa.String(length=64), server_default="SYSTEM", nullable=False),
            sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index("idx_timeline_case", "investigation_timeline", ["case_id"], if_not_exists=True)
        op.create_index("idx_timeline_timestamp", "investigation_timeline", ["timestamp"], if_not_exists=True)

    # 3. alert_rules
    if "alert_rules" not in tables:
        op.create_table(
            "alert_rules",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id"), nullable=True),
            sa.Column("rule_name", sa.String(length=128), nullable=False),
            sa.Column("rule_type", sa.String(length=64), nullable=False),
            sa.Column("threshold_value", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index("idx_alert_rule_case", "alert_rules", ["case_id"], if_not_exists=True)

    # 4. copilot_messages
    if "copilot_messages" not in tables:
        op.create_table(
            "copilot_messages",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("role", sa.String(length=16), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("grounded_evidence", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index("idx_copilot_case", "copilot_messages", ["case_id"], if_not_exists=True)

    # 5. blockchain_networks
    if "blockchain_networks" not in tables:
        op.create_table(
            "blockchain_networks",
            sa.Column("chain_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=64), nullable=False),
            sa.Column("symbol", sa.String(length=16), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("is_evm", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("rpc_url_configured", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("explorer_url", sa.String(length=256), nullable=True),
            sa.PrimaryKeyConstraint("chain_id")
        )

    # 6. cross_chain_links
    if "cross_chain_links" not in tables:
        op.create_table(
            "cross_chain_links",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("source_chain_id", sa.Integer(), nullable=False),
            sa.Column("destination_chain_id", sa.Integer(), nullable=False),
            sa.Column("source_tx_hash", sa.String(length=128), nullable=False),
            sa.Column("bridge_contract", sa.String(length=128), nullable=False),
            sa.Column("bridge_name", sa.String(length=128), nullable=False),
            sa.Column("amount", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index("idx_ccl_tx", "cross_chain_links", ["source_tx_hash"], if_not_exists=True)
        op.create_index("idx_ccl_bridge", "cross_chain_links", ["bridge_contract"], if_not_exists=True)


def downgrade() -> None:
    op.drop_table("cross_chain_links", if_exists=True)
    op.drop_table("blockchain_networks", if_exists=True)
    op.drop_table("copilot_messages", if_exists=True)
    op.drop_table("alert_rules", if_exists=True)
    op.drop_table("investigation_timeline", if_exists=True)
    op.drop_table("priority_items", if_exists=True)
