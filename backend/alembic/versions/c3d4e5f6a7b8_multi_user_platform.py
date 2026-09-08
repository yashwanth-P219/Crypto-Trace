"""multi_user_platform

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-06 22:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # Columns
    user_cols = [c['name'] for c in insp.get_columns('users')]
    if 'phone_number' not in user_cols:
        op.add_column('users', sa.Column('phone_number', sa.String(32), nullable=True))

    case_cols = [c['name'] for c in insp.get_columns('cases')]
    if 'case_number' not in case_cols:
        op.add_column('cases', sa.Column('case_number', sa.String(64), unique=True, nullable=True))
    if 'victim_id' not in case_cols:
        op.add_column('cases', sa.Column('victim_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))

    # Tables
    if "investigator_profiles" not in tables:
        op.create_table(
            "investigator_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
            sa.Column("organization", sa.String(128), nullable=True),
            sa.Column("department", sa.String(128), nullable=True),
            sa.Column("experience_years", sa.Integer(), server_default="0", nullable=False),
            sa.Column("specialization", sa.String(256), nullable=True),
            sa.Column("badge_id", sa.String(64), nullable=True),
            sa.Column("approval_status", sa.String(32), server_default="PENDING", nullable=False),
            sa.Column("availability_status", sa.String(32), server_default="OFFLINE", nullable=False),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("approved_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.current_timestamp()),
        )

    if "case_assignments" not in tables:
        op.create_table(
            "case_assignments",
            sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
            sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False),
            sa.Column("victim_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("investigator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("status", sa.String(32), server_default="PENDING", nullable=False),
            sa.Column("assigned_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("assigned_at", sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.Column("accepted_at", sa.DateTime(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.current_timestamp()),
        )

    if "notifications" not in tables:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=True),
            sa.Column("notification_type", sa.String(64), nullable=False),
            sa.Column("title", sa.String(256), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.Column("read_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    pass
