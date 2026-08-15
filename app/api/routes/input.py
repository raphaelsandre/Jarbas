from fastapi import APIRouter, Request
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse

from app.gateway.parser import parse_input
from app.gateway.service import process_gateway_input
from app.interactions.service import interaction_service

router = APIRouter(
    prefix="/input",
    tags=["gateway"],
)


@router.post("")
async def input_gateway(request: Request) -> JSONResponse:
    gateway_input = await parse_input(request)
    interaction, result = await interaction_service.execute(
        gateway_input,
        process_gateway_input,
    )
    return JSONResponse(
        content=result.model_dump(mode="json"),
        background=BackgroundTask(
            interaction_service.mark_completed_safely,
            interaction.id,
        ),
    )
