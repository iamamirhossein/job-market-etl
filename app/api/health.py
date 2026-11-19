from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from starlette import status

from app.api.deps import get_lake
from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse, ReadinessResponse
from pipeline.lake.client import LakeClient

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )


@router.get("/health/ready")
def ready(
    response: Response, lake_client: Annotated[LakeClient, Depends(get_lake)]
) -> ReadinessResponse:
    checks = {"lake": lake_client.is_reachable()}
    is_ready = all(checks.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        checks=checks,
    )
