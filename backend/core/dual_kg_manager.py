from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class SyncStrategy(Enum):
    """How to handle sync conflicts"""
    COURSE_KG_WINS = "overwrite"  # Trust Course KG as source of truth
    PERSONAL_KG_WINS = "preserve"  # Keep personal modifications
    MERGE = "merge"  # Combine both (advanced)

class DualKGManager:
    """
    Manages synchronization between Course KG and Personal KG.
    
    CRITICAL INVARIANTS:
    1. Course KG is source of truth for course structure
    2. Personal KG adds learner-specific annotations (mastery, errors, notes)
    3. Sync must be idempotent (sync twice = sync once)
    4. Sync must not block learner interactions (async, with timeout)
    """
    
    def __init__(self, course_kg_driver, personal_kg_driver, config=None):
        self.course_kg = course_kg_driver
        self.personal_kg = personal_kg_driver
        self.config = config or {}
        self.sync_strategy = SyncStrategy.COURSE_KG_WINS
        self.sync_timeout_sec = 5  # Max time for sync operation
        self.max_retries = 3
        self.last_sync_time: Dict[str, datetime] = {}
        
    async def sync_learner_state(
        self, 
        learner_id: str, 
        course_id: str,
        max_retries: int = None
    ) -> bool:
        """
        Synchronize learner state between Course KG and Personal KG.
        
        ALGORITHM:
        1. Fetch all concept nodes from Course KG for this course
        2. For each concept, check if exists in Personal KG
        3. If missing in Personal KG: CREATE with default mastery=0
        4. If exists: UPDATE mastery, error_history, last_seen
        5. Handle conflicts per sync_strategy
        6. Return success/failure
        
        Args:
            learner_id: Unique learner identifier
            course_id: Course/topic identifier
            max_retries: Override default retry count
            
        Returns:
            bool: True if sync successful, False if failed after retries
            
        Raises:
            asyncio.TimeoutError: If sync exceeds timeout
        """
        max_retries = max_retries or self.max_retries
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # With timeout to prevent blocking
                await asyncio.wait_for(
                    self._sync_internal(learner_id, course_id),
                    timeout=self.sync_timeout_sec
                )
                logger.debug(f"✓ Sync successful: learner={learner_id}, course={course_id}")
                self.last_sync_time[f"{learner_id}:{course_id}"] = datetime.now()
                return True
                
            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(
                    f"⚠ Sync timeout (attempt {retry_count}/{max_retries}): "
                    f"learner={learner_id}, course={course_id}"
                )
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                    
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"❌ Sync error (attempt {retry_count}/{max_retries}): {e}"
                )
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)
        
        logger.critical(f"❌ Sync failed after {max_retries} retries: learner={learner_id}")
        return False
    
    async def _sync_internal(self, learner_id: str, course_id: str) -> None:
        """
        Internal sync logic (called by sync_learner_state with timeout wrapper).
        
        DETAILED STEPS:
        1. Fetch Course KG concepts for this course
        2. Fetch existing Personal KG nodes for learner + course
        3. Compute set difference (new concepts, deleted concepts, modified concepts)
        4. Apply changes per strategy
        5. Update PersonalKG nodes with learner metadata
        """
        # Step 1: Fetch all concepts from Course KG for this course
        course_concepts = await self._fetch_course_concepts(course_id)
        # logger.debug(f"Course KG has {len(course_concepts)} concepts")
        
        # Step 2: Fetch existing Personal KG nodes
        personal_concepts = await self._fetch_personal_concepts(learner_id, course_id)
        # logger.debug(f"Personal KG has {len(personal_concepts)} nodes for this learner+course")
        
        # Step 3: Compute differences
        course_concept_ids = set(c['id'] for c in course_concepts)
        personal_concept_ids = set(p['id'] for p in personal_concepts)
        
        new_concept_ids = course_concept_ids - personal_concept_ids  # In course, not in personal
        deleted_concept_ids = personal_concept_ids - course_concept_ids  # In personal, not in course
        existing_concept_ids = course_concept_ids & personal_concept_ids  # In both
        
        # logger.debug(
        #     f"Sync delta: +{len(new_concept_ids)} new, "
        #     f"-{len(deleted_concept_ids)} deleted, "
        #     f"~{len(existing_concept_ids)} existing"
        # )
        
        # Step 4a: Create new Personal KG nodes for new concepts
        for concept_id in new_concept_ids:
            try:
                concept = next(c for c in course_concepts if c['id'] == concept_id)
                await self._create_personal_node(learner_id, concept, course_id)
            except Exception as e:
                logger.error(f"Failed to create personal node {concept_id}: {e}")
        
        # Step 4b: Mark deleted concepts (soft delete or remove)
        for concept_id in deleted_concept_ids:
            try:
                await self._handle_deleted_concept(learner_id, concept_id)
            except Exception as e:
                logger.error(f"Failed to handle deleted concept {concept_id}: {e}")
        
        # Step 4c: Update existing nodes with latest metadata from Course KG
        for concept_id in existing_concept_ids:
            try:
                course_concept = next(c for c in course_concepts if c['id'] == concept_id)
                await self._update_personal_node(learner_id, course_concept)
            except Exception as e:
                logger.error(f"Failed to update personal node {concept_id}: {e}")

    async def _fetch_course_concepts(self, course_id: str) -> List[Dict[str, Any]]:
        """Fetch all concept nodes for a course from Course KG"""
        # This assumes Neo4j or similar. course_kg_driver must implement execute_query or arun
        query = """
        MATCH (course:Course {id: $course_id})-[:HAS_CONCEPT*]->(concept:Concept)
        RETURN DISTINCT concept.id as id, concept.name as name, concept.definition as definition
        """
        try:
             # Use the driver's method. Assuming Neo4jHelper style.
            result = await self.course_kg.execute_read(query, {"course_id": course_id})
            return result
        except Exception as e:
            # Fallback if no direct relationships, try finding all concepts connected to course root
            return []
    
    async def _fetch_personal_concepts(self, learner_id: str, course_id: str) -> List[Dict[str, Any]]:
        """Fetch Personal KG nodes for this learner + course"""
        query = """
        MATCH (learner:Learner {id: $learner_id})-[:STUDIES]->(course:Course {id: $course_id})
        MATCH (learner)-[:HAS_STATE]->(state:ConceptState)-[:FOR_CONCEPT]->(concept:Concept)
        WHERE (course)-[:HAS_CONCEPT*]->(concept)
        RETURN DISTINCT concept.id as id, state.mastery as mastery, state.last_updated as last_updated
        """
        try:
            result = await self.personal_kg.execute_read(query, {"learner_id": learner_id, "course_id": course_id})
            return result
        except Exception as e:
            return []

    async def _create_personal_node(self, learner_id: str, concept: Dict[str, Any], course_id: str) -> None:
        """Create new Personal KG node for a concept learner hasn't seen"""
        # Assuming we need to create a ConceptState node linked to Learner and Concept
        query = """
        MERGE (learner:Learner {id: $learner_id})
        MERGE (concept:Concept {id: $concept_id})
        MERGE (learner)-[:HAS_STATE]->(state:ConceptState {id: $learner_id + '_' + $concept_id})
        ON CREATE SET 
            state.mastery = 0.0,
            state.error_history = [],
            state.attempts = 0,
            state.created_at = datetime(),
            state.last_updated = datetime()
        MERGE (state)-[:FOR_CONCEPT]->(concept)
        """
        await self.personal_kg.execute_write(
            query,
            {
                "learner_id": learner_id,
                "concept_id": concept['id'],
                "course_id": course_id,
                "concept_name": concept.get('name', 'Unknown')
            }
        )
    
    async def _update_personal_node(self, learner_id: str, concept: Dict[str, Any]) -> None:
        """Update Personal KG node with latest Course KG metadata"""
        # In practice, usually name/def are on the Concept node, which strictly belongs to Course KG.
        # But if ConceptState caches name for speed, update it here.
        # For this design, ConceptState links to Concept, so limited redundancy.
        # We might update a 'synced_at' timestamp.
        query = """
        MATCH (learner:Learner {id: $learner_id})-[:HAS_STATE]->(state:ConceptState)-[:FOR_CONCEPT]->(concept:Concept {id: $concept_id})
        SET state.synced_at = datetime()
        RETURN state
        """
        await self.personal_kg.execute_write(
            query,
            {
                "concept_id": concept['id'],
                "learner_id": learner_id
            }
        )
    
    async def _handle_deleted_concept(self, learner_id: str, concept_id: str) -> None:
        """Handle deleted concept (soft delete with archive)"""
        if self.sync_strategy == SyncStrategy.PERSONAL_KG_WINS:
            # Keep it, just mark as archived
            query = """
            MATCH (learner:Learner {id: $learner_id})-[:HAS_STATE]->(state:ConceptState)-[:FOR_CONCEPT]->(concept:Concept {id: $concept_id})
            SET state.archived = true, state.archived_at = datetime()
            """
        else:  # COURSE_KG_WINS
            # Remove from Personal KG (The ConceptState, not the Concept itself)
            query = """
             MATCH (learner:Learner {id: $learner_id})-[:HAS_STATE]->(state:ConceptState)-[:FOR_CONCEPT]->(concept:Concept {id: $concept_id})
            DETACH DELETE state
            """
        await self.personal_kg.execute_write(query, {"concept_id": concept_id, "learner_id": learner_id})
