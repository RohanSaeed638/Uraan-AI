"""add preference fields in profile

Revision ID: 55dd46c4e702
Revises: 8acf5c33f6a7
Create Date: 2026-07-31 16:32:20.305999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55dd46c4e702'
down_revision: Union[str, Sequence[str], None] = '8acf5c33f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
