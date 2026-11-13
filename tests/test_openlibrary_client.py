from unittest.mock import AsyncMock

import httpx
import pytest

from library_catalog.core.cache import cache_service
from library_catalog.core.config import settings
from library_catalog.domain.exceptions import (
    OpenLibraryException,
    OpenLibraryTimeoutException,
)
from library_catalog.external.openlibrary.client import OpenLibraryClient


def make_response():
    return {
        "numFound": 1,
        "docs": [
            {
                "title": "Clean Code",
                "cover_i": 123,
                "subject": ["Programming", "Design"],
                "publisher": ["Prentice Hall"],
                "language": ["eng"],
                "ratings_average": 4.5,
            }
        ],
    }


def test_base_client_builds_url_for_relative_path() -> None:
    client = OpenLibraryClient(base_url="https://openlibrary.org")

    assert client._build_url("search.json") == "https://openlibrary.org/search.json"


@pytest.mark.asyncio
async def test_search_uses_cached_result(monkeypatch) -> None:
    client = OpenLibraryClient()
    cached = {"publisher": "Cached"}
    monkeypatch.setattr(cache_service, "get", AsyncMock(return_value=cached))
    monkeypatch.setattr(client, "_get", AsyncMock())

    result = await client.search_by_isbn("9780132350884")

    assert result == cached
    client._get.assert_not_awaited()
    await client.close()


@pytest.mark.asyncio
async def test_search_validates_and_caches_result(monkeypatch) -> None:
    client = OpenLibraryClient()
    monkeypatch.setattr(cache_service, "get", AsyncMock(return_value=None))
    cache_set = AsyncMock()
    monkeypatch.setattr(cache_service, "set", cache_set)
    monkeypatch.setattr(client, "_get", AsyncMock(return_value=make_response()))

    result = await client.search_by_isbn("9780132350884")

    assert result == {
        "cover_url": "https://covers.openlibrary.org/b/id/123-L.jpg",
        "subjects": ["Programming", "Design"],
        "publisher": "Prentice Hall",
        "language": "eng",
        "rating": 4.5,
    }
    cache_set.assert_awaited_once()
    assert cache_set.await_args.args[2] == settings.cache_ttl_openlibrary
    await client.close()


@pytest.mark.asyncio
async def test_search_caches_empty_result(monkeypatch) -> None:
    client = OpenLibraryClient()
    monkeypatch.setattr(cache_service, "get", AsyncMock(return_value=None))
    cache_set = AsyncMock()
    monkeypatch.setattr(cache_service, "set", cache_set)
    monkeypatch.setattr(
        client,
        "_get",
        AsyncMock(return_value={"numFound": 0, "docs": []}),
    )

    result = await client.search_by_title_author("Unknown", "Unknown")

    assert result == {}
    cache_set.assert_awaited_once()
    await client.close()


@pytest.mark.asyncio
async def test_search_maps_timeout_to_domain_error(monkeypatch) -> None:
    client = OpenLibraryClient(timeout=3)
    monkeypatch.setattr(cache_service, "get", AsyncMock(return_value=None))
    monkeypatch.setattr(
        client,
        "_get",
        AsyncMock(side_effect=httpx.ReadTimeout("timeout")),
    )

    with pytest.raises(OpenLibraryTimeoutException):
        await client.search_by_title_author("Clean Code", "Martin")

    await client.close()


@pytest.mark.asyncio
async def test_search_rejects_invalid_response(monkeypatch) -> None:
    client = OpenLibraryClient()
    monkeypatch.setattr(cache_service, "get", AsyncMock(return_value=None))
    monkeypatch.setattr(
        client,
        "_get",
        AsyncMock(return_value={"unexpected": True}),
    )

    with pytest.raises(OpenLibraryException):
        await client.search_by_isbn("9780132350884")

    await client.close()
