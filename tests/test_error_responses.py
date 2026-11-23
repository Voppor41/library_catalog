import httpx
import pytest

from library_catalog.main import app


@pytest.mark.asyncio
async def test_request_id_is_preserved_in_response() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/", headers={"X-Request-ID": "request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"


@pytest.mark.asyncio
async def test_validation_error_has_common_format_without_input() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "x",
                "email": "invalid",
                "password": "secret",
            },
        )

    detail = response.json()["detail"]
    assert response.status_code == 422
    assert detail["code"] == "VALIDATION_ERROR"
    assert detail["request_id"] == response.headers["X-Request-ID"]
    assert detail["errors"]
    assert "secret" not in response.text
