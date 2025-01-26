from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exception_handlers import http_exception_handler

from src.apps.wallets.exceptions import ValidInputError
from src.core.utils.exceptions import (
    ModelAlreadyExistsError,
    ValidationError,
    RecordNotFoundError
)



async def model_already_exists_error_handler(request:Request, error: ModelAlreadyExistsError) -> Response:
    """
    Обработчик ошибов возникающий при попытка создать модель с существующим уникальным полем.
    """
    return await http_exception_handler(
        request,
        HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "field": error.field,
                "message": error.message,
            }
        )
    )

async def valid_input_error_handler(request:Request, error: ValidInputError):
    return await http_exception_handler(
        request,
        HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": error.message,
            }
        )
    )
async def record_not_found_error_handler(request:Request, error: RecordNotFoundError):
    return await http_exception_handler(
        request,
        HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "uuid": str(error.uuid),
                "message": error.message,
            }
        )
    )


async def validation_error_handler(request: Request, error: ValidationError) -> Response:
    """Обработчик ошибки валидации"""
    return await http_exception_handler(
        request,
        HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "field": error.field,
                "message": error.message
            }
        )
    )

def apply_exceptions_handlers(app: FastAPI) -> FastAPI:
    """
    Применяем глобальные обработчики исключений.
    """
    app.add_exception_handler(ModelAlreadyExistsError, model_already_exists_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(RecordNotFoundError, record_not_found_error_handler)
    app.add_exception_handler(ValidInputError, valid_input_error_handler)
    return app