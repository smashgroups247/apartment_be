"""merge heads user + properties

Revision ID: e45144a42028
Revises: 3f1b7d923fd8, 99d3d7bac4fc
Create Date: 2026-05-15 10:48:17.118961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e45144a42028'
down_revision: Union[str, None] = ('3f1b7d923fd8', '99d3d7bac4fc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
