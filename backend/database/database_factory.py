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
        """Initialize all database connections"""
        try:
            self.logger.info("🔌 Initializing database connections...")
            
            # PostgreSQL
            self.postgres = PostgreSQLClient(self.settings.DATABASE_URL)
            if not await self.postgres.connect():
                self.logger.error("❌ PostgreSQL connection failed")
                return False
            
            # Neo4j
            self.neo4j = Neo4jClient(
                self.settings.NEO4J_URI,
                self.settings.NEO4J_USER,
                self.settings.NEO4J_PASSWORD
            )
            if not await self.neo4j.connect():
                self.logger.error("❌ Neo4j connection failed")
                return False
            
            # Redis
            self.redis = RedisClient(self.settings.REDIS_URL)
            if not await self.redis.connect():
                self.logger.error("❌ Redis connection failed")
                return False
            
            self.logger.info("✅ All databases connected successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
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
