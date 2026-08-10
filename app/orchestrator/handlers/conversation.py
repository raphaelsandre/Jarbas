from .base import IntentHandler
from ..models import ExecutionResult
from app.thinking.models import Intent


class ConversationHandler(IntentHandler):
    async def handle(
        self,
        intent: Intent,
    ) -> ExecutionResult:

        query = intent.entities.get("query")

        return ExecutionResult(
            success=True,
            handler=self.__class__.__name__,
            action=intent.action,
            intent=intent.name,
            data={
                "query": query,
            },
            response_hint="generate_answer",
        )
