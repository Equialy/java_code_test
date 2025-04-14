from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
import logging

from ..exceptions import NotFoundError, BalanceError, TransferError

logger = logging.getLogger(__name__)

from ..models import Wallet
from ..schemas import WalletSchema
from ..schemas.schemas import WalletCreate, WalletResponseSchema, WalletTransferSchema


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

    async def transfer_user(self, wallet_data: WalletTransferSchema) -> tuple[WalletResponseSchema, WalletResponseSchema]:

        uuid_from = wallet_data.wallet_from.uuid
        uuid_to = wallet_data.wallet_to.uuid
        amount = wallet_data.wallet_from.amount

        if uuid_from == uuid_to:
            raise TransferError("Cannot transfer funds to the same wallet.")

        if amount < 0:
            raise TransferError("Transfer amount cannot be negative.")
        async with self.session.begin():
            # --- НАЧАЛО КЛЮЧЕВОГО ИСПРАВЛЕНИЯ ДЛЯ DEADLOCK ---
            # Определяем порядок блокировки по UUID
            lock_order_uuids = sorted([uuid_from, uuid_to])

            stmt = (
                sa.select(self.model)
                .where(self.model.uuid.in_(lock_order_uuids))
                .order_by(self.model.uuid)  # Гарантируем порядок запроса блокировки
                .with_for_update()
            )

            result = await self.session.execute(stmt)
            wallets = result.scalars().all()
            # --- КОНЕЦ КЛЮЧЕВОГО ИСПРАВЛЕНИЯ ДЛЯ DEADLOCK ---

            found_wallets = {w.uuid: w for w in wallets}

            if uuid_from not in found_wallets:
                logger.warning("Запись отправителя не найдена: %r", uuid_from)
                raise NotFoundError(uuid_from)
            if uuid_to not in found_wallets:
                logger.warning("Запись получателя не найдена: %r", uuid_to)
                raise NotFoundError(uuid_to)

            from_wallet = found_wallets[uuid_from]
            to_wallet = found_wallets[uuid_to]

            if from_wallet.balance < amount:
                raise BalanceError(uuid_from)

            if amount > 0:
                from_wallet.balance -= amount
                to_wallet.balance += amount

            # Конвертация в Pydantic схемы перед возвратом
            response_from = WalletResponseSchema.model_validate(from_wallet)
            response_to = WalletResponseSchema.model_validate(to_wallet)

            return (response_from, response_to)
