"""
Database connection and session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    str(settings.database_url),
    echo=settings.debug,
    poolclass=NullPool if settings.debug else None,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.
    Use with FastAPI Depends.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    Call this on application startup.
    """
    from src.database.models import Base

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created successfully")


async def close_db() -> None:
    """
    Close database connections.
    Call this on application shutdown.
    """
    await engine.dispose()
    logger.info("Database connections closed")


# Utility functions
async def execute_in_transaction(session: AsyncSession, func, *args, **kwargs):
    """
    Execute a function within a transaction.

    Args:
        session: AsyncSession
        func: Function to execute
        *args, **kwargs: Arguments to pass to function

    Returns:
        Result of the function

    Raises:
        Exception: If transaction fails
    """
    try:
        result = await func(session, *args, **kwargs)
        await session.commit()
        return result
    except Exception as e:
        await session.rollback()
        logger.error(f"Transaction failed: {e}")
        raise


async def health_check() -> bool:
    """
    Check database connection health.

    Returns:
        bool: True if database is healthy
    """
    try:
        async with AsyncSessionLocal() as session:
            # Execute a simple query
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False