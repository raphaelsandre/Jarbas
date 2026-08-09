from fastapi import APIRouter

from app.api.routes import health, info, voice, input


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(info.router)
api_router.include_router(voice.router)
api_router.include_router(input.router)