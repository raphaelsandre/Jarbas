from .models import ExecutionResult
from .registry import HandlerRegistry
from .handlers.unknown import UnknownIntentHandler
from app.thinking.models import Intent


class Orchestrator:
    def __init__(
        self,
        registry: HandlerRegistry,
    ):
        self.registry = registry
        self.unknown_handler = UnknownIntentHandler()

    intent = Intent

    async def execute(
        self,
        intent: Intent,
    ) -> ExecutionResult:

        handler = self.registry.get(intent.name)

        if handler is None:
            handler = self.unknown_handler

        try:
            return await handler.handle(intent)

        except Exception as exc:
            return ExecutionResult(
                success=False,
                handler=handler.__class__.__name__,
                intent=intent.name,
                action=intent.action,
                error=str(exc),
                response_hint="execution_error",
            )
