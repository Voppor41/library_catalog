from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from ..models.book import Book
from .base_repository import BaseRepository


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)

    async def find_by_filters(
            self,
            title: str | None = None,
            author: str | None = None,
            genre: str | None = None,
            year: int | None = None,
            available: bool | None = None,
            limit: int = 20,
            offset: int = 0,
    ) -> list[Book]:
        stmt = self._apply_filters(
            select(Book),
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )
        stmt = stmt.order_by(Book.created_at.desc(), Book.book_id.asc())
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def find_by_isbn(self, isbn: str) -> Book | None:
        stmt = select(Book).where(Book.isbn == isbn)
        result = await self.session.scalar(stmt)
        return result

    async def count_by_filters(
            self,
            title: str | None = None,
            author: str | None = None,
            genre: str | None = None,
            year: int | None = None,
            available: bool | None = None,
    ) -> int:
        stmt = self._apply_filters(
            select(func.count()).select_from(Book),
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )

        total = await self.session.scalar(stmt)
        return int(total or 0)

    def _apply_filters(
            self,
            stmt: Select[Any],
            title: str | None = None,
            author: str | None = None,
            genre: str | None = None,
            year: int | None = None,
            available: bool | None = None,
    ) -> Select[Any]:
        if title is not None:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))
        if author is not None:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))
        if genre is not None:
            stmt = stmt.where(Book.genre == genre)
        if year is not None:
            stmt = stmt.where(Book.year == year)
        if available is not None:
            stmt = stmt.where(Book.available == available)

        return stmt
