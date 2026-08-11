from abc import ABC, abstractmethod
from app.dispatcher.models.tool_result import ToolResult

class BaseTool(ABC):
    """
    Classe base para tudo
    """

    name: str
    description: str

    @abstractmethod

    async def execute(self, payload: dict) -> ToolResult:
        """
        executa a ferramenta. Toda ferramenta deve implementar esse metodo!!
        :param payload:
        :return:
        """
        pass
