from ...api.v1.schemas.user import UserCreate, UserLogin, UserPublic, TokenResponse
from ...core.security import create_access_token, hash_password, verify_password
from ...data.repositories.user_repository import UserRepository
from ..exceptions import InvalidCredentialsException, UserAlreadyExistsException


class UserService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def create_user(self, data: UserCreate) -> UserPublic:

        if await self.user_repository.get_by_username(data.username):
            raise UserAlreadyExistsException(data.username)
        if await self.user_repository.get_by_email(data.email):
            raise UserAlreadyExistsException(data.email)

        user_data = await self.user_repository.create(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
            role="user",
        )

        return UserPublic.model_validate(user_data)

    async def login_user(self, data: UserLogin) -> UserPublic:

        user = await self.user_repository.get_by_username(data.username)
        if user is None or not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsException()

        token = create_access_token(user.id, user.role)
        return TokenResponse(access_token=token)