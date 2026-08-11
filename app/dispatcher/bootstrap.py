from .dispatcher import Dispatcher
from .registry.tool_registry import ToolRegistry
from .tools.mock import MockTool

def create_dispatcher() -> Dispatcher:
    registry = ToolRegistry()
    registry.register(
        MockTool()
    )
    return Dispatcher(
        registry=registry,
    )