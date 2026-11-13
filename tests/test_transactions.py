from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from library_catalog.api.v1.schemas.book import BookCreate
from library_catalog.api.v1.schemas.user import UserCreate
from library_catalog.data.repositories.base_repository import BaseRepository
from library_catalog.domain.exceptions import (
    BookAlreadyExistsException,
    UserAlreadyExistsException,
)
from library_catalog.domain.services.book_service import BookService
from library_catalog.domain.services.user_service import UserService


class Record:
    def __init__(self, **values):
        self.__dict__.update(values)


def make_session():
    return SimpleNamespace(
        add=Mock(),
        flush=AsyncMock(),
        refresh=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )


def make_book():
    now = datetime.now(UTC)
    return SimpleNamespace(
        book_id=uuid4(),
        title="Clean Code",
        author="Robert C. Martin",
        year=2008,
        genre="Programming",
        pages=464,
        available=True,
        isbn="9780132350884",
        description=None,
        extra=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_repository_create_flushes_without_committing() -> None:
    session = make_session()
    repository = BaseRepository(session, Record)

    result = await repository.create(value="created")

    assert result.value == "created"
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(result)
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_book_service_commits_successful_create() -> None:
    repository = SimpleNamespace(
        find_by_isbn=AsyncMock(return_value=None),
        create=AsyncMock(return_value=make_book()),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    client = SimpleNamespace(enrich=AsyncMock(return_value={}))
    service = BookService(repository, client)
    service._invalidate_search_cache = AsyncMock()

    await service.create_book(
        BookCreate(
            title="Clean Code",
            author="Robert C. Martin",
            year=2008,
            genre="Programming",
            pages=464,
            isbn="9780132350884",
        )
    )

    repository.commit.assert_awaited_once()
    repository.rollback.assert_not_awaited()
    service._invalidate_search_cache.assert_awaited_once()


@pytest.mark.asyncio
async def test_book_service_rolls_back_duplicate_isbn() -> None:
    error = IntegrityError("insert", {}, Exception("duplicate"))
    repository = SimpleNamespace(
        find_by_isbn=AsyncMock(return_value=None),
        create=AsyncMock(side_effect=error),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    client = SimpleNamespace(enrich=AsyncMock(return_value={}))
    service = BookService(repository, client)
    service._invalidate_search_cache = AsyncMock()

    with pytest.raises(BookAlreadyExistsException):
        await service.create_book(
            BookCreate(
                title="Clean Code",
                author="Robert C. Martin",
                year=2008,
                genre="Programming",
                pages=464,
                isbn="9780132350884",
            )
        )

    repository.rollback.assert_awaited_once()
    repository.commit.assert_not_awaited()
    service._invalidate_search_cache.assert_not_awaited()


@pytest.mark.asyncio
async def test_user_service_rolls_back_concurrent_username_conflict(
    monkeypatch,
) -> None:
    error = IntegrityError("insert", {}, Exception("duplicate"))
    repository = SimpleNamespace(
        get_by_username=AsyncMock(side_effect=[None, object()]),
        get_by_email=AsyncMock(return_value=None),
        create=AsyncMock(side_effect=error),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    service = UserService(repository)
    monkeypatch.setattr(
        "library_catalog.domain.services.user_service.hash_password",
        lambda password: "hashed",
    )

    with pytest.raises(UserAlreadyExistsException):
        await service.create_user(
            UserCreate(
                username="reader",
                email="reader@example.com",
                password="password123",
            )
        )

    repository.rollback.assert_awaited_once()
    repository.commit.assert_not_awaited()
