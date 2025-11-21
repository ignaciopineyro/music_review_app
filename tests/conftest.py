import pytest
import asyncio

from fastapi.testclient import TestClient
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db import get_session as original_get_session
from app.models.album import Album


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine_test = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
async_session_test = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


async def get_session_override():
    async with async_session_test() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _create_tables():
        async with engine_test.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    loop.run_until_complete(_create_tables())
    loop.close()


@pytest.fixture
def client():
    from fastapi import FastAPI
    from app.routers import albums

    test_app = FastAPI()
    test_app.include_router(albums.router)

    test_app.dependency_overrides[original_get_session] = get_session_override

    with TestClient(test_app) as c:
        yield c

    test_app.dependency_overrides.clear()
