import json
import tempfile
import unittest
from pathlib import Path

import app.database.connection as database_connection
import app.realtime.piesocket as piesocket_module
from app.gateway.models import GatewayInput, GatewayResult
from app.interactions.models import InteractionStatus
from app.interactions.repository import InteractionRepository
from app.interactions.service import InteractionService
from app.realtime.piesocket import PieSocketBridge
from app.thinking.models import Intent


async def successful_processor(gateway_input: GatewayInput) -> GatewayResult:
    return GatewayResult(
        input=gateway_input.text or "",
        output="resposta pelo broker",
        intent=Intent(name="conversation"),
    )


class FakePieSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send(self, raw: str) -> None:
        self.messages.append(json.loads(raw))


class PieSocketBridgeTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database_connection.DATABASE_PATH
        self.original_service = piesocket_module.interaction_service
        self.original_processor = piesocket_module.process_gateway_input
        database_connection.DATABASE_PATH = Path(self.temporary_directory.name) / "jarbas.db"
        repository = InteractionRepository()
        await repository.initialize()
        piesocket_module.interaction_service = InteractionService(repository)
        piesocket_module.process_gateway_input = successful_processor
        self.bridge = PieSocketBridge("wss://example.test")
        self.socket = FakePieSocket()

    async def asyncTearDown(self) -> None:
        database_connection.DATABASE_PATH = self.original_database_path
        piesocket_module.interaction_service = self.original_service
        piesocket_module.process_gateway_input = self.original_processor
        self.temporary_directory.cleanup()

    async def test_result_remains_pending_until_matching_ack(self) -> None:
        await self.bridge._process_input(
            self.socket,
            {
                "request_id": "request-1",
                "client_id": "client-1",
                "text": "olá",
            },
        )
        message = self.socket.messages[0]
        self.assertEqual(message["event"], "jarbas:result")
        self.assertEqual(message["data"]["response"]["output"], "resposta pelo broker")

        interaction_id = message["data"]["interaction_id"]
        interaction = await piesocket_module.interaction_service.repository.get(interaction_id)
        self.assertEqual(interaction.status, InteractionStatus.AWAITING_DELIVERY)

        await self.bridge._acknowledge(
            {
                "request_id": "request-1",
                "client_id": "client-1",
                "interaction_id": interaction_id,
            }
        )
        delivered = await piesocket_module.interaction_service.repository.get(interaction_id)
        self.assertEqual(delivered.status, InteractionStatus.COMPLETED)

    async def test_recover_republishes_only_the_requesting_client(self) -> None:
        await self.bridge._process_input(
            self.socket,
            {"request_id": "request-1", "client_id": "client-1", "text": "um"},
        )
        await self.bridge._process_input(
            self.socket,
            {"request_id": "request-2", "client_id": "client-2", "text": "dois"},
        )
        recovered = FakePieSocket()
        await self.bridge._recover(recovered, {"client_id": "client-1"})

        self.assertEqual(len(recovered.messages), 1)
        self.assertEqual(recovered.messages[0]["data"]["request_id"], "request-1")


if __name__ == "__main__":
    unittest.main()
