from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.gateway.models import GatewayInput, GatewayResult

class InteractionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    AWAITING_DELIVERY = "awaiting_delivery"
    RUNNING = "running"

class Interaction(BaseModel):
    id: UUID
    status: InteractionStatus

    input: GatewayInput | None = None
    result: GatewayResult | None = None
    error: str | None = None
    started_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    aborted_at: datetime | None = None
    delivered_at: datetime | None = None

