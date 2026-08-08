from fastapi import APIRouter
from app.config import settings
router = APIRouter(
    prefix="/info",
    tags=["Info"]
)

@router.get("/")
async def info():
    return {
        "name": settings.jarbas_name,
        "version": settings.jarbas_version,
        "environment": settings.environment
    }