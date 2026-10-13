from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ..schemas.book import (
    BookCreate,
    BookUpdate,
    ShowBook,
    BookFilters
)
from ..schemas.common import PaginationResponse, PaginationParams
from ...dependencies import BookServiceDep

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("/",
             response_model=ShowBook,
             status_code=status.HTTP_201_CREATED,
             summary="Создать книгу",
             description="создать новую книгу в каталоге с автоматическим обогащением из Open Library"
)
async def create_book(
        book_data: BookCreate,
        service: BookServiceDep,
):
    return await service.create_book(book_data)

@router.get(
    "/",
    response_model=PaginationResponse[ShowBook],
    summary="Получить список книг",
    description="Получить список книг с фильтрацией и пагинацией",
)
async def get_books(
        service: BookServiceDep,
        pagination: Annotated[PaginationParams, Depends()],
        title: str | None = Query(None, description="Поиск по названию"),
        author: str | None = Query(None, description="Поиск по автору"),
        genre: str | None = Query(None, description="Фильтр по жанру"),
        year: int | None = Query(None, description="Фильтр по году"),
        available: bool | None = Query(None, description="Фильтр по доступности"),
):

    books, total = await service.search_book(
        title=title,
        author=author,
        genre=genre,
        year=year,
        available=available,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return PaginationResponse.create(books, total, pagination)

@router.get(
    "/{book_id}",
    response_model=ShowBook,
    summary="Получить книгу",
    description="Получить информацию о конкретной книге по ID"
)
async def get_book(
        book_id: UUID,
        service: BookServiceDep,
):
    return await service.get_book(book_id)

@router.patch(
    "/{book_id}",
    response_model=ShowBook,
    summary="Обновить книгу",
    description="Частичное обновление книги (передаются только изменяемые поля)",
)
async def update_book(
        book_id: UUID,
        book_data: BookUpdate,
        service: BookServiceDep,
):

    return await service.update_book(book_id, book_data)

@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу из катлога",
)
async def delete_book(
        book_id: UUID,
        service: BookServiceDep,
):
    await service.delete_book(book_id)