import aiosqlite


DB_PATH = "jarbas.db"
MAX_CONTEXT = 20


async def init_context() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                jarbas_output TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()

async def add_context(
    user_input: str,
    jarbas_output: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO context (
                user_input,
                jarbas_output
            )
            VALUES (?, ?)
            """,
            (
                user_input,
                jarbas_output,
            ),
        )
        await db.execute(
            """
            DELETE FROM context
            WHERE id NOT IN (
                SELECT id
                FROM context
                ORDER BY id DESC
                LIMIT ?
            )
            """,
            (MAX_CONTEXT,),
        )
        await trim_context(db)
        await db.commit()

async def get_context() -> list[dict]:
  async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                user_input,
                jarbas_output
            FROM context
            ORDER BY id ASC
            """
        )
        rows = await cursor.fetchall()
        return [
            {
                "user": row["user_input"],
                "jarbas": row["jarbas_output"],
            }
            for row in rows

        ]

async def trim_context(db) -> None:
    cursor = await db.execute(
        "SELECT COUNT(*) FROM context"
    )
    count = (await cursor.fetchone())[0]
    excess = count - MAX_CONTEXT
    if excess <= 0:
        return
    await db.execute(
        """
        DELETE FROM context
            WHERE id IN (SELECT id
                         FROM context
                         ORDER BY id ASC
                LIMIT ?
                )
        """,
        (excess,),
    )

async def clear_context() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM context")
        await db.commit()
