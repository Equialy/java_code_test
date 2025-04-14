from src.core.utils.exceptions import RecordNotFoundError, ValidationError
from uuid import UUID


class NotFoundError(RecordNotFoundError):
    def __init__(self, uuid: UUID, *args) -> None:
        self.message = f"Запись не найдена"
        super().__init__(uuid=uuid, message=self.message, *args)


class BalanceError(Exception):
    def __init__(self, uuid: UUID, *args) -> None:
        self.uuid = uuid
        self.message = f"Недостаточно средств"
        # super().__init__(field=str(uuid), message=self.message, *args)


class ValidInputError(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self.message = message


class TransferError(Exception): # Для общих ошибок перевода
    def __init__(self, msg):
        self.msg = msg

class WalletNotFoundError(Exception): # Пример кастомного исключения
    def __init__(self, wallet_id):
        self.wallet_id = wallet_id
        super().__init__(f"Wallet not found: {wallet_id}")

