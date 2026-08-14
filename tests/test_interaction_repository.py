import asyncio
from datetime import datetime, UTC
from uuid import uuid4

from app.gateway.models import GatewayInput
from app.interactions.models import InteractionStatus, Interaction
from app.interactions.repository import InteractionRepository
async def main() -> None:
    repository = InteractionRepository()

    await repository.initialize()

    interaction = Interaction(
        id=uuid4(),
        status=InteractionStatus.PENDING,
        input=GatewayInput(
            text="teste de interaction",
        ),
        created_at=datetime.now(UTC),
    )

    await repository.create(interaction)

    saved_interaction = await repository.get(
        interaction.id,
    )

    print("ORIGINAL:")
    print(interaction.model_dump())

    print("\nBANCO:")
    print(
        saved_interaction.model_dump()
        if saved_interaction
        else None
    )


asyncio.run(main())