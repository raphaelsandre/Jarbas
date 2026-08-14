from uuid import UUID

from app.database.connection import get_database_connection
from app.gateway.models import GatewayInput, GatewayResult
from app.interactions.models import Interaction, InteractionStatus


class InteractionRepository:

    async def initialize(self) -> None:
        async with get_database_connection() as connection:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions
                (
                    id
                    TEXT
                    PRIMARY
                    KEY,
                    status
                    TEXT
                    NOT
                    NULL,

                    input
                    TEXT
                    NOT
                    NULL,
                    result
                    TEXT,
                    error
                    TEXT,

                    created_at
                    TEXT
                    NOT
                    NULL,
                    started_at
                    TEXT,
                    completed_at
                    TEXT,
                    failed_at
                    TEXT,
                    aborted_at
                    TEXT,
                    delivered_at
                    TEXT
                )
                """
            )

    async def create(
                    self,
                    interaction: Interaction,
    ) -> None:
                async with get_database_connection() as connection:
                    await connection.execute(
                        """
                        INSERT INTO interactions (id,
                                                  status,
                                                  input,
                                                  result,
                                                  error,
                                                  created_at,
                                                  started_at,
                                                  completed_at,
                                                  failed_at,
                                                  aborted_at,
                                                  delivered_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(interaction.id),
                            interaction.status.value,
                            interaction.input.model_dump_json(),
                            (
                                interaction.result.model_dump_json()
                                if interaction.result is not None
                                else None
                            ),
                            interaction.error,
                            interaction.created_at.isoformat(),
                            (
                                interaction.started_at.isoformat()
                                if interaction.started_at is not None
                                else None
                            ),
                            (
                                interaction.completed_at.isoformat()
                                if interaction.completed_at is not None
                                else None
                            ),
                            (
                                interaction.failed_at.isoformat()
                                if interaction.failed_at is not None
                                else None
                            ),
                            (
                                interaction.aborted_at.isoformat()
                                if interaction.aborted_at is not None
                                else None
                            ),
                            (
                                interaction.delivered_at.isoformat()
                                if interaction.delivered_at is not None
                                else None
                            ),
                        ),
                    )

    async def get(
                        self,
                        interaction_id: UUID,
    ) -> Interaction | None:
                async with get_database_connection() as connection:
                        cursor = await connection.execute(
                            """
                            SELECT *
                            FROM interactions
                            WHERE id = ?
                            """,
                            (str(interaction_id),), )
                        row = await cursor.fetchone()
                        if row is None:
                            return None
                        return Interaction(
                            id=UUID(row["id"]),
                            status=InteractionStatus(row["status"]),
                            input=GatewayInput.model_validate_json(row["input"]),
                            result=(
                                GatewayResult.model_validate_json(row["result"])
                                if row["result"] is not None
                                else None
                            ),
                            error=row["error"],
                            created_at=row["created_at"],
                            started_at=row["started_at"],
                            completed_at=row["completed_at"],
                            failed_at=row["failed_at"],
                            aborted_at=row["aborted_at"],
                            delivered_at=row["delivered_at"],
                        )
