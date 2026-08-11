from typing import Any
from pydantic import BaseModel

class ToolResponse(BaseModel):
    success: bool
    data: Any | None = None
    error: str | None = None