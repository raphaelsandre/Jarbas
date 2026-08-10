from pydantic import BaseModel, Field

from dataclasses import dataclass

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Intent:
    name: str
    action: str | None = None
    entities: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    requires_response: bool = True


class ThinkingProfile(BaseModel):
    version: int = 1
    vocabulary: dict[str, str] = Field(default_factory=dict)
    preferences: dict[str, str] = Field(default_factory=dict)

