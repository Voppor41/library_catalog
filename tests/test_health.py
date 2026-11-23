from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import Response, status
from sqlalchemy.exc import SQLAlchemyError

from library_catalog.api.v1.routers import health


@pytest.mark.asyncio
async def test_liveness_does_not_check_dependencies() -> None:
    result = await health.liveness()

    assert result.status == "healthy"


@pytest.mark.asyncio
async def test_readiness_is_healthy_when_dependencies_are_connected(
    monkeypatch,
) -> None:
    database = SimpleNamespace(execute=AsyncMock())
    monkeypatch.setattr(health, "redis_health", AsyncMock(return_value="connected"))
    response = Response()

    result = await health.readiness(database, response)

    assert result.status == "healthy"
    assert result.database == "connected"
    assert result.redis == "connected"
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_readiness_is_degraded_when_redis_is_disconnected(
    monkeypatch,
) -> None:
    database = SimpleNamespace(execute=AsyncMock())
    monkeypatch.setattr(
        health,
        "redis_health",
        AsyncMock(return_value="disconnected"),
    )
    response = Response()

    result = await health.readiness(database, response)

    assert result.status == "degraded"
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_readiness_returns_503_when_database_is_disconnected(
    monkeypatch,
) -> None:
    database = SimpleNamespace(
        execute=AsyncMock(side_effect=SQLAlchemyError("offline")),
    )
    monkeypatch.setattr(health, "redis_health", AsyncMock(return_value="connected"))
    response = Response()

    result = await health.readiness(database, response)

    assert result.status == "unhealthy"
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
