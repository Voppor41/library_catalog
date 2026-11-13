from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from library_catalog.core.config import settings
from library_catalog.core.security import create_access_token, decode_access_token


def test_create_access_token_contains_identity_role_and_expiration() -> None:
    user_id = uuid4()
    issued_at = datetime.now(UTC)

    token = create_access_token(user_id=user_id, role="user")
    payload = jwt.decode(
        token,
        key=settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "user"

    expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
    expected_expiration = issued_at + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    assert abs(expires_at - expected_expiration) < timedelta(seconds=2)


def test_decode_access_token_rejects_expired_token() -> None:
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "role": "user",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        },
        key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_decode_access_token_requires_identity_role_and_expiration() -> None:
    token = jwt.encode(
        {"sub": str(uuid4())},
        key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)
