"""Guards the database's Row Level Security.

Supabase exposes every public table to the public (anon) key. Each table
must therefore have RLS enabled, or its data is readable by anyone who opens
the website's JavaScript. These tests need the real database and are skipped
when it is not reachable (for example on a machine without a .env).
"""
import asyncio
import selectors

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def _query(sql: str):
    from app.core.config import settings

    async def run():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                return (await conn.execute(text(sql))).all()
        finally:
            await engine.dispose()

    return asyncio.run(
        run(),
        loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
    )


def _rows_or_skip(sql: str):
    try:
        return _query(sql)
    except Exception as exc:  # no database in this environment
        pytest.skip(f"database not reachable: {type(exc).__name__}")


def test_every_public_table_has_row_level_security():
    rows = _rows_or_skip(
        "select c.relname from pg_class c "
        "join pg_namespace n on n.oid = c.relnamespace "
        "where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity "
        "order by c.relname"
    )

    unprotected = [r[0] for r in rows]

    assert unprotected == [], (
        "These tables are readable through the public Supabase key. Enable RLS "
        f"for them in a migration: {unprotected}"
    )


def test_backend_role_still_bypasses_rls():
    """The API connects as a role that bypasses RLS; if that changed, every
    query would silently return nothing."""
    rows = _rows_or_skip(
        "select r.rolbypassrls or r.rolsuper from pg_roles r "
        "where r.rolname = current_user"
    )

    assert rows[0][0] is True
