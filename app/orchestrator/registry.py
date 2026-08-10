from .handlers.base import IntentHandler


class HandlerRegistry:
    def __init__(self):
        self._handlers: dict[str, IntentHandler] = {}

    def register(
        self,
        intent_name: str,
        handler: IntentHandler,
    ) -> None:

        self._handlers[intent_name] = handler

    def get(
        self,
        intent_name: str,
    ) -> IntentHandler | None:

        return self._handlers.get(intent_name)
