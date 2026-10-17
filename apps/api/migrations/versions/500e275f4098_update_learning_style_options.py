"""update learning style options

Revision ID: 500e275f4098
Revises: ec44e9870020
Create Date: 2026-08-19 14:30:09.633511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '500e275f4098'
down_revision: Union[str, Sequence[str], None] = 'ec44e9870020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
