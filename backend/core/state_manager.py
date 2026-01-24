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
            # Delegate serialization and TTL to RedisClient wrapper
            return await self.redis.set(key, value, ttl=ttl)
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
            # Delegate to RedisClient wrapper
            return await self.redis.get(key)
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
            return False

    # ============ DUAL-KG SYNC INTEGRATION ============
    
    def init_dual_kg(self, config=None):
        """Initialize Dual KG Manager if Neo4j is available"""
        from backend.core.dual_kg_manager import DualKGManager
        
        # Assumption: self.postgres and self.neo4j are available
        # But StateManager currently only takes postgres_client in __init__
        # We need to inject Neo4j client separately or change __init__
        if hasattr(self, 'neo4j') and self.neo4j:
            self.dual_kg = DualKGManager(self.neo4j, self.neo4j, config) # Using Neo4j driver for both for now
            self.logger.info("✅ DualKGManager initialized")
        else:
            self.logger.warning("⚠️ DualKGManager NOT initialized (Neo4j missing)")
            self.dual_kg = None

    async def on_learner_session_start(self, learner_id: str, course_id: str):
        """Called when learner starts a session"""
        if self.dual_kg:
            # Sync first thing
            sync_ok = await self.dual_kg.sync_learner_state(learner_id, course_id)
            if not sync_ok:
                self.logger.error(f"Failed to sync for {learner_id}, falling back to cache")

    async def on_agent_update_mastery(self, learner_id: str, concept_id: str, new_mastery: float, course_id: str = "unknown"):
        """Called when Evaluator updates mastery"""
        # Update in database/cache
        await self.update_learner_progress(learner_id, concept_id, new_mastery)
        
        # Trigger async sync if DualKG is active
        if self.dual_kg:
            import asyncio
            # Fire and forget sync
            asyncio.create_task(
                self.dual_kg.sync_learner_state(learner_id, course_id)
            )
