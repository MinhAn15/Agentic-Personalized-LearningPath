"""
Database connections and client factories.

This module provides connection management for:
- Redis (hot cache)
- PostgreSQL (cold storage)
- Neo4j (knowledge graph)
"""

from typing import Optional
import logging
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.config import get_settings

logger = logging.getLogger(__name__)

# Global connection instances
_redis_client: Optional[redis.Redis] = None
_postgres_engine = None
_postgres_session_factory = None


# ============= REDIS =============

async def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("🔴 Connected to Redis")
    
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("🔴 Redis connection closed")


# ============= POSTGRESQL =============

def get_postgres_engine():
    """Get or create PostgreSQL async engine"""
    global _postgres_engine
    
    if _postgres_engine is None:
        settings = get_settings()
        # Convert postgresql:// to postgresql+asyncpg://
        db_url = settings.DATABASE_URL.replace(
            "postgresql://", 
            "postgresql+asyncpg://"
        )
        _postgres_engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=5,
            max_overflow=10
        )
        logger.info("🐘 PostgreSQL engine created")
    
    return _postgres_engine


def get_session_factory():
    """Get session factory for PostgreSQL"""
    global _postgres_session_factory
    
    if _postgres_session_factory is None:
        engine = get_postgres_engine()
        _postgres_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    return _postgres_session_factory


async def get_postgres_session() -> AsyncSession:
    """Get a new PostgreSQL session"""
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def close_postgres():
    """Close PostgreSQL engine"""
    global _postgres_engine
    
    if _postgres_engine:
        await _postgres_engine.dispose()
        _postgres_engine = None
        logger.info("🐘 PostgreSQL engine disposed")


# ============= POSTGRES CLIENT WRAPPER =============

class PostgresClient:
    """
    Wrapper for PostgreSQL operations matching state_manager interface.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute(self, query: str, params: tuple = None):
        """Execute a query"""
        from sqlalchemy import text
        await self.session.execute(text(query), params or {})
        await self.session.commit()
    
    async def fetch_one(self, query: str, params: tuple = None):
        """Fetch one row"""
        from sqlalchemy import text
        result = await self.session.execute(text(query), params or {})
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None
    
    async def fetch_all(self, query: str, params: tuple = None):
        """Fetch all rows"""
        from sqlalchemy import text
        result = await self.session.execute(text(query), params or {})
        return [dict(row._mapping) for row in result.fetchall()]


# ============= STATE MANAGER FACTORY =============

async def create_state_manager():
    """
    Factory function to create CentralStateManager with connections.
    
    Usage:
        state_manager = await create_state_manager()
    """
    from backend.core.state_manager import CentralStateManager
    
    redis_client = await get_redis_client()
    
    # For PostgreSQL, we use a wrapper
    engine = get_postgres_engine()
    factory = get_session_factory()
    
    async with factory() as session:
        postgres_client = PostgresClient(session)
        
        return CentralStateManager(
            redis_client=redis_client,
            postgres_client=postgres_client
        )


# ============= LIFECYCLE =============

async def init_databases():
    """Initialize all database connections"""
    await get_redis_client()
    get_postgres_engine()
    logger.info("✅ All database connections initialized")


async def close_databases():
    """Close all database connections"""
    await close_redis()
    await close_postgres()
    logger.info("✅ All database connections closed")
