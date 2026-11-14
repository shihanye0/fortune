"""add users.birth_longitude for true solar time

Revision ID: f7b8c9d0e1a2
Revises: e5a1c2d3b4f5
Create Date: 2026-11-15
"""
from alembic import op
import sqlalchemy as sa

revision = "f7b8c9d0e1a2"
down_revision = "e5a1c2d3b4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
        cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
        if "birth_longitude" not in cols:
            op.add_column("users", sa.Column("birth_longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    if "birth_longitude" in cols:
        op.drop_column("users", "birth_longitude")
