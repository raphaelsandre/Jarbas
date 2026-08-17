from aiosqlite import Connection

from app.database.connection import get_database_connection
from app.shared.llm.client import llm_client

MAX_CONTEXT = 3


async def init_context() -> None:
    async with get_database_connection() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope TEXT NOT NULL DEFAULT 'default',
                model TEXT NOT NULL,
                user_input TEXT NOT NULL,
                jarbas_output TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor = await db.execute("PRAGMA table_info(context)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "scope" not in columns:
            await db.execute(
                "ALTER TABLE context ADD COLUMN scope TEXT NOT NULL DEFAULT 'default'"
            )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_context_scope_id ON context(scope, id)"
        )


async def add_context(
    user_input: str,
    jarbas_output: str,
    *,
    scope: str = "default",
) -> None:
    async with get_database_connection() as db:
        await db.execute(
            """
            INSERT INTO context (
                scope,
                model,
                user_input,
                jarbas_output
            )
            VALUES (?, ?, ?, ?)
            """,
            (scope, llm_client.model, user_input, jarbas_output),
        )
        await trim_context(db, scope)


async def get_context(*, scope: str = "default") -> list[dict]:
    async with get_database_connection() as db:
        cursor = await db.execute(
            """
            SELECT user_input, jarbas_output
            FROM context
            WHERE scope = ?
            ORDER BY id ASC
            """,
            (scope,),
        )
        rows = await cursor.fetchall()
        return [
            {"user": row["user_input"], "jarbas": row["jarbas_output"]}
            for row in rows
        ]


async def trim_context(db: Connection, scope: str) -> None:
    cursor = await db.execute(
        "SELECT COUNT(*) FROM context WHERE scope = ?",
        (scope,),
    )
    count = (await cursor.fetchone())[0]
    excess = count - MAX_CONTEXT
    if excess <= 0:
        return
    await db.execute(
        """
        DELETE FROM context
        WHERE scope = ? AND id IN (
            SELECT id FROM context
            WHERE scope = ?
            ORDER BY id ASC
            LIMIT ?
        )
        """,
        (scope, scope, excess),
    )


async def clear_context(*, scope: str | None = None) -> None:
    async with get_database_connection() as db:
        if scope is None:
            await db.execute("DELETE FROM context")
        else:
            await db.execute("DELETE FROM context WHERE scope = ?", (scope,))
