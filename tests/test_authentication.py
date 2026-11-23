from uuid import uuid4

import pytest

from library_catalog.api.dependencies import get_current_user
from library_catalog.core.security import create_access_token
from library_catalog.domain.exceptions import InvalidTokenException


class FakeUserRepository:
    def __init__(self, user: object | None) -> None:
        self.user = user

    async def get_by_id(self, user_id):
        return self.user


@pytest.mark.asyncio
async def test_get_current_user_returns_existing_user() -> None:
    user_id = uuid4()
    user = object()
    repository = FakeUserRepository(user)
    token = create_access_token(user_id=user_id, role="user")

    result = await get_current_user(token=token, user_repo=repository)

    assert result is user


@pytest.mark.asyncio
async def test_get_current_user_rejects_unknown_user() -> None:
    token = create_access_token(user_id=uuid4(), role="user")

    with pytest.raises(InvalidTokenException):
        await get_current_user(
            token=token,
            user_repo=FakeUserRepository(None),
        )


@pytest.mark.asyncio
async def test_get_current_user_rejects_malformed_token() -> None:
    with pytest.raises(InvalidTokenException):
        await get_current_user(
            token="not-a-jwt",
            user_repo=FakeUserRepository(object()),
        )
