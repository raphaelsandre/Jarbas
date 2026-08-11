from typing import Any
from pydantic import BaseModel


class ToolResult(BaseModel):
    output: Any
    metadata: dict[str, Any] = {}