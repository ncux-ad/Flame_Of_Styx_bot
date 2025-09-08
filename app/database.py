from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import load_config

Base = declarative_base()

# Get database URL from config
config = load_config()
database_url = f"sqlite+aiosqlite:///{config.db_path}"

# Create async engine
engine = create_async_engine(database_url, echo=False, future=True, pool_pre_ping=True)

# Create session maker
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables."""
    # Import models here to avoid circular imports
    from app.models import Bot, Channel, ModerationLog, SuspiciousProfile, User

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
