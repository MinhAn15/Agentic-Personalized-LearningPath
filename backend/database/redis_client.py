import redis.asyncio as redis
from typing import Optional, Any, Dict
import json
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Redis client for caching and session management.
    
    Use cases:
    - Cache learner profiles (TTL: 5 min)
    - Cache learning paths (TTL: 1 hour)
    - Cache KG query results (TTL: varies)
    - Store active sessions
    - Rate limiting
    
    All values JSON-serialized for type safety.
    """
    
    def __init__(self, url: str):
        """
        Initialize Redis client.
        
        Args:
            url: Redis URL (redis://localhost:6379)
        """
        self.url = url
        self.client = None
        self.logger = logging.getLogger("RedisClient")
    
    async def connect(self) -> bool:
        """Create Redis connection"""
        try:
            self.client = await redis.from_url(self.url)
            # Verify connection
            await self.client.ping()
            self.logger.info(f"✅ Connected to Redis at {self.url}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close connection"""
        if self.client:
            await self.client.close()
            self.logger.info("✅ Disconnected from Redis")
    
    # ============= CACHE OPERATIONS =============
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = 300  # Default 5 minutes
    ) -> bool:
        """Set key-value with TTL"""
        try:
            # JSON serialize
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, default=str)
            else:
                value_str = str(value)
            
            if ttl:
                await self.client.setex(key, ttl, value_str)
            else:
                await self.client.set(key, value_str)
            self.logger.debug(f"✅ Set {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            self.logger.error(f"❌ Set failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        try:
            value = await self.client.get(key)
            if value:
                # Try JSON decode
                try:
                    return json.loads(value)
                except:
                    return value.decode() if isinstance(value, bytes) else value
            return None
        except Exception as e:
            self.logger.error(f"❌ Get failed: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            await self.client.delete(key)
            self.logger.debug(f"✅ Deleted {key}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Delete failed: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            self.logger.error(f"❌ Exists check failed: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL in seconds (-1 = no expiry, -2 = doesn't exist)"""
        try:
            return await self.client.ttl(key)
        except Exception as e:
            self.logger.error(f"❌ TTL check failed: {e}")
            return -2
    
    # ============= SESSION OPERATIONS =============
    
    async def create_session(self, session_id: str, data: Dict, ttl: int = 3600) -> bool:
        """Create session with data"""
        return await self.set(f"session:{session_id}", data, ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        return await self.get(f"session:{session_id}")
    
    async def update_session(self, session_id: str, data: Dict, ttl: int = 3600) -> bool:
        """Update session (reset TTL)"""
        return await self.set(f"session:{session_id}", data, ttl)
    
    async def destroy_session(self, session_id: str) -> bool:
        """Delete session"""
        return await self.delete(f"session:{session_id}")
    
    # ============= COUNTER OPERATIONS (for rate limiting) =============
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"❌ Increment failed: {e}")
            return 0
    
    async def set_rate_limit(self, key: str, max_requests: int, window: int) -> bool:
        """Set rate limit (max_requests in window seconds)"""
        try:
            current = await self.increment(key)
            if current == 1:
                await self.client.expire(key, window)
            
            if current > max_requests:
                self.logger.warning(f"⚠️ Rate limit exceeded: {key}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"❌ Rate limit check failed: {e}")
            return False
    
    # ============= GENERIC OPERATIONS =============
    
    async def flushdb(self) -> bool:
        """Clear all keys in database (CAREFUL!)"""
        try:
            await self.client.flushdb()
            self.logger.warning("⚠️ Flushed all Redis keys")
            return True
        except Exception as e:
            self.logger.error(f"❌ Flush failed: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return False
