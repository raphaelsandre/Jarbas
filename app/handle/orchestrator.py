from app.admin.repository import admin_repository
from app.admin.service import validate_tool_endpoint
from app.admin.webhook import WebhookToolHandler
from app.orchestrator.handlers.conversation import ConversationHandler
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.registry import HandlerRegistry


def create_orchestrator() -> Orchestrator:
    registry = HandlerRegistry()
    registry.register("conversation", ConversationHandler())
    return Orchestrator(registry=registry)


orchestrator = create_orchestrator()
_registered_tool_names: set[str] = set()


async def reload_registered_tools() -> None:
    global _registered_tool_names
    for name in _registered_tool_names:
        orchestrator.registry.unregister(name)

    loaded: set[str] = set()
    for tool in await admin_repository.list_tools(enabled_only=True):
        try:
            validate_tool_endpoint(tool.endpoint)
        except ValueError:
            continue
        orchestrator.registry.register(tool.name, WebhookToolHandler(tool))
        loaded.add(tool.name)
    _registered_tool_names = loaded
