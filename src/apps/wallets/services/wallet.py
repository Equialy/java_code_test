from typing import Protocol
from uuid import UUID

from src.apps.wallets.exceptions import NotFoundError, BalanceError
from src.apps.wallets.repositories import WalletRepositoryProtocol
from src.apps.wallets.schemas import WalletSchema
from src.apps.wallets.schemas.schemas import WalletCreate, WalletDataOperationsSchema


class WalletServiceProtocol(Protocol):

    async def create_wallet(self, create_objects: WalletCreate) -> WalletSchema:
        ...

    async def get_wallet_by_id(self, wallet_id: UUID) -> WalletSchema:
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

    async def deposit(self, wallet_data: WalletDataOperationsSchema) -> WalletSchema:
        try:
            updated_wallet = await self.wallet_factory_repository.deposit_wallet(wallet_data.uuid, wallet_data.amount)
        except:
            raise NotFoundError(wallet_data.uuid)
        return updated_wallet

    async def withdraw(self, wallet_data: WalletDataOperationsSchema) -> WalletSchema:
        try:
            updated_wallet = await self.wallet_factory_repository.withdraw_wallet(wallet_data.uuid, wallet_data.amount)
        except:
            wallet = await self.wallet_factory_repository.get_by_id(wallet_data.uuid)
            if not wallet:
                raise NotFoundError(wallet_data.uuid)
            else:
                raise BalanceError(wallet_data.uuid)
        return updated_wallet
