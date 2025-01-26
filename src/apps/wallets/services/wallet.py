from typing import Protocol
from uuid import UUID
from decimal import Decimal

from src.apps.wallets.exceptions import NotFoundError, BalanceError
from src.apps.wallets.repositories import WalletRepositoryFactoryProtocol, WalletRepositoryProtocol
from src.apps.wallets.schemas import WalletSchema
from src.apps.wallets.schemas.schemas import WalletCreate, WalletDataOperationsSchema


class WalletServiceProtocol(Protocol):

    async def create_wallet(self, create_objects: WalletCreate) -> WalletSchema:

        ...
    async def get_wallet_by_id(self,wallet_id: UUID ) -> WalletSchema:
        ...

    async def deposit(self, wallet_data: WalletDataOperationsSchema) -> WalletSchema:
        ...

    async def withdraw(self, wallet_data: WalletDataOperationsSchema) -> WalletSchema:
        ...


class WalletServiceImpl:

    def __init__(self, wallet_factory_repository: WalletRepositoryProtocol) -> None:
        self.wallet_factory_repository = wallet_factory_repository

    async def create_wallet(self, create_objects: WalletCreate) -> WalletSchema:
        wallet_service = await self.wallet_factory_repository.create(create_objects)
        return wallet_service

    async def get_wallet_by_id(self, wallet_id: UUID) -> WalletSchema:

        wallet_service = await self.wallet_factory_repository.get_by_id(wallet_id=wallet_id)
        if not wallet_service:
            raise NotFoundError(wallet_id)


        return wallet_service

    async def deposit(self,wallet_data: WalletDataOperationsSchema ) -> WalletSchema:

        wallet_model_id = await self.wallet_factory_repository.get_by_id(wallet_data.uuid)
        if not wallet_model_id:
            raise NotFoundError(wallet_data.uuid)
        wallet_balance = wallet_model_id.balance + wallet_data.amount
        return await self.wallet_factory_repository.update(wallet_data.uuid, balance=wallet_balance)

    async def withdraw(self, wallet_data: WalletDataOperationsSchema) -> WalletSchema:
        wallet_model_id = await self.wallet_factory_repository.get_by_id(wallet_data.uuid)

        if not wallet_model_id:
            raise NotFoundError(wallet_data.uuid)
        if wallet_model_id.balance < wallet_data.amount:
            raise BalanceError(wallet_data.uuid)

        wallet_balance = wallet_model_id.balance - wallet_data.amount
        return await self.wallet_factory_repository.update(wallet_data.uuid, balance=wallet_balance)

