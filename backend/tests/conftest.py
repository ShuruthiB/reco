import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_merchant_id
from app.db.session import get_db_session
from app.domain.models import Merchant
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/reco"),
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def merchant_id(db_session: AsyncSession) -> uuid.UUID | None:
    result = await db_session.execute(
        select(Merchant.id).where(Merchant.status == "active").limit(1)
    )
    return result.scalar_one_or_none()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, merchant_id: uuid.UUID | None
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    async def override_merchant_id() -> uuid.UUID:
        if merchant_id is not None:
            return merchant_id
        return uuid.UUID("00000000-0000-0000-0000-000000000001")

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_merchant_id] = override_merchant_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
