from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ToolCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9_.-]+$")
    description: str = Field(min_length=3, max_length=500)
    endpoint: HttpUrl
    method: Literal["POST", "PUT", "PATCH"] = "POST"
    timeout_seconds: float = Field(default=20, ge=1, le=120)
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def reserved_names(cls, value: str) -> str:
        if value == "conversation":
            raise ValueError("conversation é uma intent reservada")
        return value


class ToolUpdate(ToolCreate):
    pass


class ToolDefinition(ToolCreate):
    id: UUID
    endpoint: str
    created_at: datetime
    updated_at: datetime


class ModelSelection(BaseModel):
    model: str = Field(min_length=1, max_length=200)
