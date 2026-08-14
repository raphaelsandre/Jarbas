from app.thinking.models import Intent
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict
from typing import Any

@dataclass(frozen=True)
class InputFile:
    filename: str
    content_type: str
    content: bytes


class GatewayInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str | None = None
    data: dict[str, Any] | None = None
    files: list[InputFile] | None = None

class GatewayResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    input: str
    intent: Intent
    output: str | None = None