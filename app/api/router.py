from fastapi import APIRouter
from app.gateway.routes.websocket import router as websocket_router
from app.api.routes import health, info, input


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(info.router)
api_router.include_router(input.router)
api_router.include_router(websocket_router)