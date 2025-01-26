from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from ..models import Wallet
from ..schemas import WalletSchema
from ..schemas.schemas import WalletUpdateSchema, WalletCreate


class WalletRepositoryProtocol(Protocol):

    async def get_by_id(self,  wallet_id: UUID) -> WalletSchema:
        ...

    async def create(self, create_objects: WalletCreate) -> WalletSchema:
        ...

    async def update(self,  wallet_id: UUID, **update_object) -> WalletSchema:
        ...

class WalletRepositoryFactoryProtocol(Protocol):

    async def make(self) -> WalletRepositoryProtocol:
        ...

class WalletRepositoryImpl:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = Wallet

    async def create(self, create_objects: WalletCreate) :
        stmt =sa.insert(self.model).values(create_objects.model_dump()).returning(self.model)
        model = await self.session.execute(stmt)
        result = model.scalar_one()
        return result

    async def get_by_id(self, wallet_id: UUID) :
        query = sa.select(self.model).where(self.model.uuid == str(wallet_id))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, wallet_id: UUID, **update_object: dict) :
        stmt =(sa.update(self.model)
               .where(self.model.uuid == wallet_id)
               .values(**update_object)
               .returning(self.model))
        result = await self.session.execute(stmt)
        return result.scalar_one()

