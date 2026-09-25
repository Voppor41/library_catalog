from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from ..models.book import Book



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
        stmt = select(Book)

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
            limit: int = 20,
            offset: int = 0,
    ) -> int:
        stmt = select(func.count()).select_from(Book)

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

        total = await self.session.scalar(stmt)
        return int(total or 0)