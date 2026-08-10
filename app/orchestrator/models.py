from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExecutionResult:
    success: bool
    handler: str
    intent: str
    action: str | None = None
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    response_hint: str | None = None
