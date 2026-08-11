from abc import ABC, abstractmethod
from typing import Any

class Tool(ABC):
    """
    Contrato base para ferramenta dispatcher
    """
    name: str
    description: str

    @abstractmethod
    async def execute(self, payload: dict[str, Any]) -> Any:
        """
        Executa ferramenta
        """
        pass
