import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import app.database.connection as database_connection
from app.config import settings
from app.main import app
from app.shared.llm.client import llm_client


async def fake_models() -> list[str]:
    return ["qwen3:8b", "gemma3:12b"]


class AdminApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database_connection.DATABASE_PATH
        self.original_origins = settings.jarbas_tool_allowed_origins
        self.original_model = llm_client.model
        self.original_list_models = llm_client.list_models
        database_connection.DATABASE_PATH = Path(self.temporary_directory.name) / "jarbas.db"
        settings.jarbas_tool_allowed_origins = "https://automation.example"
        llm_client.list_models = fake_models
        self.headers = {
            "X-Jarbas-Key": settings.jarbas_api_key,
            "User-Agent": settings.jarbas_user_agent,
        }

    def tearDown(self) -> None:
        database_connection.DATABASE_PATH = self.original_database_path
        settings.jarbas_tool_allowed_origins = self.original_origins
        llm_client.set_model(self.original_model)
        llm_client.list_models = self.original_list_models
        self.temporary_directory.cleanup()

    def test_admin_requires_server_credentials(self) -> None:
        with TestClient(app) as client:
            response = client.get("/admin/overview")
        self.assertEqual(response.status_code, 403)

    def test_model_database_and_tool_management(self) -> None:
        with TestClient(app) as client:
            model_response = client.put(
                "/admin/models",
                headers=self.headers,
                json={"model": "gemma3:12b"},
            )
            self.assertEqual(model_response.status_code, 200)
            self.assertEqual(model_response.json()["active"], "gemma3:12b")

            tool_response = client.post(
                "/admin/tools",
                headers=self.headers,
                json={
                    "name": "casa.luzes",
                    "description": "Controla as luzes da casa",
                    "endpoint": "https://automation.example/hooks/luzes",
                    "method": "POST",
                    "timeout_seconds": 10,
                    "enabled": True,
                },
            )
            self.assertEqual(tool_response.status_code, 201)
            self.assertEqual(tool_response.json()["name"], "casa.luzes")

            tables = client.get("/admin/database", headers=self.headers)
            self.assertEqual(tables.status_code, 200)
            names = {item["name"] for item in tables.json()}
            self.assertIn("registered_tools", names)
            self.assertIn("runtime_settings", names)

            rows = client.get(
                "/admin/database/registered_tools",
                headers=self.headers,
            )
            self.assertEqual(rows.status_code, 200)
            self.assertEqual(rows.json()["total"], 1)

    def test_tool_endpoint_must_be_allowlisted(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/admin/tools",
                headers=self.headers,
                json={
                    "name": "externa",
                    "description": "Destino não autorizado",
                    "endpoint": "https://evil.example/hook",
                    "method": "POST",
                    "timeout_seconds": 10,
                    "enabled": True,
                },
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Origem não autorizada", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
