"""resources.task_id: not null, indexed, cascade on delete

Revision ID: a1c3e5f7b9d2
Revises: 9826d58b7248
Create Date: 2026-10-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3e5f7b9d2'
down_revision: Union[str, Sequence[str], None] = '9826d58b7248'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM resources WHERE task_id IS NULL")
    op.alter_column(
        'resources', 'task_id',
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.create_index(
        op.f('ix_resources_task_id'), 'resources', ['task_id'], unique=False
    )
    op.drop_constraint(
        'resources_task_id_fkey', 'resources', type_='foreignkey'
    )
    op.create_foreign_key(
        'resources_task_id_fkey', 'resources', 'roadmap_tasks',
        ['task_id'], ['id'], ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint(
        'resources_task_id_fkey', 'resources', type_='foreignkey'
    )
    op.create_foreign_key(
        'resources_task_id_fkey', 'resources', 'roadmap_tasks',
        ['task_id'], ['id'],
    )
    op.drop_index(op.f('ix_resources_task_id'), table_name='resources')
    op.alter_column(
        'resources', 'task_id',
        existing_type=sa.UUID(),
        nullable=True,
    )
