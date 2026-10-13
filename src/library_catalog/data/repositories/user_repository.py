from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from ..models.user import User


class UserRepository(BaseRepository[User]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username) -> User:
        stmt = select(User).where(User.username == username)
        return await self.session.scalar(stmt)

    async def get_by_email(self, email) -> User:
        stmt = select(User).where(User.email == email)
        return await self.session.scalar(stmt)