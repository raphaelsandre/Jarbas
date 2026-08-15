import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.gateway.models import GatewayInput
from app.gateway.service import process_gateway_input
from app.gateway.websocket.manager import websocket_connection_manager
from app.gateway.websocket.models import WebSocketClientEvent, WebSocketServerEvent
from app.interactions.service import interaction_service

logger = logging.getLogger(__name__)
router = APIRouter()


async def send_processing_error(websocket: WebSocket) -> None:
    response = WebSocketServerEvent(
        type="error",
        message="Não foi possível processar a mensagem.",
    )
    await websocket_connection_manager.send_json(
        websocket,
        response.model_dump(),
    )


async def restore_awaiting_delivery(websocket: WebSocket) -> None:
    try:
        interactions = await interaction_service.get_awaiting_delivery()
    except Exception:
        logger.exception("Could not load interactions awaiting delivery")
        return

    for interaction in interactions:
        if interaction.result is None:
            await interaction_service.mark_failed_safely(
                interaction.id,
                "Interaction awaiting delivery has no result",
            )
            continue

        await websocket_connection_manager.send_json(
            websocket,
            interaction.result.model_dump(),
        )
        await interaction_service.mark_completed_safely(interaction.id)


@router.websocket("/ws")
async def websocket_router(websocket: WebSocket) -> None:
    await websocket_connection_manager.connect(websocket)
    try:
        await restore_awaiting_delivery(websocket)
        while True:
            payload = await websocket.receive_json()
            try:
                event = WebSocketClientEvent.model_validate(payload)
            except Exception:
                logger.exception("Invalid WebSocket event")
                await send_processing_error(websocket)
                continue

            if event.type == "ping":
                response = WebSocketServerEvent(
                    type="pong",
                    message="Beleza meu patrao?",
                )
                await websocket_connection_manager.send_json(
                    websocket,
                    response.model_dump(),
                )
                continue

            gateway_input = GatewayInput(
                text=event.text,
                files=event.files,
            )
            try:
                interaction, result = await interaction_service.execute(
                    gateway_input,
                    process_gateway_input,
                )
            except Exception:
                logger.exception("Could not process WebSocket input")
                await send_processing_error(websocket)
                continue

            await websocket_connection_manager.send_json(
                websocket,
                result.model_dump(),
            )
            await interaction_service.mark_completed_safely(
                interaction.id,
            )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WebSocket connection stopped unexpectedly")
    finally:
        websocket_connection_manager.disconnect(websocket)
