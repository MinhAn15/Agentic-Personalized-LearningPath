from typing import Any, Dict, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class CentralStateManager:
    """
    Central State Manager for entire system.
    
    Responsibilities:
    - Maintain learner state (profile, progress, history)
    - Maintain agent state (intermediate results)
    - Provide atomic operations for consistency
    - Support time-series queries for history
    
    Storage layers:
    - Redis: Hot data (current session)
    - PostgreSQL: Cold data (history, persistence)
    """
    
    def __init__(self, redis_client, postgres_client):
        self.redis = redis_client
        self.postgres = postgres_client
        self.logger = logging.getLogger("StateManager")
    
    # ============= LEARNER STATE =============
    
    async def create_learner(self, learner_id: str, profile: Dict) -> bool:
        """Create new learner profile"""
        try:
            # Hot cache
            await self.redis.set(f"learner:{learner_id}", json.dumps(profile))
            
            # Cold storage
            await self.postgres.execute(
                """
                INSERT INTO learners (learner_id, profile, created_at)
                VALUES (%s, %s, %s)
                """,
                (learner_id, json.dumps(profile), datetime.now())
            )
            
            self.logger.info(f"✅ Created learner: {learner_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to create learner: {e}")
            return False
    
    async def get_learner(self, learner_id: str) -> Optional[Dict]:
        """Get learner profile (from cache if available)"""
        try:
            # Try hot cache first
            cached = await self.redis.get(f"learner:{learner_id}")
            if cached:
                return json.loads(cached)
            
            # Fall back to cold storage
            result = await self.postgres.fetch_one(
                "SELECT profile FROM learners WHERE learner_id = %s",
                (learner_id,)
            )
            if result:
                profile = json.loads(result['profile'])
                # Warm cache
                await self.redis.set(f"learner:{learner_id}", result['profile'])
                return profile
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to get learner: {e}")
            return None
    
    async def update_learner(self, learner_id: str, updates: Dict) -> bool:
        """Update learner profile (write-through to both caches)"""
        try:
            # Get current
            current = await self.get_learner(learner_id)
            if not current:
                return False
            
            # Merge updates
            updated = {**current, **updates}
            
            # Hot cache
            await self.redis.set(f"learner:{learner_id}", json.dumps(updated))
            
            # Cold storage
            await self.postgres.execute(
                "UPDATE learners SET profile = %s, updated_at = %s WHERE learner_id = %s",
                (json.dumps(updated), datetime.now(), learner_id)
            )
            
            self.logger.info(f"✅ Updated learner: {learner_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to update learner: {e}")
            return False
    
    # ============= LEARNER PROGRESS =============
    
    async def save_progress(
        self,
        learner_id: str,
        concept_id: str,
        mastery: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Save learner's mastery of a concept"""
        try:
            ts = timestamp or datetime.now()
            
            # Cold storage (historical)
            await self.postgres.execute(
                """
                INSERT INTO learner_progress 
                (learner_id, concept_id, mastery, timestamp)
                VALUES (%s, %s, %s, %s)
                """,
                (learner_id, concept_id, mastery, ts)
            )
            
            # Hot cache (current state)
            await self.redis.set(
                f"progress:{learner_id}:{concept_id}",
                mastery
            )
            
            self.logger.debug(f"✅ Saved progress: {learner_id} → {concept_id} = {mastery:.2f}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to save progress: {e}")
            return False
    
    async def get_progress(self, learner_id: str, concept_id: str) -> Optional[float]:
        """Get learner's mastery of a concept (from cache)"""
        try:
            cached = await self.redis.get(f"progress:{learner_id}:{concept_id}")
            if cached:
                return float(cached)
            
            # If not in cache, query DB
            result = await self.postgres.fetch_one(
                """
                SELECT mastery FROM learner_progress
                WHERE learner_id = %s AND concept_id = %s
                ORDER BY timestamp DESC LIMIT 1
                """,
                (learner_id, concept_id)
            )
            
            if result:
                mastery = result['mastery']
                await self.redis.set(f"progress:{learner_id}:{concept_id}", mastery)
                return mastery
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to get progress: {e}")
            return None
    
    # ============= LEARNING PATH =============
    
    async def save_learning_path(self, learner_id: str, path: list) -> bool:
        """Save the recommended learning path"""
        try:
            path_json = json.dumps(path)
            
            await self.redis.set(f"learning_path:{learner_id}", path_json)
            await self.postgres.execute(
                """
                INSERT INTO learning_paths (learner_id, path, created_at)
                VALUES (%s, %s, %s)
                """,
                (learner_id, path_json, datetime.now())
            )
            
            self.logger.info(f"✅ Saved learning path for {learner_id} ({len(path)} concepts)")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to save learning path: {e}")
            return False
    
    async def get_learning_path(self, learner_id: str) -> Optional[list]:
        """Get current learning path"""
        try:
            cached = await self.redis.get(f"learning_path:{learner_id}")
            if cached:
                return json.loads(cached)
            
            result = await self.postgres.fetch_one(
                """
                SELECT path FROM learning_paths
                WHERE learner_id = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (learner_id,)
            )
            
            if result:
                path = json.loads(result['path'])
                await self.redis.set(f"learning_path:{learner_id}", result['path'])
                return path
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to get learning path: {e}")
            return None
    
    # ============= GENERIC KEY-VALUE =============
    
    async def set(self, key: str, value: Any) -> bool:
        """Generic set (for agent state storage)"""
        try:
            value_str = json.dumps(value) if not isinstance(value, str) else value
            await self.redis.set(key, value_str)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to set {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Generic get (for agent state retrieval)"""
        try:
            value = await self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to get {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from state"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to delete {key}: {e}")
            return False
