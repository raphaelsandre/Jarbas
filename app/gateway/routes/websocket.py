from app.gateway.service import process_gateway_input
from app.gateway.models import GatewayInput
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.gateway.websocket.manager import websocket_connection_manager
from app.gateway.websocket.models import WebSocketClientEvent, WebSocketServerEvent
from dataclasses import asdict

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
                    type="pong", message="Beleza meu patrao?"
                )
                await websocket_connection_manager.send_json(
                    websocket, asdict(response) 
                )
                continue
            if event.type == "input":
                gateway_input= GatewayInput(
                    text=event.text, files=event.files
                )
                result = await process_gateway_input(gateway_input)
            await websocket_connection_manager.send_json(
                websocket, asdict(result)
            )
    except WebSocketDisconnect:
        websocket_connection_manager.disconnect(websocket)
