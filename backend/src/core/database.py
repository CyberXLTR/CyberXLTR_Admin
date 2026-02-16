"""
PostgreSQL Database Client for CyberXLTR Admin Platform
"""

import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from .config import settings

logger = logging.getLogger(__name__)

# Create declarative base for models
Base = declarative_base()


class DatabaseClient:
    """
    PostgreSQL database client with async support
    """
    
    _instance: Optional['DatabaseClient'] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._engine is None:
            self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the database engine"""
        try:
            # Convert postgresql:// to postgresql+asyncpg://
            database_url = settings.database_url
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            self._engine = create_async_engine(
                database_url,
                echo=settings.debug,
                poolclass=NullPool if settings.debug else None,
                pool_pre_ping=True,
            )
            
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise RuntimeError(f"Cannot initialize database: {e}")
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine"""
        if self._engine is None:
            self._initialize_engine()
        return self._engine
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if self._session_factory is None:
            self._initialize_engine()
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connection closed")


# Global database client instance
db_client = DatabaseClient()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with db_client.get_session() as session:
        yield session

