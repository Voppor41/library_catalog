import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        headers: dict[str, str] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.headers = headers
        super().__init__(self.message)


class NotFoundException(AppException):
    """Ресурс не найден."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=404,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": {
                    "code": exc.__class__.__name__,
                    "message": exc.message,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        errors = [
            {
                "location": error["loc"],
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "request_id": getattr(request.state, "request_id", None),
                    "errors": errors,
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Database request failed request_id=%s", request_id)
        return JSONResponse(
            status_code=503,
            content={
                "detail": {
                    "code": "DATABASE_ERROR",
                    "message": "Database is temporarily unavailable",
                    "request_id": request_id,
                }
            },
        )
