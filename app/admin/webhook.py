from dataclasses import asdict

import httpx

from app.admin.models import ToolDefinition
from app.orchestrator.handlers.base import IntentHandler
from app.orchestrator.models import ExecutionResult
from app.thinking.models import Intent


class WebhookToolHandler(IntentHandler):
    def __init__(self, tool: ToolDefinition) -> None:
        self.tool = tool

    async def handle(self, intent: Intent) -> ExecutionResult:
        async with httpx.AsyncClient(timeout=self.tool.timeout_seconds) as client:
            response = await client.request(
                self.tool.method,
                self.tool.endpoint,
                json={"intent": asdict(intent)},
            )
            response.raise_for_status()

        try:
            payload = response.json()
        except ValueError:
            payload = {"response": response.text}
        if not isinstance(payload, dict):
            payload = {"value": payload}

        return ExecutionResult(
            success=True,
            handler=f"WebhookTool:{self.tool.name}",
            intent=intent.name,
            action=intent.action,
            data=payload,
            response_hint="tool_response",
        )
