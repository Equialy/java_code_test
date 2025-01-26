import asyncio

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.db import Base
from src.main import app
from src.settings import settings

asyncio_engine_test = create_async_engine(
    settings.test_db.url_db_test, echo=settings.debug
)

AsyncSessionFactoryTest = async_sessionmaker(
    asyncio_engine_test,
    autocommit=False,
    expire_on_commit=False,
    future=True,
    autoflush=False,
)


@pytest.fixture(scope='session')
async def prepare_database():
    async with asyncio_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="function")
async def ac_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def session():
    async with AsyncSessionFactoryTest() as session:
        yield session
