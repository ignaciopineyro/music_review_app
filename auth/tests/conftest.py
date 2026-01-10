import pytest
import pytest_asyncio
import os
import uuid

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient
from dotenv import load_dotenv
from app.main import app
from app.db import Base, get_db

load_dotenv(".env.testing")

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_auth_db"
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL, echo=False, future=True, pool_pre_ping=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def db_session(test_engine):
    async_sessionmaker_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_sessionmaker_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    unique_id = str(uuid.uuid4()).replace("-", "")[:8]
    return {
        "username": f"testuser{unique_id}",
        "email": f"test{unique_id}@example.com",
        "password": "TestPassword123",
    }


@pytest.fixture
def another_test_user_data():
    unique_id = str(uuid.uuid4()).replace("-", "")[:8]
    return {
        "username": f"anotheruser{unique_id}",
        "email": f"another{unique_id}@example.com",
        "password": "AnotherPassword123",
    }
