import pytest
from pydantic import ValidationError

from library_catalog.api.v1.schemas.common import (
    HealthCheckResponse,
    PaginationParams,
    PaginationResponse,
)


def test_pagination_params_calculate_limit_and_offset() -> None:
    pagination = PaginationParams(page=3, page_size=25)

    assert pagination.limit == 25
    assert pagination.offset == 50


def test_pagination_response_calculates_page_count() -> None:
    pagination = PaginationParams(page=2, page_size=20)

    response = PaginationResponse[str].create(
        items=["book"],
        total=41,
        pagination=pagination,
    )

    assert response.items == ["book"]
    assert response.page == 2
    assert response.pages == 3


def test_health_response_uses_database_field() -> None:
    response = HealthCheckResponse(status="healthy", database="connected")

    assert response.database == "connected"

    with pytest.raises(ValidationError):
        HealthCheckResponse(status="healthy", data="connected")
