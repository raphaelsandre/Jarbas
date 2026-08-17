import tempfile
import unittest
from pathlib import Path

import app.context.short_term as short_term
import app.database.connection as database_connection
import app.response.engine as response_engine
import app.thinking.engine as thinking_engine


class FakeLLM:
    def __init__(self, response: str = "resposta atual") -> None:
        self.response = response
        self.calls: list[tuple[list[dict], bool]] = []

    async def chat(
        self,
        messages: list[dict],
        *,
        json_mode: bool = True,
    ) -> str:
        self.calls.append((messages, json_mode))
        return self.response


class ResponseEngineTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_current_message_is_sent_as_last_user_message(self) -> None:
        original_llm = response_engine.llm
        fake_llm = FakeLLM()
        response_engine.llm = fake_llm
        try:
            response = await response_engine.generate_answer(
                "mensagem atual",
                context=[
                    {
                        "user": "mensagem anterior",
                        "jarbas": "resposta anterior",
                    }
                ],
            )
        finally:
            response_engine.llm = original_llm

        messages, json_mode = fake_llm.calls[0]
        self.assertEqual(response, "resposta atual")
        self.assertEqual(
            messages[-1],
            {"role": "user", "content": "mensagem atual"},
        )
        self.assertFalse(json_mode)


class ContextScopeTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database_connection.DATABASE_PATH
        database_connection.DATABASE_PATH = (
            Path(self.temporary_directory.name) / "jarbas.db"
        )
        await short_term.init_context()

    async def asyncTearDown(self) -> None:
        database_connection.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    async def test_context_is_isolated_and_trimmed_per_client(self) -> None:
        for number in range(4):
            await short_term.add_context(
                f"a-{number}",
                f"resposta-a-{number}",
                scope="cliente-a",
            )
        await short_term.add_context(
            "b-0",
            "resposta-b-0",
            scope="cliente-b",
        )

        context_a = await short_term.get_context(scope="cliente-a")
        context_b = await short_term.get_context(scope="cliente-b")

        self.assertEqual(
            [item["user"] for item in context_a],
            ["a-1", "a-2", "a-3"],
        )
        self.assertEqual(
            context_b,
            [{"user": "b-0", "jarbas": "resposta-b-0"}],
        )


class ThinkingFastPathTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_conversation_does_not_call_llm_without_tools(self) -> None:
        original_list_tools = thinking_engine.admin_repository.list_tools

        async def no_tools(*, enabled_only: bool = False):
            return []

        thinking_engine.admin_repository.list_tools = no_tools
        try:
            intent = await thinking_engine.think("oi")
        finally:
            thinking_engine.admin_repository.list_tools = original_list_tools

        self.assertEqual(intent.name, "conversation")
        self.assertEqual(intent.action, "answer")


if __name__ == "__main__":
    unittest.main()
