from typing import Generic, TypeVar, Type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: UUID) -> T | None:
        result = await self.session.get(self.model, id)
        return result

    async def update(self, id: UUID, **kwargs) -> T | None:
        new_instance = await self.get_by_id(id)
        if new_instance is None:
            return None

        for field, value in kwargs.items():
            if hasattr(new_instance, field):
                setattr(new_instance, field, value)

        await self.session.commit()
        await self.session.refresh(new_instance)
        return new_instance

    async def delete(self, id: UUID) -> bool:
        instance = await self.get_by_id(id)
        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.commit()
        return True

    async def get_all(self, limit: int = 100, offset: int = 0,) -> list[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return list(result.all())


