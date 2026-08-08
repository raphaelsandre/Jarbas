from fastapi import FastAPI
from .config import settings
from app.api.router import api_router
app = FastAPI(
    title=settings.jarbas_name,
    version=settings.jarbas_version,
)

app.include_router(api_router)