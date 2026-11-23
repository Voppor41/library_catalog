from typing import Literal

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):

    page: int = Field(1, ge=1, description="Номер страницы")
    page_size: int = Field(20, ge=1, le=100, description="Размер страницы")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginationResponse[T](BaseModel):
    items: list[T]
    total: int = Field(..., description="Всего элементов")
    page: int = Field(..., description="Текущая страница")
    page_size: int = Field(..., description="Размер страницы")
    pages: int = Field(..., description="Всего страниц")

    @classmethod
    def create(
            cls,
            items: list[T],
            total: int,
            pagination: PaginationParams,
    ):

        pages = (total + pagination.page_size - 1) // pagination.page_size

        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )


class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    database: Literal["connected", "disconnected"]
    redis: Literal["connected", "disconnected"]


class LivenessResponse(BaseModel):
    status: Literal["healthy"]
