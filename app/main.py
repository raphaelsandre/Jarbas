import asyncio
import sys
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.admin.service import initialize_admin
from app.api.router import api_router
from app.config import settings
from app.context.short_term import init_context
from app.handle.orchestrator import reload_registered_tools
from app.interactions.service import interaction_repository
from app.realtime.piesocket import piesocket_bridge


@asynccontextmanager
async def lifespan(app: FastAPI):
    await interaction_repository.initialize()
    await init_context()
    await initialize_admin()
    await reload_registered_tools()

    bridge_task = None
    running_tests = "pytest" in sys.modules or "unittest" in sys.modules
    if settings.piesocket_enabled and not running_tests:
        bridge_task = asyncio.create_task(piesocket_bridge.run())

    try:
        yield
    finally:
        if bridge_task is not None:
            await piesocket_bridge.stop()
            bridge_task.cancel()
            with suppress(asyncio.CancelledError):
                await bridge_task


app = FastAPI(
    title=settings.jarbas_name,
    version=settings.jarbas_version,
    lifespan=lifespan,
)

app.include_router(api_router)

pwa_dist = Path(settings.pwa_dist_dir)
if pwa_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(pwa_dist), html=True), name="pwa")
