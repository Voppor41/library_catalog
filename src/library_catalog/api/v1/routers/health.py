from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ....core.redis_config import redis_health
from ...dependencies import DbSessionDep
from ..schemas.common import HealthCheckResponse, LivenessResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", response_model=LivenessResponse)
async def liveness():
    return LivenessResponse(status="healthy")


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Проверить состояние сервиса и подключение к БД",
)
async def readiness(db: DbSessionDep, response: Response):

    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except SQLAlchemyError:
        db_status = "disconnected"

    redis_status = await redis_health()

    if db_status == "disconnected":
        service_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif redis_status == "disconnected":
        service_status = "degraded"
    else:
        service_status = "healthy"

    return HealthCheckResponse(
        status=service_status,
        database=db_status,
        redis=redis_status,
    )
