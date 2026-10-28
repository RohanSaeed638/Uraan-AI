"""fix roadmap statuses

Revision ID: 8f59c4ef9283
Revises: 6c294c471542
Create Date: 2026-10-19 00:11:36.279497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f59c4ef9283'
down_revision: Union[str, Sequence[str], None] = '6c294c471542'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Repair statuses written by the old bug that saved every new roadmap
    as "completed". Rules: "completed" only when every task is done; at most
    one "active" roadmap per learner (the newest); the rest are "archived"
    and can be re-activated from the roadmaps page."""

    # 1. "completed" but with unfinished (or no) tasks -> archived.
    op.execute("""
        UPDATE roadmaps r SET status = 'archived'
        WHERE r.status = 'completed'
          AND (
            NOT EXISTS (
              SELECT 1 FROM roadmap_phases p
              JOIN roadmap_tasks t ON t.phase_id = p.id
              WHERE p.roadmap_id = r.id
            )
            OR EXISTS (
              SELECT 1 FROM roadmap_phases p
              JOIN roadmap_tasks t ON t.phase_id = p.id
              WHERE p.roadmap_id = r.id AND t.completed = false
            )
          )
    """)

    # 2. More than one active roadmap per learner -> keep only the newest.
    op.execute("""
        UPDATE roadmaps r SET status = 'archived'
        WHERE r.status = 'active'
          AND EXISTS (
            SELECT 1 FROM roadmaps o
            WHERE o.profile_id = r.profile_id
              AND o.status = 'active'
              AND o.created_at > r.created_at
          )
    """)

    # 3. A learner left with no active roadmap gets their newest archived one.
    op.execute("""
        UPDATE roadmaps r SET status = 'active'
        WHERE r.status = 'archived'
          AND NOT EXISTS (
            SELECT 1 FROM roadmaps o
            WHERE o.profile_id = r.profile_id AND o.status = 'active'
          )
          AND r.created_at = (
            SELECT max(o.created_at) FROM roadmaps o
            WHERE o.profile_id = r.profile_id AND o.status = 'archived'
          )
    """)


def downgrade() -> None:
    """Data repair only; the previous (wrong) statuses are not restored."""
    pass
