from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
import aiosqlite

DATABASE_PATH = Path("app/database/db/jarbas.db")

@asynccontextmanager
async def get_database_connection() -> AsyncIterator[aiosqlite.Connection]:
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    connection = await aiosqlite.connect(DATABASE_PATH)
    connection.row_factory = aiosqlite.Row
    try:
        yield connection
        await connection.commit()
    except Exception:
        await connection.rollback()
        raise

    finally:
        await connection.close()

