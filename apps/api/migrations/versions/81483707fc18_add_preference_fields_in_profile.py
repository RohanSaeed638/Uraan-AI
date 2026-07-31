"""add preference fields in profile

Revision ID: 81483707fc18
Revises: f07e917e391f
Create Date: 2026-07-31 15:02:28.537874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81483707fc18'
down_revision: Union[str, Sequence[str], None] = 'f07e917e391f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
