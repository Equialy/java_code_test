from fastapi import FastAPI
from src.apps.wallets.router import router as wallet_router


def apply_routes(app: FastAPI) -> FastAPI:

    app.include_router(wallet_router)

    return app
