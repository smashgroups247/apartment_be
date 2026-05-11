"""The database module"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from api.utils.settings import settings, BASE_DIR

DB_TYPE = settings.DB_TYPE


def get_db_engine(test_mode: bool = False):
    if DB_TYPE == "sqlite" or test_mode:
        BASE_PATH = f"sqlite+aiosqlite:///{BASE_DIR}"
        DATABASE_URL = BASE_PATH + "/"

        if test_mode:
            DATABASE_URL = BASE_PATH + "test.db"
            return create_async_engine(
                DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
            )
        return create_async_engine(DATABASE_URL, echo=False)

    # For PostgreSQL: use DB_URL directly (has the full external hostname),
    # but ensure the scheme is compatible with asyncpg.
    raw_url = settings.DB_URL
    if raw_url.startswith("postgresql://"):
        DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgres://"):
        DATABASE_URL = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL = raw_url

    return create_async_engine(DATABASE_URL, echo=False)


engine = get_db_engine()

# Create standard async sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

Base = declarative_base()


async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
