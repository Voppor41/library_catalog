import httpx
from pydantic import ValidationError

from ...core.cache import cache_service, make_cache_key
from ...core.config import settings
from ...domain.exceptions import OpenLibraryException, OpenLibraryTimeoutException
from ..base.base_client import BaseApiClient
from .schemas import OpenLibrarySearchDoc, OpenLibrarySearchResponse


class OpenLibraryClient(BaseApiClient):

    def __init__(
            self,
            base_url: str = "https://openlibrary.org",
            timeout: float = 10.0
    ):
        super().__init__(base_url, timeout=timeout)

    def client_name(self) -> str:
        return "openlibrary"

    async def search_by_isbn(self, isbn: str) -> dict:
        cache_key = make_cache_key("ol:isbn", isbn)
        return await self._search(
            cache_key,
            params={"isbn": isbn, "limit": 1},
        )

    async def search_by_title_author(
            self,
            title: str,
            author: str,
    ) -> dict:

        cache_key = make_cache_key("ol:title-author", title, author)
        return await self._search(
            cache_key,
            params={"title": title, "author": author, "limit": 1},
        )

    async def enrich(
            self,
            title: str,
            author: str,
            isbn: str | None,
    ) -> dict:

        if isbn:
            data = await self.search_by_isbn(isbn)
            if data:
                return data

        return await self.search_by_title_author(title, author)

    async def _search(self, cache_key: str, params: dict) -> dict:
        cached = await cache_service.get(cache_key)
        if cached is not None:
            return cached

        try:
            data = await self._get("/search.json", params=params)
            response = OpenLibrarySearchResponse.model_validate(data)
            result = (
                self._extract_book_data(response.docs[0])
                if response.docs
                else {}
            )
            await cache_service.set(
                cache_key,
                result,
                settings.cache_ttl_openlibrary,
            )
            return result
        except httpx.TimeoutException as exc:
            raise OpenLibraryTimeoutException(self.timeout) from exc
        except httpx.HTTPError as exc:
            raise OpenLibraryException(str(exc)) from exc
        except (ValidationError, ValueError) as exc:
            raise OpenLibraryException("Invalid response") from exc

    def _extract_book_data(self, doc: OpenLibrarySearchDoc) -> dict:

        result = {}

        if doc.cover_i:
            result["cover_url"] = (
                f"https://covers.openlibrary.org/b/id/{doc.cover_i}-L.jpg"
            )

        if doc.subject:
            result["subjects"] = doc.subject[:10]

        if doc.publisher:
            result["publisher"] = doc.publisher[0]

        if doc.language:
            result["language"] = doc.language[0]

        if doc.ratings_average is not None:
            result["rating"] = doc.ratings_average

        return result

