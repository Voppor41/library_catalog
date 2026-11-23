import anyio
from sqlalchemy.exc import IntegrityError

from ...api.v1.schemas.user import TokenResponse, UserCreate, UserLogin, UserPublic
from ...core.security import create_access_token, hash_password, verify_password
from ...data.repositories.user_repository import UserRepository
from ..exceptions import InvalidCredentialsException, UserAlreadyExistsException


class UserService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def create_user(self, data: UserCreate) -> UserPublic:

        if await self.user_repository.get_by_username(data.username):
            raise UserAlreadyExistsException("username", data.username)
        if await self.user_repository.get_by_email(data.email):
            raise UserAlreadyExistsException("email", str(data.email))

        password_hash = await anyio.to_thread.run_sync(hash_password, data.password)

        try:
            user_data = await self.user_repository.create(
                username=data.username,
                email=data.email,
                password_hash=password_hash,
                role="user",
            )
            await self.user_repository.commit()
        except IntegrityError:
            await self.user_repository.rollback()
            if await self.user_repository.get_by_username(data.username):
                raise UserAlreadyExistsException("username", data.username)
            if await self.user_repository.get_by_email(data.email):
                raise UserAlreadyExistsException("email", str(data.email))
            raise

        return UserPublic.model_validate(user_data)

    async def login_user(self, data: UserLogin) -> TokenResponse:

        user = await self.user_repository.get_by_username(data.username)
        if user is None:
            raise InvalidCredentialsException()

        password_is_valid = await anyio.to_thread.run_sync(
            verify_password,
            data.password,
            user.password_hash,
        )
        if not password_is_valid:
            raise InvalidCredentialsException()

        token = create_access_token(user.id, user.role)
        return TokenResponse(access_token=token)
