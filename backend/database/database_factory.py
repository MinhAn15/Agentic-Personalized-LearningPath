from typing import Dict
import logging

from .postgres_client import PostgreSQLClient
from .neo4j_client import Neo4jClient
from .redis_client import RedisClient
from backend.config import get_settings

logger = logging.getLogger(__name__)

class DatabaseFactory:
    """
    Factory for creating and managing database clients.
    
    Handles:
    - Initialization of all database clients
    - Connection pooling
    - Health checks
    - Graceful shutdown
    
    Usage:
        factory = DatabaseFactory()
        await factory.initialize()
        
        postgres = factory.postgres
        neo4j = factory.neo4j
        redis = factory.redis
        
        await factory.health_check()
        await factory.shutdown()
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.postgres = None
        self.neo4j = None
        self.redis = None
        self.logger = logging.getLogger("DatabaseFactory")
    
    async def initialize(self) -> bool:
        """Initialize all database connections with retry logic"""
        import asyncio
        max_retries = 30  # Increased to 30 for stability
        retry_delay = 2   # seconds

        for attempt in range(max_retries):
            try:
                self.logger.info(f"🔌 Initializing database connections (Attempt {attempt + 1}/{max_retries})...")
                
                # PostgreSQL
                if not self.postgres:
                     self.postgres = PostgreSQLClient(self.settings.DATABASE_URL)
                
                # Try Postgres first
                pg_connected = await self.postgres.connect()
                
                # Neo4j
                if not self.neo4j:
                    self.neo4j = Neo4jClient(
                        self.settings.NEO4J_URI,
                        self.settings.NEO4J_USER,
                        self.settings.NEO4J_PASSWORD
                    )
                neo4j_connected = await self.neo4j.connect()

                # Redis
                if not self.redis:
                    self.redis = RedisClient(self.settings.REDIS_URL)
                redis_connected = await self.redis.connect()
                
                if pg_connected and neo4j_connected and redis_connected:
                    self.logger.info("✅ All databases connected successfully")
                    return True
                else:
                    self.logger.warning(f"⚠️ Connection failed (PG: {pg_connected}, Neo4j: {neo4j_connected}, Redis: {redis_connected}). Retrying in {retry_delay}s...")
                    # Close failed connections to reset state
                    if not pg_connected: await self.postgres.disconnect()
                    if not neo4j_connected: await self.neo4j.disconnect()
                    if not redis_connected: await self.redis.disconnect()
                    
                    await asyncio.sleep(retry_delay)
            
            except Exception as e:
                self.logger.error(f"❌ Initialization error attempt {attempt + 1}: {e}")
                await asyncio.sleep(retry_delay)
        
        return False
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all databases"""
        try:
            results = {
                "postgres": await self.postgres.health_check() if self.postgres else False,
                "neo4j": await self.neo4j.health_check() if self.neo4j else False,
                "redis": await self.redis.health_check() if self.redis else False
            }
            
            all_healthy = all(results.values())
            status = "✅ All healthy" if all_healthy else "⚠️ Some issues"
            self.logger.info(f"{status}: {results}")
            
            return results
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return {"postgres": False, "neo4j": False, "redis": False}
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all connections"""
        try:
            self.logger.info("🛑 Shutting down databases...")
            
            if self.postgres:
                await self.postgres.disconnect()
            if self.neo4j:
                await self.neo4j.disconnect()
            if self.redis:
                await self.redis.disconnect()
            
            self.logger.info("✅ All databases disconnected")
        except Exception as e:
            self.logger.error(f"❌ Shutdown failed: {e}")

# Global factory instance
_factory = None

def get_factory() -> DatabaseFactory:
    """Get or create global factory instance"""
    global _factory
    if _factory is None:
        _factory = DatabaseFactory()
    return _factory

async def initialize_databases() -> bool:
    """Initialize all databases (for app startup)"""
    factory = get_factory()
    return await factory.initialize()

async def shutdown_databases() -> None:
    """Shutdown all databases (for app shutdown)"""
    factory = get_factory()
    await factory.shutdown()
