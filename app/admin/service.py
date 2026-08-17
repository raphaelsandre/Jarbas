from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from app.admin.models import ToolCreate, ToolDefinition
from app.admin.repository import admin_repository
from app.config import settings
from app.database.connection import get_database_connection
from app.shared.llm.client import llm_client

MODEL_SETTING = "active_model"


def _allowed_tool_origins() -> set[str]:
    return {
        origin.strip().rstrip("/")
        for origin in settings.jarbas_tool_allowed_origins.split(",")
        if origin.strip()
    }


def validate_tool_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    if origin not in _allowed_tool_origins():
        raise ValueError(
            "Origem não autorizada. Configure JARBAS_TOOL_ALLOWED_ORIGINS no servidor."
        )


async def initialize_admin() -> None:
    await admin_repository.initialize()
    stored_model = await admin_repository.get_setting(MODEL_SETTING)
    if stored_model:
        llm_client.set_model(stored_model)


async def get_models() -> dict[str, Any]:
    available = await llm_client.list_models()
    active = llm_client.model
    if active not in available:
        available.insert(0, active)
    return {"active": active, "available": available}


async def select_model(model: str) -> dict[str, Any]:
    model = model.strip()
    llm_client.set_model(model)
    await admin_repository.set_setting(MODEL_SETTING, model)
    return await get_models()


async def list_database_tables() -> list[dict[str, Any]]:
    async with get_database_connection() as connection:
        cursor = await connection.execute(
            """
            SELECT name
            FROM sqlite_schema
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        tables = []
        for row in await cursor.fetchall():
            name = str(row["name"])
            count_cursor = await connection.execute(
                f'SELECT COUNT(*) AS total FROM "{name}"'
            )
            count = await count_cursor.fetchone()
            tables.append({"name": name, "rows": int(count["total"])})
        return tables


async def read_database_table(
    table: str,
    *,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    tables = {item["name"] for item in await list_database_tables()}
    if table not in tables:
        raise KeyError(table)

    async with get_database_connection() as connection:
        column_cursor = await connection.execute(f'PRAGMA table_info("{table}")')
        columns = [str(row["name"]) for row in await column_cursor.fetchall()]
        count_cursor = await connection.execute(
            f'SELECT COUNT(*) AS total FROM "{table}"'
        )
        total = int((await count_cursor.fetchone())["total"])
        cursor = await connection.execute(
            f'SELECT * FROM "{table}" ORDER BY rowid DESC LIMIT ? OFFSET ?',
            (limit, offset),
        )
        rows = [
            {
                key: (
                    value.decode("utf-8", errors="replace")
                    if isinstance(value, bytes)
                    else value
                )
                for key, value in dict(row).items()
            }
            for row in await cursor.fetchall()
        ]
    return {
        "table": table,
        "columns": columns,
        "rows": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def list_tools() -> list[ToolDefinition]:
    return await admin_repository.list_tools()


async def create_tool(payload: ToolCreate) -> ToolDefinition:
    validate_tool_endpoint(str(payload.endpoint))
    tool = await admin_repository.create_tool(payload)
    await reload_orchestrator_tools()
    return tool


async def update_tool(tool_id: UUID, payload: ToolCreate) -> ToolDefinition | None:
    validate_tool_endpoint(str(payload.endpoint))
    tool = await admin_repository.update_tool(tool_id, payload)
    if tool is not None:
        await reload_orchestrator_tools()
    return tool


async def delete_tool(tool_id: UUID) -> bool:
    deleted = await admin_repository.delete_tool(tool_id)
    if deleted:
        await reload_orchestrator_tools()
    return deleted


async def reload_orchestrator_tools() -> None:
    from app.handle.orchestrator import reload_registered_tools

    await reload_registered_tools()
