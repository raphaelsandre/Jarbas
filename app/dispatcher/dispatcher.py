from unittest import result

from .models.tool_request import ToolRequest
from .models.tool_response import ToolResponse
from .registry.tool_registry import ToolRegistry

class Dispatcher:
    """
    Responsavel por localizar e executar ferramentas
    """
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    async def dispatch(
            self,
            request: ToolRequest,
        ) -> ToolResponse:
        tool = self.registry.get(request.tool)
        if tool is None:
            return ToolResponse(
                success=False,
                error=f"Ferramenta '{request.tool}' não foi encontrada"
            )
        try:
            result = await tool.execute(
                request.payload
            )
            return ToolResponse(
                success=True,
                data=result.output
            )
        except Exception as exc:
            return ToolResponse(
                success=False,
                error=str(exc)
            )
