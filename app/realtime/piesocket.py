import asyncio
import json
import logging
from contextlib import suppress
from uuid import UUID

from websockets.asyncio.client import connect

from app.config import settings
from app.gateway.models import GatewayInput
from app.gateway.service import process_gateway_input
from app.interactions.service import interaction_service

logger = logging.getLogger(__name__)


class PieSocketBridge:
    def __init__(self, url: str) -> None:
        self.url = url
        self.connected = False
        self._stop = asyncio.Event()
        self._tasks: set[asyncio.Task] = set()

    async def run(self) -> None:
        retry = 1
        while not self._stop.is_set():
            try:
                async with connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                    max_size=1024 * 1024,
                ) as websocket:
                    self.connected = True
                    retry = 1
                    async for raw in websocket:
                        task = asyncio.create_task(self._handle(websocket, raw))
                        self._tasks.add(task)
                        task.add_done_callback(self._tasks.discard)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("PieSocket bridge disconnected")
            finally:
                self.connected = False

            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._stop.wait(), timeout=retry)
            retry = min(retry * 2, 15)

    async def stop(self) -> None:
        self._stop.set()
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _handle(self, websocket, raw: str | bytes) -> None:
        try:
            envelope = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return
        event = envelope.get("event")
        data = envelope.get("data")
        if not isinstance(data, dict):
            return

        if event == "jarbas:input":
            await self._process_input(websocket, data)
        elif event == "jarbas:ack":
            await self._acknowledge(data)
        elif event == "jarbas:recover":
            await self._recover(websocket, data)

    async def _process_input(self, websocket, data: dict) -> None:
        request_id = data.get("request_id")
        client_id = data.get("client_id")
        text = data.get("text")
        if not all(isinstance(value, str) and value for value in (request_id, client_id, text)):
            return

        gateway_input = GatewayInput(
            text=text,
            data={"request_id": request_id, "client_id": client_id},
        )
        try:
            interaction, result = await interaction_service.execute(
                gateway_input,
                process_gateway_input,
            )
            await self._publish_result(
                websocket,
                interaction_id=str(interaction.id),
                request_id=request_id,
                client_id=client_id,
                response=result.model_dump(mode="json"),
            )
        except Exception:
            logger.exception("Could not process PieSocket input")
            await self._publish(
                websocket,
                "jarbas:error",
                {
                    "request_id": request_id,
                    "client_id": client_id,
                    "message": "Não foi possível processar a mensagem.",
                },
            )

    async def _acknowledge(self, data: dict) -> None:
        try:
            interaction_id = UUID(str(data.get("interaction_id")))
        except ValueError:
            return
        interaction = await interaction_service.repository.get(interaction_id)
        if interaction is None or not interaction.input.data:
            return
        if (
            interaction.input.data.get("request_id") != data.get("request_id")
            or interaction.input.data.get("client_id") != data.get("client_id")
        ):
            return
        await interaction_service.mark_completed_safely(interaction_id)

    async def _recover(self, websocket, data: dict) -> None:
        client_id = data.get("client_id")
        if not isinstance(client_id, str) or not client_id:
            return
        interactions = await interaction_service.get_awaiting_delivery()
        for interaction in interactions:
            metadata = interaction.input.data or {}
            if metadata.get("client_id") != client_id or interaction.result is None:
                continue
            await self._publish_result(
                websocket,
                interaction_id=str(interaction.id),
                request_id=str(metadata.get("request_id")),
                client_id=client_id,
                response=interaction.result.model_dump(mode="json"),
            )

    async def _publish_result(
        self,
        websocket,
        *,
        interaction_id: str,
        request_id: str,
        client_id: str,
        response: dict,
    ) -> None:
        await self._publish(
            websocket,
            "jarbas:result",
            {
                "interaction_id": interaction_id,
                "request_id": request_id,
                "client_id": client_id,
                "response": response,
            },
        )

    @staticmethod
    async def _publish(websocket, event: str, data: dict) -> None:
        await websocket.send(
            json.dumps({"event": event, "data": data}, ensure_ascii=False)
        )


piesocket_bridge = PieSocketBridge(settings.piesocket_ws_url)
