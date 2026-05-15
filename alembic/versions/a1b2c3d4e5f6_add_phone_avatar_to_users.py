"""add phone_number and avatar_url to users

Revision ID: a1b2c3d4e5f6
Revises: 22962e293a83
Create Date: 2026-03-03 00:00:00.000000

INSTRUCTIONS:
  1. Find your latest revision id: run `alembic history` in your terminal
  2. Replace <replace_with_your_latest_revision_id> with that value
  3. Save this file to: alembic/versions/a1b2c3d4e5f6_add_phone_avatar_to_users.py
  4. Run: alembic upgrade head
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "22962e293a83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "phone_number")