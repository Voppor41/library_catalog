from functools import lru_cache
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db
from ..core.security import decode_access_token
from ..data.models.user import User
from ..data.repositories.book_repository import BookRepository
from ..data.repositories.user_repository import UserRepository
from ..domain.exceptions import InvalidTokenException
from ..domain.services.book_service import BookService
from ..domain.services.user_service import UserService
from ..external.openlibrary.client import OpenLibraryClient

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
)


@lru_cache
def get_openlibrary_client() -> OpenLibraryClient:
    """
       Получить singleton OpenLibraryClient.

       lru_cache создает клиент один раз и переиспользует.
    """
    return OpenLibraryClient(
        base_url=settings.openlibrary_base_url,
        timeout=settings.openlibrary_timeout,
    )


async def get_book_repository(
        db: Annotated[AsyncSession, Depends(get_db)],
) -> BookRepository:
    return BookRepository(db)


async def get_book_service(
        book_repo: Annotated[BookRepository, Depends(get_book_repository)],
        ol_client: Annotated[OpenLibraryClient, Depends(get_openlibrary_client)],
) -> BookService:
    return BookService(
        book_repository=book_repo,
        openlibrary_client=ol_client,
    )

async def get_user_repository(
        db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)

async def get_user_service(
        user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo)


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise InvalidTokenException() from exc

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise InvalidTokenException()

    return user


# ========== TYPE ALIASES ДЛЯ УДОБСТВА ==========

# Можно использовать в роутерах так:
# async def my_route(service: BookServiceDep):
BookServiceDep = Annotated[BookService, Depends(get_book_service)]
BookRepoDep = Annotated[BookRepository, Depends(get_book_repository)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db)]
AuthServiceDep = Annotated[UserService, Depends(get_user_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
