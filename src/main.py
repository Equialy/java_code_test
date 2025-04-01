import uvicorn
from fastapi import FastAPI

from src.exceptions import apply_exceptions_handlers
from src.middlware import apply_middleware
from src.routers import apply_routes
import logging

from src.settings import config_logging


def create_app() -> FastAPI:
    config_logging(level=logging.INFO)
    app = FastAPI(
        docs_url='/docs',
        openapi_url='/docs.json',
    )

    app = apply_exceptions_handlers(apply_routes(apply_middleware(app)))

    return app


app = create_app()

if __name__ == '__main__':
    uvicorn.run('src.main:app', reload=False)
