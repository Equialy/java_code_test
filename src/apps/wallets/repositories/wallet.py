from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from ..models import Wallet
from ..schemas import WalletSchema
from ..schemas.schemas import WalletUpdateSchema, WalletCreate


class WalletRepositoryProtocol(Protocol):

    async def get_by_id(self, wallet_id: UUID) -> WalletSchema:
        ...

    async def create(self, create_objects: WalletCreate) -> WalletSchema:
        ...

    async def deposit_wallet(self, wallet_id: UUID, amount: Decimal) -> WalletSchema:
        ...

    async def withdraw_wallet(self, wallet_id: UUID, amount: Decimal) -> WalletSchema:
        ...


class WalletRepositoryImpl:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = Wallet

    async def create(self, create_objects: WalletCreate):
        stmt = sa.insert(self.model).values(create_objects.model_dump()).returning(self.model)
        model = await self.session.execute(stmt)
        result = model.scalar_one()
        return result

    async def get_by_id(self, wallet_id: UUID):
        query = sa.select(self.model).where(self.model.uuid == str(wallet_id)).with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def deposit_wallet(self, wallet_id: UUID, amount: Decimal):
        stmt = (sa.update(self.model)
                .where(self.model.uuid == wallet_id)
                .values(balance=self.model.balance + amount)
                .returning(self.model))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def withdraw_wallet(self, wallet_id: UUID, amount: Decimal):
        stmt = (sa.update(self.model)
                .where(self.model.uuid == wallet_id,
                       self.model.balance >= amount)
                .values(balance=self.model.balance - amount)
                .returning(self.model))
        result = await self.session.execute(stmt)
        return result.scalar_one()
