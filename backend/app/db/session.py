import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings
from backend.app.utils.logging import logger
from backend.app.db.base import Base

# Determine database engine
db_url = settings.DATABASE_URL

# For sqlite in async mode: ensure sqlite+aiosqlite
if db_url.startswith("sqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")

# Connect args for sqlite
connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

try:
    async_engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        connect_args=connect_args,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    logger.info(f"Database configured with engine: {db_url.split('://')[0]}")
except Exception as e:
    logger.error(f"Error configuring database engine: {e}")
    # Fallback to local in-memory sqlite
    async_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create tables if not existing."""
    # Import all models to ensure they are registered with Base
    from backend.app.models import (
        user_profile,
        marine_observation,
        fishing_zone,
        alert,
        query,
        recommendation,
    )
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")
