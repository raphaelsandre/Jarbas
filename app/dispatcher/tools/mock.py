from app.dispatcher.models.tool_result import ToolResult
from app.dispatcher.tools.base import BaseTool

class MockTool(BaseTool):
    """
    Ferramenta falsa para validação e teste do dispatcher
    """

    name = "mock"
    description = "Ferramenta para teste e validação do dispatcher"

    async def execute(self, payload: dict) -> ToolResult:
        return ToolResult(
            output={
                "message": "Ferramenta de testes executada com sucesso",
                "payload_received": payload
            },
            metadata={
                "tool": self.name
            }
        )