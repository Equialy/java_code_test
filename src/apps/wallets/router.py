from uuid import UUID

from fastapi import APIRouter, status

from src.apps.wallets.depends import UserService
from src.apps.wallets.schemas import WalletResponseSchema
from src.apps.wallets.schemas.schemas import WalletCreate, WalletDataOperationsSchema

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_wallet(user_service: UserService, create_objects: WalletCreate) -> WalletResponseSchema:
    """Создание кошелька"""
    wallet = await user_service.create_wallet(create_objects)
    return wallet


@router.get("/{wallet_id}")
async def get_wallet(wallet_id: UUID, user_service: UserService) -> WalletResponseSchema:
    """Получение кошелька по UUID"""
    return await user_service.get_wallet_by_id(wallet_id)


@router.post("/{wallet_id}/deposit")
async def deposit(wallet_data: WalletDataOperationsSchema, user_service: UserService) -> WalletResponseSchema:
    """Внесение депозита"""
    return await user_service.deposit(wallet_data)


@router.post("/{wallet_id}/withdraw")
async def withdraw(wallet_data: WalletDataOperationsSchema, user_service: UserService) -> WalletResponseSchema:
    """Снятие со счета"""
    return await user_service.withdraw(wallet_data)
