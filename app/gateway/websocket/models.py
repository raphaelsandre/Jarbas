from typing import Literal
from pydantic import BaseModel


class WebSocketClientEvent(BaseModel):
    type: Literal["ping", "input"]
    text: str | None = None
    files: list[str] | None = None


class WebSocketServerEvent(BaseModel):
    type: Literal["pong", "error"]
    message: str
