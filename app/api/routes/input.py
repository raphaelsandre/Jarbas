# from app.gateway.service import process_gateway_request
from fastapi import Request, APIRouter, Depends
from app.security.auth import authenticate_request
from app.gateway.service import process_gateway_request

router = APIRouter(
    prefix="/input",
    tags=["gateway"],
    # dependencies=[
    #   Depends(authenticate_request),
    # ],
)


@router.post("")
async def input_gateway(request: Request):
    return await process_gateway_request(request)