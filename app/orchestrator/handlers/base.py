from abc import ABC, abstractmethod

from ..models import ExecutionResult
from app.thinking.models import Intent


class IntentHandler(ABC):
    @abstractmethod
    async def handle(
        self,
        intent: Intent,
    ) -> ExecutionResult: ...
