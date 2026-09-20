from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes import core, health, plugins, quantpulse, quantpulse_paper, quantpulse_provider, quantpulse_stream
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import initialize_database
from app.services.upstox_market_poller import UpstoxMarketPoller
from app.services.upstox_websocket import UpstoxWebsocketFeed

market_poller = UpstoxMarketPoller()
market_websocket = UpstoxWebsocketFeed()

configure_logging(settings.log_level)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await initialize_database()
    await market_websocket.start()
    try:
        yield
    finally:
        await market_websocket.stop()

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
register_exception_handlers(app)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(plugins.router, prefix=settings.api_prefix)
app.include_router(core.router, prefix=settings.api_prefix)
app.include_router(quantpulse.router, prefix=settings.api_prefix)
app.include_router(quantpulse_paper.router, prefix=settings.api_prefix)
app.include_router(quantpulse_provider.router, prefix=settings.api_prefix)
app.include_router(quantpulse_stream.router, prefix=settings.api_prefix)
