"""phase567_intelligence

Revision ID: a1b2c3d4e5f6
Revises: eff08db853bf
Create Date: 2026-09-06 15:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'eff08db853bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # 1. Upgrade address_labels if needed
    if "address_labels" in tables:
        cols = [c["name"] for c in insp.get_columns("address_labels")]
        if "chain_id" not in cols:
            op.add_column("address_labels", sa.Column("chain_id", sa.Integer(), server_default="11155111", nullable=False))
        if "label" not in cols:
            op.add_column("address_labels", sa.Column("label", sa.String(length=256), nullable=True))
        if "source_url" not in cols:
            op.add_column("address_labels", sa.Column("source_url", sa.String(length=512), nullable=True))
        if "verified" not in cols:
            op.add_column("address_labels", sa.Column("verified", sa.Boolean(), server_default="false", nullable=False))
        if "last_verified_at" not in cols:
            op.add_column("address_labels", sa.Column("last_verified_at", sa.DateTime(), server_default=sa.func.now(), nullable=True))
        if "created_at" not in cols:
            op.add_column("address_labels", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True))
        if "updated_at" not in cols:
            op.add_column("address_labels", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True))
        
        # Add index
        op.create_index("idx_address_label_full", "address_labels", ["address", "blockchain", "chain_id"], if_not_exists=True)
    else:
        op.create_table(
            "address_labels",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("address", sa.String(length=128), nullable=False),
            sa.Column("blockchain", sa.String(length=32), server_default="Ethereum", nullable=False),
            sa.Column("chain_id", sa.Integer(), server_default="11155111", nullable=False),
            sa.Column("entity_name", sa.String(length=128), nullable=False),
            sa.Column("entity_type", sa.String(length=32), server_default="UNKNOWN", nullable=False),
            sa.Column("label", sa.String(length=256), nullable=True),
            sa.Column("source", sa.String(length=128), server_default="Forensic Database", nullable=True),
            sa.Column("source_url", sa.String(length=512), nullable=True),
            sa.Column("confidence", sa.String(length=16), server_default="HIGH", nullable=False),
            sa.Column("verified", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("last_verified", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("last_verified_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("address", "blockchain", "chain_id", name="uq_address_blockchain_chain")
        )
        op.create_index("idx_address_label_lookup", "address_labels", ["address", "blockchain"], if_not_exists=True)
        op.create_index("idx_address_label_full", "address_labels", ["address", "blockchain", "chain_id"], if_not_exists=True)

    # 2. Create analysis_patterns table
    if "analysis_patterns" not in tables:
        op.create_table(
            "analysis_patterns",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id"), nullable=True),
            sa.Column("wallet_address", sa.String(length=128), nullable=False),
            sa.Column("blockchain", sa.String(length=32), server_default="Ethereum", nullable=False),
            sa.Column("chain_id", sa.Integer(), server_default="11155111", nullable=False),
            sa.Column("pattern_id", sa.String(length=64), nullable=False),
            sa.Column("pattern_name", sa.String(length=128), nullable=False),
            sa.Column("severity", sa.String(length=16), server_default="MEDIUM", nullable=False),
            sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("related_wallets", sa.JSON(), nullable=True),
            sa.Column("related_transaction_hashes", sa.JSON(), nullable=True),
            sa.Column("evidence_json", sa.JSON(), nullable=True),
            sa.Column("detected_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index("idx_analysis_pattern_wallet", "analysis_patterns", ["wallet_address"], if_not_exists=True)
        op.create_index("idx_analysis_pattern_case", "analysis_patterns", ["case_id"], if_not_exists=True)
        op.create_index("idx_analysis_pattern_name", "analysis_patterns", ["pattern_name"], if_not_exists=True)
        op.create_index("idx_analysis_pattern_severity", "analysis_patterns", ["severity"], if_not_exists=True)

    # 3. Create risk_assessments table
    if "risk_assessments" not in tables:
        op.create_table(
            "risk_assessments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id"), nullable=True),
            sa.Column("wallet_address", sa.String(length=128), nullable=False),
            sa.Column("blockchain", sa.String(length=32), server_default="Ethereum", nullable=False),
            sa.Column("chain_id", sa.Integer(), server_default="11155111", nullable=False),
            sa.Column("risk_score", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("risk_category", sa.String(length=16), server_default="LOW", nullable=False),
            sa.Column("rule_based_score", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("ml_score", sa.Float(), nullable=True),
            sa.Column("model_name", sa.String(length=128), nullable=True),
            sa.Column("model_version", sa.String(length=32), nullable=True),
            sa.Column("contributions_json", sa.JSON(), nullable=False),
            sa.Column("features_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index("idx_risk_assessment_wallet", "risk_assessments", ["wallet_address"], if_not_exists=True)
        op.create_index("idx_risk_assessment_case", "risk_assessments", ["case_id"], if_not_exists=True)
        op.create_index("idx_risk_assessment_score", "risk_assessments", ["risk_score"], if_not_exists=True)


def downgrade() -> None:
    op.drop_table("risk_assessments", if_exists=True)
    op.drop_table("analysis_patterns", if_exists=True)
