from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.common import HealthCheckResponse
from ...dependencies import DbSessionDep

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Проверить состояние сервиса и подключение к БД",
)
async def health_check(db: DbSessionDep):

    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthCheckResponse(
        status="healthy",
        data=db_status,
    )