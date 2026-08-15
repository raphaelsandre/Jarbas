from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.context.short_term import init_context
from app.interactions.service import interaction_repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    await interaction_repository.initialize()
    await init_context()
    yield


app = FastAPI(
    title=settings.jarbas_name,
    version=settings.jarbas_version,
    lifespan=lifespan,
)

app.include_router(api_router)
