"""set_property_status_default_pending_approval

Revision ID: c8f1b2e9a7d0
Revises: 486419238951
Create Date: 2026-05-27 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8f1b2e9a7d0"
down_revision: Union[str, None] = "486419238951"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE properties SET status = 'pending_approval' "
        "WHERE status IS NULL OR TRIM(status) = ''"
    )
    op.alter_column(
        "properties",
        "status",
        existing_type=sa.String(length=50),
        nullable=False,
        server_default=sa.text("'pending_approval'"),
    )


def downgrade() -> None:
    op.alter_column(
        "properties",
        "status",
        existing_type=sa.String(length=50),
        nullable=False,
        server_default=None,
    )
