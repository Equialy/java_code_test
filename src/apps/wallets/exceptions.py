from src.core.utils.exceptions import RecordNotFoundError, ValidationError
from uuid import UUID


class NotFoundError(RecordNotFoundError):
    def __init__(self, uuid: UUID, *args) -> None:
        self.message = f"Запись не найдена"
        super().__init__(uuid=uuid, message=self.message, *args)


class BalanceError(ValidationError):
    def __init__(self, uuid: UUID, *args) -> None:
        self.message = f"Недостаточно средств"
        super().__init__(field=str(uuid), message=self.message, *args)


class ValidInputError(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self.message = message
