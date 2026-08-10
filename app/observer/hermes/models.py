from pydantic import BaseModel, Field

class HermesProfile(BaseModel):
    version: int = 1
    vocabulary: dict[str, str] = Field(default_factory=dict)
    preferences: dict[str, str] = Field(default_factory=dict)
