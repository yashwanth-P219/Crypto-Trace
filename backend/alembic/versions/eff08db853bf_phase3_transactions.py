"""phase3_transactions

Revision ID: eff08db853bf
Revises: 
Create Date: 2026-09-06 12:25:07.643553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eff08db853bf'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to Phase 3 transactions and case_transactions."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # If transactions exists with old schema, migrate data cleanly
    if "transactions" in tables:
        cols = [c["name"] for c in insp.get_columns("transactions")]
        if "tx_hash" not in cols:
            # Recreate with Phase 3 schema and migrate existing data
            op.rename_table("transactions", "transactions_old_p2")
            
            op.create_table(
                "transactions",
                sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
                sa.Column("tx_hash", sa.String(length=128), nullable=False),
                sa.Column("blockchain", sa.String(length=32), server_default="Ethereum", nullable=False),
                sa.Column("chain_id", sa.Integer(), server_default="11155111", nullable=False),
                sa.Column("block_number", sa.Integer(), nullable=True),
                sa.Column("block_hash", sa.String(length=128), nullable=True),
                sa.Column("transaction_index", sa.Integer(), nullable=True),
                sa.Column("from_address", sa.String(length=128), nullable=False),
                sa.Column("to_address", sa.String(length=128), nullable=True),
                sa.Column("value_wei", sa.String(length=78), server_default="0", nullable=False),
                sa.Column("value_eth", sa.Float(), server_default="0.0", nullable=False),
                sa.Column("gas", sa.BigInteger(), server_default="21000", nullable=True),
                sa.Column("gas_price_wei", sa.String(length=78), nullable=True),
                sa.Column("nonce", sa.Integer(), nullable=True),
                sa.Column("receipt_status", sa.String(length=32), server_default="SUCCESS", nullable=True),
                sa.Column("gas_used", sa.BigInteger(), nullable=True),
                sa.Column("block_timestamp", sa.DateTime(), nullable=True),
                sa.Column("transaction_type", sa.String(length=32), server_default="native_transfer", nullable=True),
                sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id"), nullable=True),
                sa.Column("gas_fee", sa.Float(), nullable=True),
                sa.Column("amount_usd_if_available", sa.Float(), nullable=True),
                sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
                sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
                sa.PrimaryKeyConstraint("id"),
                sa.UniqueConstraint("tx_hash", "blockchain", "chain_id", name="uq_tx_chain")
            )
            # Copy over existing transactions
            bind.execute(sa.text("""
                INSERT INTO transactions (
                    tx_hash, blockchain, chain_id, block_number, from_address, to_address,
                    value_wei, value_eth, gas_used, gas_fee, receipt_status,
                    block_timestamp, transaction_type, case_id, amount_usd_if_available
                )
                SELECT 
                    transaction_hash, blockchain, 11155111, block_number, from_address, to_address,
                    CAST(CAST(amount_native * 1000000000000000000 AS BIGINT) AS TEXT),
                    amount_native, gas_used, gas_fee, status,
                    timestamp, 'native_transfer', case_id, amount_usd_if_available
                FROM transactions_old_p2;
            """))
            op.drop_table("transactions_old_p2")
    else:
        op.create_table(
            "transactions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("tx_hash", sa.String(length=128), nullable=False),
            sa.Column("blockchain", sa.String(length=32), server_default="Ethereum", nullable=False),
            sa.Column("chain_id", sa.Integer(), server_default="11155111", nullable=False),
            sa.Column("block_number", sa.Integer(), nullable=True),
            sa.Column("block_hash", sa.String(length=128), nullable=True),
            sa.Column("transaction_index", sa.Integer(), nullable=True),
            sa.Column("from_address", sa.String(length=128), nullable=False),
            sa.Column("to_address", sa.String(length=128), nullable=True),
            sa.Column("value_wei", sa.String(length=78), server_default="0", nullable=False),
            sa.Column("value_eth", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("gas", sa.BigInteger(), server_default="21000", nullable=True),
            sa.Column("gas_price_wei", sa.String(length=78), nullable=True),
            sa.Column("nonce", sa.Integer(), nullable=True),
            sa.Column("receipt_status", sa.String(length=32), server_default="SUCCESS", nullable=True),
            sa.Column("gas_used", sa.BigInteger(), nullable=True),
            sa.Column("block_timestamp", sa.DateTime(), nullable=True),
            sa.Column("transaction_type", sa.String(length=32), server_default="native_transfer", nullable=True),
            sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id"), nullable=True),
            sa.Column("gas_fee", sa.Float(), nullable=True),
            sa.Column("amount_usd_if_available", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tx_hash", "blockchain", "chain_id", name="uq_tx_chain")
        )

    # Ensure case_transactions exists
    if "case_transactions" not in tables:
        op.create_table(
            "case_transactions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False),
            sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("case_id", "transaction_id", name="uq_case_tx")
        )

    # Create Indexes
    op.create_index("idx_tx_hash_lookup", "transactions", ["tx_hash"], if_not_exists=True)
    op.create_index("idx_from_address_lookup", "transactions", ["from_address"], if_not_exists=True)
    op.create_index("idx_to_address_lookup", "transactions", ["to_address"], if_not_exists=True)
    op.create_index("idx_block_number_lookup", "transactions", ["block_number"], if_not_exists=True)
    op.create_index("idx_blockchain_chain_lookup", "transactions", ["blockchain", "chain_id"], if_not_exists=True)
    op.create_index("idx_block_timestamp_lookup", "transactions", ["block_timestamp"], if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_block_timestamp_lookup", table_name="transactions", if_exists=True)
    op.drop_index("idx_blockchain_chain_lookup", table_name="transactions", if_exists=True)
    op.drop_index("idx_block_number_lookup", table_name="transactions", if_exists=True)
    op.drop_index("idx_to_address_lookup", table_name="transactions", if_exists=True)
    op.drop_index("idx_from_address_lookup", table_name="transactions", if_exists=True)
    op.drop_index("idx_tx_hash_lookup", table_name="transactions", if_exists=True)
    op.drop_table("case_transactions", if_exists=True)
