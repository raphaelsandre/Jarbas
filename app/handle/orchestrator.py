from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.registry import HandlerRegistry
from app.orchestrator.handlers.conversation import ConversationHandler


def create_orchestrator() -> Orchestrator:
    registry = HandlerRegistry()
    registry.register(
        "conversation",
        ConversationHandler(),
    )
    return Orchestrator(registry=registry)
