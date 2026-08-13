from app.thinking.models import Intent
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InputFile:
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class GatewayInput:
    text: str | None = None
    data: dict[str, Any] | None = None
    files: list[InputFile] | None = None

@dataclass(frozen=True)
class GatewayResult:
    input: str
    intent: Intent
    output: str | None = None