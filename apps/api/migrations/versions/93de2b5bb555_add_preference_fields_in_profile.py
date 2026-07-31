"""add preference fields in profile

Revision ID: 93de2b5bb555
Revises: 81483707fc18
Create Date: 2026-07-31 15:26:32.843411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93de2b5bb555'
down_revision: Union[str, Sequence[str], None] = '81483707fc18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
