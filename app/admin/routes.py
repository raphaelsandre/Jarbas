import sqlite3
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.admin.models import ModelSelection, ToolCreate, ToolDefinition
from app.admin import service
from app.security.auth import authenticate_request

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(authenticate_request)],
)


@router.get("/overview")
async def overview() -> dict:
    tables = await service.list_database_tables()
    models = await service.get_models()
    tools = await service.list_tools()
    return {
        "model": models["active"],
        "tables": len(tables),
        "rows": sum(item["rows"] for item in tables),
        "tools": len(tools),
        "tools_enabled": sum(1 for tool in tools if tool.enabled),
    }


@router.get("/models")
async def models() -> dict:
    return await service.get_models()


@router.put("/models")
async def select_model(payload: ModelSelection) -> dict:
    return await service.select_model(payload.model)


@router.get("/database")
async def database_tables() -> list[dict]:
    return await service.list_database_tables()


@router.get("/database/{table}")
async def database_table(
    table: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    try:
        return await service.read_database_table(table, limit=limit, offset=offset)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Tabela não encontrada") from error


@router.get("/tools", response_model=list[ToolDefinition])
async def tools() -> list[ToolDefinition]:
    return await service.list_tools()


@router.post("/tools", response_model=ToolDefinition, status_code=status.HTTP_201_CREATED)
async def create_tool(payload: ToolCreate) -> ToolDefinition:
    try:
        return await service.create_tool(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Já existe uma tool com esse nome") from error


@router.put("/tools/{tool_id}", response_model=ToolDefinition)
async def update_tool(tool_id: UUID, payload: ToolCreate) -> ToolDefinition:
    try:
        tool = await service.update_tool(tool_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Já existe uma tool com esse nome") from error
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool não encontrada")
    return tool


@router.delete("/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(tool_id: UUID) -> None:
    if not await service.delete_tool(tool_id):
        raise HTTPException(status_code=404, detail="Tool não encontrada")
