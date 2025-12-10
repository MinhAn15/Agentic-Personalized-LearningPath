from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class CentralStateManager:
    """
    Central state manager for multi-agent system.
    
    Manages:
    - Shared state across all agents (via Redis)
    - Learner profiles and progress
    - Learning paths and recommendations
    - Agent execution state
    """
    
    def __init__(self, redis_client, postgres_client):
        """
        Initialize state manager.
        
        Args:
            redis_client: Redis client for fast state access
            postgres_client: PostgreSQL client for persistent state
        """
        self.redis = redis_client
        self.postgres = postgres_client
        self.logger = logging.getLogger(__name__)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in Redis cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiry)
            
        Returns:
            True if successful
        """
        try:
            if isinstance(value, dict):
                value = json.dumps(value)
            
            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to set state {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            self.logger.error(f"Failed to get state {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from Redis cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete state {key}: {e}")
            return False
    
    async def get_learner_profile(self, learner_id: str) -> Optional[Dict[str, Any]]:
        """
        Get learner profile from cache or database.
        
        Args:
            learner_id: Learner ID
            
        Returns:
            Learner profile dict or None
        """
        # Try cache first
        profile = await self.get(f"profile:{learner_id}")
        if profile:
            return profile
        
        # Fall back to database
        try:
            profile = await self.postgres.get_learner(learner_id)
            if profile:
                # Cache for future access (1 hour TTL)
                await self.set(f"profile:{learner_id}", profile, ttl=3600)
            return profile
        except Exception as e:
            self.logger.error(f"Failed to get learner profile {learner_id}: {e}")
            return None
    
    async def update_learner_progress(
        self,
        learner_id: str,
        concept_id: str,
        mastery_level: float
    ) -> bool:
        """
        Update learner's mastery of a concept.
        
        Args:
            learner_id: Learner ID
            concept_id: Concept ID
            mastery_level: New mastery level (0-1)
            
        Returns:
            True if successful
        """
        try:
            # Update in database
            success = await self.postgres.save_progress(
                learner_id,
                concept_id,
                mastery_level
            )
            
            if success:
                # Invalidate cache
                await self.delete(f"progress:{learner_id}")
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to update progress: {e}")
            return False
