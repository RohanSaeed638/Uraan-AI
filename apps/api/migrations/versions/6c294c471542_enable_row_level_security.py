"""enable row level security

Revision ID: 6c294c471542
Revises: 342f7d4fda75
Create Date: 2026-10-19 00:11:33.765907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c294c471542'
down_revision: Union[str, Sequence[str], None] = '342f7d4fda75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Supabase exposes every table in the public schema through its REST API to
# anyone holding the public (anon) key. With RLS on and no policies, that key
# can read and write nothing. The backend connects as the table owner
# (`postgres`, which bypasses RLS), so the app itself is unaffected.
_FOR_EACH_PUBLIC_TABLE = """
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I {action} ROW LEVEL SECURITY', t.tablename);
  END LOOP;
END $$;
"""


def upgrade() -> None:
    """Enable RLS on every table in the public schema."""
    op.execute(_FOR_EACH_PUBLIC_TABLE.format(action="ENABLE"))


def downgrade() -> None:
    """Disable RLS again (this re-opens the tables to the public key)."""
    op.execute(_FOR_EACH_PUBLIC_TABLE.format(action="DISABLE"))
