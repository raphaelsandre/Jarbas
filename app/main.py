from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.router import api_router
from .config import settings
from app.context.short_term import init_context

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_context()
    yield
app = FastAPI(
    title=settings.jarbas_name,
    version=settings.jarbas_version,
    lifespan=lifespan,
)

app.include_router(api_router)

