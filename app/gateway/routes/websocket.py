from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.gateway.websocket.manager import websocket_connection_manager
from gateway.websocket.models import WebSocketClientEvent, WebSocketServerEvent

router = APIRouter()

@router.websocket("/ws")
async def websocket_router(websocket: WebSocket) -> None:
    await websocket_connection_manager.connect(websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            event = WebSocketClientEvent.model_validate(payload)
            if event.type == "ping":
                response = WebSocketServerEvent(
                    type="pong",
                    message="Jarbas websocket is COMENDO A PORRA TODA"
                )
                await websocket_connection_manager.send_json(
                    websocket,
                    response.model_dump()
                )
    except WebSocketDisconnect:
        websocket_connection_manager.disconnect(websocket)