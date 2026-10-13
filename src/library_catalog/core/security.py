import jwt
import bcrypt

from datetime import datetime, timedelta, timezone
from uuid import UUID

from .config import settings


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(user_id: UUID, role: str) -> str:

    expire = datetime.now(timezone.utc) + timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        algorithm=settings.JWT_ALGORITHM,
        key=settings.SECRET_KEY,
    )