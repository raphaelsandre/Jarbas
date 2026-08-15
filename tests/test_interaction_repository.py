import asyncio
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

import app.api.routes.input as http_route
import app.database.connection as database_connection
import app.gateway.routes.websocket as websocket_route
import app.interactions.service as interaction_service_module
from app.gateway.models import GatewayInput, GatewayResult
from app.interactions.models import InteractionStatus
from app.interactions.repository import InteractionRepository
from app.interactions.service import InteractionService, interaction_service
from app.main import app
from app.thinking.models import Intent


async def successful_processor(gateway_input: GatewayInput) -> GatewayResult:
    return GatewayResult(
        input=gateway_input.text or "",
        output="resposta entregue",
        intent=Intent(name="conversation"),
    )


async def failed_processor(gateway_input: GatewayInput) -> GatewayResult:
    raise ValueError("falha controlada")


class FakeWebSocket:
    def __init__(
        self,
        payloads: list[dict] | None = None,
        fail_delivery: bool = False,
    ) -> None:
        self.payloads = list(payloads or [])
        self.fail_delivery = fail_delivery
        self.sent_payloads: list[dict] = []
        self.statuses_during_send: list[str] = []

    async def accept(self) -> None:
        pass

    async def receive_json(self) -> dict:
        if not self.payloads:
            raise WebSocketDisconnect()
        return self.payloads.pop(0)

    async def send_json(self, payload: dict) -> None:
        with sqlite3.connect(database_connection.DATABASE_PATH) as database:
            row = database.execute(
                """
                SELECT status
                FROM interactions
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()
        if row is not None:
            self.statuses_during_send.append(row[0])
        if self.fail_delivery:
            raise WebSocketDisconnect()
        self.sent_payloads.append(payload)


class TemporaryDatabaseTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database_connection.DATABASE_PATH
        database_connection.DATABASE_PATH = (
            Path(self.temporary_directory.name) / "jarbas.db"
        )
        self.repository = InteractionRepository()
        self.service = InteractionService(self.repository)
        await self.repository.initialize()

    async def asyncTearDown(self) -> None:
        database_connection.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    async def test_interaction_lifecycle_reaches_completed(self) -> None:
        interaction, result = await self.service.execute(
            GatewayInput(text="ola"),
            successful_processor,
        )

        awaiting = await self.repository.get(interaction.id)
        self.assertIsNotNone(awaiting)
        self.assertEqual(
            awaiting.status,
            InteractionStatus.AWAITING_DELIVERY,
        )
        self.assertEqual(awaiting.result, result)
        self.assertIsNone(awaiting.completed_at)
        self.assertIsNone(awaiting.delivered_at)

        completed = await self.service.mark_completed(interaction.id)
        persisted = await self.repository.get(interaction.id)

        self.assertEqual(completed.status, InteractionStatus.COMPLETED)
        self.assertEqual(persisted.status, InteractionStatus.COMPLETED)
        self.assertEqual(persisted.completed_at, persisted.delivered_at)
        self.assertIsNotNone(persisted.completed_at)

    async def test_processing_failure_reaches_failed(self) -> None:
        with self.assertRaisesRegex(ValueError, "falha controlada"):
            await self.service.execute(
                GatewayInput(text="ola"),
                failed_processor,
            )

        failed = await self.repository.list_by_status(
            InteractionStatus.FAILED,
        )
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].error, "falha controlada")
        self.assertIsNotNone(failed[0].failed_at)
        self.assertIsNone(failed[0].completed_at)
        self.assertIsNone(failed[0].delivered_at)

    async def test_websocket_reconnect_restores_same_interaction(self) -> None:
        interaction, _ = await interaction_service.execute(
            GatewayInput(text="restaurar"),
            successful_processor,
        )
        websocket = FakeWebSocket()

        await websocket_route.websocket_router(websocket)

        restored = await self.repository.get(interaction.id)
        with sqlite3.connect(database_connection.DATABASE_PATH) as database:
            count = database.execute(
                "SELECT COUNT(*) FROM interactions"
            ).fetchone()[0]

        self.assertEqual(count, 1)
        self.assertEqual(restored.id, interaction.id)
        self.assertEqual(restored.status, InteractionStatus.COMPLETED)
        self.assertEqual(
            websocket.statuses_during_send,
            [InteractionStatus.AWAITING_DELIVERY.value],
        )
        self.assertEqual(len(websocket.sent_payloads), 1)

    async def test_websocket_disconnect_keeps_awaiting_delivery(self) -> None:
        original_processor = websocket_route.process_gateway_input
        websocket_route.process_gateway_input = successful_processor
        websocket = FakeWebSocket(
            payloads=[{"type": "input", "text": "ola"}],
            fail_delivery=True,
        )
        try:
            await websocket_route.websocket_router(websocket)
        finally:
            websocket_route.process_gateway_input = original_processor

        awaiting = await self.repository.list_by_status(
            InteractionStatus.AWAITING_DELIVERY,
        )
        self.assertEqual(len(awaiting), 1)
        self.assertIsNone(awaiting[0].completed_at)
        self.assertIsNone(awaiting[0].delivered_at)


    async def test_websocket_error_does_not_interrupt_next_input(self) -> None:
        calls = 0

        async def fail_once(gateway_input: GatewayInput) -> GatewayResult:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ValueError("falha controlada")
            return await successful_processor(gateway_input)

        original_processor = websocket_route.process_gateway_input
        websocket_route.process_gateway_input = fail_once
        websocket = FakeWebSocket(
            payloads=[
                {"type": "input", "text": "falhar"},
                {"type": "input", "text": "continuar"},
            ]
        )
        with self.assertLogs(websocket_route.logger, level="ERROR"):
            try:
                await websocket_route.websocket_router(websocket)
            finally:
                websocket_route.process_gateway_input = original_processor

        with sqlite3.connect(database_connection.DATABASE_PATH) as database:
            statuses = [
                row[0]
                for row in database.execute(
                    "SELECT status FROM interactions ORDER BY created_at ASC"
                )
            ]

        self.assertEqual(
            statuses,
            [
                InteractionStatus.FAILED.value,
                InteractionStatus.COMPLETED.value,
            ],
        )
        self.assertEqual(websocket.sent_payloads[0]["type"], "error")
        self.assertEqual(
            websocket.sent_payloads[1]["output"],
            "resposta entregue",
        )

    async def test_invalid_restore_does_not_block_next_interaction(self) -> None:
        first, _ = await interaction_service.execute(
            GatewayInput(text="invalida"),
            successful_processor,
        )
        second, _ = await interaction_service.execute(
            GatewayInput(text="valida"),
            successful_processor,
        )
        with sqlite3.connect(database_connection.DATABASE_PATH) as database:
            database.execute(
                "UPDATE interactions SET result = NULL WHERE id = ?",
                (str(first.id),),
            )
            database.commit()

        websocket = FakeWebSocket()
        await websocket_route.websocket_router(websocket)

        restored_first = await self.repository.get(first.id)
        restored_second = await self.repository.get(second.id)
        self.assertEqual(restored_first.status, InteractionStatus.FAILED)
        self.assertEqual(restored_second.status, InteractionStatus.COMPLETED)
        self.assertEqual(len(websocket.sent_payloads), 1)
        self.assertEqual(
            websocket.sent_payloads[0]["output"],
            "resposta entregue",
        )


class HttpInteractionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database_connection.DATABASE_PATH
        self.original_processor = http_route.process_gateway_input
        self.original_mark_completed_safely = interaction_service.mark_completed_safely
        database_connection.DATABASE_PATH = (
            Path(self.temporary_directory.name) / "jarbas.db"
        )
        http_route.process_gateway_input = successful_processor

    def tearDown(self) -> None:
        interaction_service.mark_completed_safely = self.original_mark_completed_safely
        http_route.process_gateway_input = self.original_processor
        database_connection.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    def test_http_response_completes_after_delivery(self) -> None:
        statuses_before_completion: list[InteractionStatus] = []

        async def observe_and_complete(interaction_id):
            interaction = await interaction_service.repository.get(
                interaction_id
            )
            statuses_before_completion.append(interaction.status)
            return await self.original_mark_completed_safely(interaction_id)

        interaction_service.mark_completed_safely = observe_and_complete

        with TestClient(app) as client:
            response = client.post("/input", json={"text": "ola"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["output"], "resposta entregue")
        self.assertEqual(
            statuses_before_completion,
            [InteractionStatus.AWAITING_DELIVERY],
        )

        with sqlite3.connect(database_connection.DATABASE_PATH) as database:
            row = database.execute(
                """
                SELECT status, completed_at, delivered_at
                FROM interactions
                """
            ).fetchone()

        self.assertEqual(row[0], InteractionStatus.COMPLETED.value)
        self.assertIsNotNone(row[1])
        self.assertEqual(row[1], row[2])

    def test_http_failure_does_not_interrupt_next_request(self) -> None:
        http_route.process_gateway_input = failed_processor

        with TestClient(app, raise_server_exceptions=False) as client:
            failed_response = client.post("/input", json={"text": "falhar"})
            http_route.process_gateway_input = successful_processor
            successful_response = client.post("/input", json={"text": "continuar"})

        self.assertEqual(failed_response.status_code, 500)
        self.assertEqual(successful_response.status_code, 200)
        with sqlite3.connect(database_connection.DATABASE_PATH) as database:
            rows = database.execute(
                """
                SELECT status, error, failed_at, completed_at, delivered_at
                FROM interactions
                ORDER BY created_at ASC
                """
            ).fetchall()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], InteractionStatus.FAILED.value)
        self.assertEqual(rows[0][1], "falha controlada")
        self.assertIsNotNone(rows[0][2])
        self.assertIsNone(rows[0][3])
        self.assertIsNone(rows[0][4])
        self.assertEqual(rows[1][0], InteractionStatus.COMPLETED.value)
        self.assertIsNotNone(rows[1][3])
        self.assertEqual(rows[1][3], rows[1][4])

    def test_http_completion_error_is_restored_by_websocket(self) -> None:
        original_mark_completed = interaction_service.mark_completed

        async def fail_completion(interaction_id):
            raise RuntimeError("falha ao persistir completed")

        interaction_service.mark_completed = fail_completion
        try:
            with TestClient(app) as client:
                with self.assertLogs(
                    interaction_service_module.logger,
                    level="ERROR",
                ):
                    response = client.post(
                        "/input",
                        json={"text": "recuperar"},
                    )
                interaction_service.mark_completed = original_mark_completed
                with client.websocket_connect("/ws") as websocket:
                    restored_payload = websocket.receive_json()
                    websocket.send_json({"type": "ping"})
                    websocket.receive_json()
        finally:
            interaction_service.mark_completed = original_mark_completed

        self.assertEqual(response.status_code, 200)
        self.assertEqual(restored_payload["output"], "resposta entregue")
        with sqlite3.connect(database_connection.DATABASE_PATH) as database:
            row = database.execute(
                """
                SELECT status, completed_at, delivered_at
                FROM interactions
                """
            ).fetchone()
            count = database.execute(
                "SELECT COUNT(*) FROM interactions"
            ).fetchone()[0]

        self.assertEqual(count, 1)
        self.assertEqual(row[0], InteractionStatus.COMPLETED.value)
        self.assertIsNotNone(row[1])
        self.assertEqual(row[1], row[2])

    def test_real_websocket_reconnect_restores_without_new_row(self) -> None:
        with TestClient(app) as client:
            interaction, _ = asyncio.run(
                interaction_service.execute(
                    GatewayInput(text="restaurar via WSS real"),
                    successful_processor,
                )
            )
            with client.websocket_connect("/ws") as websocket:
                payload = websocket.receive_json()
                websocket.send_json({"type": "ping"})
                pong = websocket.receive_json()

        restored = asyncio.run(
            interaction_service.repository.get(interaction.id)
        )
        with sqlite3.connect(database_connection.DATABASE_PATH) as database:
            count = database.execute(
                "SELECT COUNT(*) FROM interactions"
            ).fetchone()[0]

        self.assertEqual(payload["output"], "resposta entregue")
        self.assertEqual(pong["type"], "pong")
        self.assertEqual(count, 1)
        self.assertEqual(restored.id, interaction.id)
        self.assertEqual(restored.status, InteractionStatus.COMPLETED)
        self.assertEqual(restored.completed_at, restored.delivered_at)


if __name__ == "__main__":
    unittest.main()
