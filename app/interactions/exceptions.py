from uuid import UUID


class InteractionError(Exception):
    """Base para erros do domínio de interactions."""


class InteractionNotFoundError(InteractionError):
    def __init__(self, interaction_id: UUID) -> None:
        super().__init__(
            f"Interaction '{interaction_id}' not found"
        )


class InvalidInteractionTransitionError(InteractionError):
    def __init__(
        self,
        current_status: str,
        target_status: str,
    ) -> None:
        super().__init__(
            f"Invalid interaction transition: "
            f"{current_status} -> {target_status}"
        )


class InteractionAlreadyFinishedError(InteractionError):
    def __init__(self, interaction_id: UUID) -> None:
        super().__init__(
            f"Interaction '{interaction_id}' is already finished"
        )
