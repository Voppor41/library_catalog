from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from library_catalog.core.config import settings
from library_catalog.core.security import create_access_token


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
