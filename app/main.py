from fastapi import FastAPI
from app.api.router import api_router
from .config import settings

app = FastAPI(
    title=settings.jarbas_name,
    version=settings.jarbas_version,
)

app.include_router(api_router)

