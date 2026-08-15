import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.gateway.models import GatewayInput, GatewayResult
from app.interactions.exceptions import (
    InteractionAlreadyFinishedError,
    InteractionNotFoundError,
    InvalidInteractionTransitionError,
)
from app.interactions.models import Interaction, InteractionStatus
from app.interactions.repository import InteractionRepository

GatewayProcessor = Callable[[GatewayInput], Awaitable[GatewayResult]]
logger = logging.getLogger(__name__)


class InteractionService:
    _FINISHED_STATUSES = {
        InteractionStatus.COMPLETED,
        InteractionStatus.FAILED,
        InteractionStatus.ABORTED,
    }
    _ALLOWED_TRANSITIONS = {
        InteractionStatus.PENDING: {
            InteractionStatus.RUNNING,
            InteractionStatus.FAILED,
        },
        InteractionStatus.RUNNING: {
            InteractionStatus.AWAITING_DELIVERY,
            InteractionStatus.FAILED,
        },
        InteractionStatus.AWAITING_DELIVERY: {
            InteractionStatus.COMPLETED,
            InteractionStatus.FAILED,
        },
    }

    def __init__(
        self,
        repository: InteractionRepository,
    ) -> None:
        self.repository = repository

    async def execute(
        self,
        gateway_input: GatewayInput,
        processor: GatewayProcessor,
    ) -> tuple[Interaction, GatewayResult]:
        interaction = await self.create(gateway_input)
        await self.mark_running(interaction.id)
        try:
            result = await processor(gateway_input)
        except Exception as error:
            await self.mark_failed_safely(interaction.id, str(error))
            raise
        interaction = await self.mark_awaiting_delivery(
            interaction.id,
            result,
        )
        return interaction, result

    async def create(self, gateway_input: GatewayInput) -> Interaction:
        interaction = Interaction(
            id=uuid4(),
            status=InteractionStatus.PENDING,
            input=gateway_input,
            created_at=datetime.now(UTC),
        )
        await self.repository.create(interaction)
        return interaction

    async def mark_running(self, interaction_id: UUID) -> Interaction:
        return await self._transition(
            interaction_id,
            InteractionStatus.RUNNING,
            started_at=datetime.now(UTC),
        )

    async def mark_awaiting_delivery(
        self,
        interaction_id: UUID,
        result: GatewayResult,
    ) -> Interaction:
        return await self._transition(
            interaction_id,
            InteractionStatus.AWAITING_DELIVERY,
            result=result,
        )

    async def mark_completed(self, interaction_id: UUID) -> Interaction:
        delivered_at = datetime.now(UTC)
        return await self._transition(
            interaction_id,
            InteractionStatus.COMPLETED,
            completed_at=delivered_at,
            delivered_at=delivered_at,
        )

    async def mark_failed(
        self,
        interaction_id: UUID,
        error: str,
    ) -> Interaction:
        return await self._transition(
            interaction_id,
            InteractionStatus.FAILED,
            error=error,
            failed_at=datetime.now(UTC),
        )

    async def mark_failed_safely(
        self,
        interaction_id: UUID,
        error: str,
    ) -> None:
        try:
            await self.mark_failed(interaction_id, error)
        except Exception:
            logger.exception(
                "Could not mark interaction %s as failed",
                interaction_id,
            )

    async def mark_completed_safely(
        self,
        interaction_id: UUID,
    ) -> None:
        try:
            await self.mark_completed(interaction_id)
        except Exception:
            logger.exception(
                "Could not mark interaction %s as completed",
                interaction_id,
            )

    async def get_awaiting_delivery(self) -> list[Interaction]:
        return await self.repository.list_by_status(
            InteractionStatus.AWAITING_DELIVERY,
        )

    async def _transition(
        self,
        interaction_id: UUID,
        target_status: InteractionStatus,
        **updates: object,
    ) -> Interaction:
        interaction = await self.repository.get(interaction_id)
        if interaction is None:
            raise InteractionNotFoundError(interaction_id)
        if interaction.status in self._FINISHED_STATUSES:
            raise InteractionAlreadyFinishedError(interaction_id)
        allowed_statuses = self._ALLOWED_TRANSITIONS.get(
            interaction.status,
            set(),
        )
        if target_status not in allowed_statuses:
            raise InvalidInteractionTransitionError(
                interaction.status.value,
                target_status.value,
            )

        updated_interaction = interaction.model_copy(
            update={"status": target_status, **updates},
        )
        if not await self.repository.update(updated_interaction):
            raise InteractionNotFoundError(interaction_id)
        return updated_interaction


interaction_repository = InteractionRepository()
interaction_service = InteractionService(interaction_repository)
