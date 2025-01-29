from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.wallets.repositories import WalletRepositoryImpl, WalletRepositoryProtocol
from src.apps.wallets.services import WalletServiceProtocol, WalletServiceImpl
from src.core.db import get_async_session

# --- repositories ---

Session = Annotated[AsyncSession, Depends(get_async_session)]

def get_wallet_repositories(session: Session) -> WalletRepositoryProtocol:
    return WalletRepositoryImpl(session)

WalletFactoryRepository = Annotated[WalletRepositoryProtocol, Depends(get_wallet_repositories)]

# --- services ---

def get_wallet_service(users_factory_repositories: WalletFactoryRepository) -> WalletServiceProtocol:
    return WalletServiceImpl(users_factory_repositories)


WalletService = Annotated[WalletServiceProtocol, Depends(get_wallet_service)]
