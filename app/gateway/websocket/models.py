from typing import Literal
from pydantic import BaseModel


class WebSocketClientEvent(BaseModel):
    type: Literal["ping"]


class WebSocketServerEvent(BaseModel):
    type: Literal["pong"]
    message: str
