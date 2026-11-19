import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from pipeline.lake.client import LakeClient, LakeError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info(
        "APP Started %s v%s (%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    lake = LakeClient(
        endpoint_url=settings.lake_endpoint_url,
        access_key=settings.lake_access_key,
        secret_key=settings.lake_secret_key.get_secret_value(),
        bucket=settings.lake_bucket,
    )
    try:
        await asyncio.to_thread(lake.ensure_bucket)
    except LakeError:
        logger.warning("Lake is not available in startup", exc_info=True)

    app.state.lake_client = lake
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(health_router)
    return app


app = create_app()
