from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.dialects import postgresql

from library_catalog.data.repositories.book_repository import BookRepository


def compile_query(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


@pytest.mark.asyncio
async def test_find_by_filters_has_stable_order_and_pagination() -> None:
    result = SimpleNamespace(all=list)
    session = SimpleNamespace(scalars=AsyncMock(return_value=result))
    repository = BookRepository(session)

    await repository.find_by_filters(title="Clean", limit=10, offset=20)

    query = compile_query(session.scalars.await_args.args[0])
    assert "WHERE books.title ILIKE '%%Clean%%'" in query
    assert "ORDER BY books.created_at DESC, books.book_id ASC" in query
    assert "LIMIT 10 OFFSET 20" in query


@pytest.mark.asyncio
async def test_count_uses_same_filters_without_pagination() -> None:
    session = SimpleNamespace(scalar=AsyncMock(return_value=2))
    repository = BookRepository(session)

    total = await repository.count_by_filters(
        author="Martin",
        available=True,
    )

    query = compile_query(session.scalar.await_args.args[0])
    assert "books.author ILIKE '%%Martin%%'" in query
    assert "books.available = true" in query
    assert "LIMIT" not in query
    assert "OFFSET" not in query
    assert total == 2
