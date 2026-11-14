"""add calculation_version to daily_fortunes

Revision ID: e5a1c2d3b4f5
Revises: c842f79d1aa4
Create Date: 2026-11-15
"""
from alembic import op
import sqlalchemy as sa


revision = "e5a1c2d3b4f5"
down_revision = "c842f79d1aa4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 幂等：repair_initial_schema 用 Base.metadata.create_all 建表（含新列）时不重复加列
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("daily_fortunes")}
    if "calculation_version" not in cols:
        op.add_column("daily_fortunes", sa.Column("calculation_version", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("daily_fortunes", "calculation_version")
