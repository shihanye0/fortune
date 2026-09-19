"""add durable per-channel push outbox

Revision ID: c842f79d1aa4
Revises: b31dc536e703
Create Date: 2026-09-18 19:15:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "c842f79d1aa4"
down_revision = "b31dc536e703"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "push_deliveries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", "channel", name="uq_push_delivery_user_date_channel"),
    )
    op.create_index("ix_push_deliveries_user_id", "push_deliveries", ["user_id"])
    op.create_index("ix_push_deliveries_date", "push_deliveries", ["date"])


def downgrade() -> None:
    op.drop_index("ix_push_deliveries_date", table_name="push_deliveries")
    op.drop_index("ix_push_deliveries_user_id", table_name="push_deliveries")
    op.drop_table("push_deliveries")
