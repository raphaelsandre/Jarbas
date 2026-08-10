from .base import IntentHandler
from ..models import ExecutionResult
from app.thinking.models import Intent


class UnknownIntentHandler(IntentHandler):
    async def handle(
        self,
        intent: Intent,
    ) -> ExecutionResult:

        return ExecutionResult(
            success=False,
            handler=self.__class__.__name__,
            intent=intent.name,
            error=f"Unsupported intent: {intent.name}",
            response_hint="unsupported_intent",
        )
