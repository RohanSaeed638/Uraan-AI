"""Deleting a learner and everything stored about them.

There is no "delete my account" button; the Privacy Policy promises deletion on
request, and `scripts/delete_account.py` is how that request is carried out.

A learner's rows hang off `profiles` through many tables, and `profiles` is not
linked to Supabase's `auth.users` by a foreign key, so deleting the sign-in does
not remove them. This walks the foreign keys from `profiles` downwards and
deletes the deepest rows first, so it needs no list of tables that could go
stale when a new table is added.
"""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

CHILDREN = text(
    "select c.conrelid::regclass::text as child, a.attname as col "
    "from pg_constraint c "
    "join pg_attribute a on a.attrelid = c.conrelid and a.attnum = c.conkey[1] "
    "where c.contype = 'f' and c.confrelid = cast(:parent as regclass)"
)


async def _purge(conn: AsyncConnection, table: str, where_sql: str, params: dict, deleted: dict[str, int]) -> None:
    """Deletes the rows of `table` matching `where_sql`, after everything that points at them."""
    for child, col in (await conn.execute(CHILDREN, {"parent": table})).all():
        # Rows in Supabase's own schemas are not ours to touch.
        if child.startswith(("auth.", "storage.")):
            continue

        await _purge(conn, child, f"{col} in (select id from {table} where {where_sql})", params, deleted)

    result = await conn.execute(text(f"delete from {table} where {where_sql}"), params)
    deleted[table] = deleted.get(table, 0) + (result.rowcount or 0)


async def delete_learner(conn: AsyncConnection, auth_user_id: UUID, remove_login: bool = True) -> dict[str, int]:
    """Deletes the learner's profile and all that belongs to it, and (by default)
    their Supabase sign-in. Returns how many rows went from each table. Run it
    inside a transaction; rolling that back undoes everything."""
    deleted: dict[str, int] = {}

    await _purge(conn, "profiles", "auth_user_id = :user", {"user": auth_user_id}, deleted)

    if remove_login:
        result = await conn.execute(text("delete from auth.users where id = :user"), {"user": auth_user_id})
        deleted["auth.users"] = result.rowcount or 0

    return {table: count for table, count in deleted.items() if count}
