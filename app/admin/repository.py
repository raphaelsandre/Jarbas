from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.admin.models import ToolCreate, ToolDefinition
from app.database.connection import get_database_connection


class AdminRepository:
    async def initialize(self) -> None:
        async with get_database_connection() as connection:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS registered_tools (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    timeout_seconds REAL NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_registered_tools_enabled
                ON registered_tools(enabled, name)
                """
            )
            await connection.execute("PRAGMA optimize")

    async def get_setting(self, key: str) -> str | None:
        async with get_database_connection() as connection:
            cursor = await connection.execute(
                "SELECT value FROM runtime_settings WHERE key = ?",
                (key,),
            )
            row = await cursor.fetchone()
            return None if row is None else str(row["value"])

    async def set_setting(self, key: str, value: str) -> None:
        now = datetime.now(UTC).isoformat()
        async with get_database_connection() as connection:
            await connection.execute(
                """
                INSERT INTO runtime_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE
                SET value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, now),
            )

    async def list_tools(self, *, enabled_only: bool = False) -> list[ToolDefinition]:
        query = "SELECT * FROM registered_tools"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name"
        async with get_database_connection() as connection:
            cursor = await connection.execute(query)
            return [self._tool_from_row(row) for row in await cursor.fetchall()]

    async def get_tool(self, tool_id: UUID) -> ToolDefinition | None:
        async with get_database_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM registered_tools WHERE id = ?",
                (str(tool_id),),
            )
            row = await cursor.fetchone()
            return None if row is None else self._tool_from_row(row)

    async def create_tool(self, payload: ToolCreate) -> ToolDefinition:
        now = datetime.now(UTC)
        tool = ToolDefinition(
            id=uuid4(),
            created_at=now,
            updated_at=now,
            endpoint=str(payload.endpoint),
            **payload.model_dump(exclude={"endpoint"}),
        )
        async with get_database_connection() as connection:
            await connection.execute(
                """
                INSERT INTO registered_tools (
                    id, name, description, endpoint, method, timeout_seconds,
                    enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(tool.id), tool.name, tool.description, tool.endpoint,
                    tool.method, tool.timeout_seconds, int(tool.enabled),
                    tool.created_at.isoformat(), tool.updated_at.isoformat(),
                ),
            )
        return tool

    async def update_tool(self, tool_id: UUID, payload: ToolCreate) -> ToolDefinition | None:
        existing = await self.get_tool(tool_id)
        if existing is None:
            return None
        tool = ToolDefinition(
            id=tool_id,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
            endpoint=str(payload.endpoint),
            **payload.model_dump(exclude={"endpoint"}),
        )
        async with get_database_connection() as connection:
            await connection.execute(
                """
                UPDATE registered_tools
                SET name = ?, description = ?, endpoint = ?, method = ?,
                    timeout_seconds = ?, enabled = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    tool.name, tool.description, tool.endpoint, tool.method,
                    tool.timeout_seconds, int(tool.enabled),
                    tool.updated_at.isoformat(), str(tool_id),
                ),
            )
        return tool

    async def delete_tool(self, tool_id: UUID) -> bool:
        async with get_database_connection() as connection:
            cursor = await connection.execute(
                "DELETE FROM registered_tools WHERE id = ?",
                (str(tool_id),),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _tool_from_row(row) -> ToolDefinition:
        return ToolDefinition(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            endpoint=row["endpoint"],
            method=row["method"],
            timeout_seconds=row["timeout_seconds"],
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


admin_repository = AdminRepository()
