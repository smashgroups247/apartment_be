"""add_phone_number_and_avatar_url_to_users

Revision ID: a0fa4c74bcd2
Revises: c4faa46d0092
Create Date: 2026-05-08 14:05:28.166229

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0fa4c74bcd2'
down_revision: Union[str, None] = 'c4faa46d0092'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns that exist in the model but not in the remote DB
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'phone_number')
