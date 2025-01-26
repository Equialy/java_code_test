import uuid
from typing import Any, Generic, TypeVar
from uuid import UUID
from fastapi import HTTPException, status


class RecordNotFoundError(Exception):
    def __init__(self, uuid: UUID, message: str, *args: object) -> None:
        super().__init__(*args)
        self.uuid = uuid
        self.message = message






class ModelAlreadyExistsError(Exception):
    """
    Ошибка, возникающая при попытке создать модель с существующим уникальным полем.
    """

    def __init__(self, field: str, message: str, *args: object) -> None:
        super().__init__(*args)
        self.field = field
        self.message = message


class ValidationError(Exception):
    """
    Ошибка валидации.
    """

    def __init__(self, field: str | list[str], message: str, *args: object) -> None:
        super().__init__(*args)
        self.field = field
        self.message = message




class FileNotFound(HTTPException):
    """
    Исключение если файл не найден.
    """

    def __init__(self, path: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f'File {path} not found.', headers=headers)
