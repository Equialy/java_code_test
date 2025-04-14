from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
import logging

from ..exceptions import NotFoundError, BalanceError

logger = logging.getLogger(__name__)

from ..models import Wallet
from ..schemas import WalletSchema
from ..schemas.schemas import  WalletCreate, WalletResponseSchema, WalletTransferSchema


class WalletRepositoryProtocol(Protocol):

    async def get_by_id(self, wallet_id: UUID) -> WalletSchema:
        ...

    async def create(self, create_objects: WalletCreate) -> WalletSchema:
        ...

    async def deposit_wallet(self, wallet_id: UUID, amount: Decimal) -> WalletSchema:
        ...

    async def withdraw_wallet(self, wallet_id: UUID, amount: Decimal) -> WalletSchema:
        ...

    async def transfer_user(self, wallet_data: WalletTransferSchema) -> tuple[
        WalletResponseSchema, WalletResponseSchema]:
        ...


class WalletRepositoryImpl:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = Wallet

    async def create(self, create_objects: WalletCreate):
        stmt = sa.insert(self.model).values(create_objects.model_dump()).returning(self.model)
        model = await self.session.execute(stmt)
        result = model.scalar_one()
        logger.info("Кошелек %r создан", result.uuid)
        return result

    async def get_by_id(self, wallet_id: UUID):
        query = sa.select(self.model).where(self.model.uuid == str(wallet_id)).with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def deposit_wallet(self, wallet_id: UUID, amount: Decimal) -> WalletResponseSchema:
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

    async def transfer_user(self, wallet_data: WalletTransferSchema) -> tuple[
        WalletResponseSchema, WalletResponseSchema]:
        async with self.session.begin():
            from_wallet = await self.get_by_id(wallet_data.wallet_from.uuid)
            if not from_wallet or from_wallet.balance < wallet_data.wallet_from.amount:
                raise BalanceError(wallet_data.wallet_from.uuid)

            cte = (
                sa.select(self.model.uuid,
                          sa.case(
                              (self.model.uuid == wallet_data.wallet_from.uuid,
                               self.model.balance - wallet_data.wallet_from.amount),
                              (self.model.uuid == wallet_data.wallet_to.uuid,
                               self.model.balance + wallet_data.wallet_from.amount)
                          ).label("new_balance")
                      ).where(self.model.uuid.in_([
                    wallet_data.wallet_from.uuid,
                    wallet_data.wallet_to.uuid
                ])
                )
                .cte("updates")
            )
            update_stmt = (
                sa.update(self.model)
                .values(balance=cte.c.new_balance)
                .where(self.model.uuid == cte.c.uuid)
                .returning(self.model)
            )
            result = await self.session.execute(update_stmt)
            return tuple(result.scalars().all())
