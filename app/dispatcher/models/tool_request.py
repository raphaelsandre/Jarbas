from pydantic import BaseModel
from typing import Any


class ToolRequest(BaseModel):
    tool: str
    payload: dict[str, Any]