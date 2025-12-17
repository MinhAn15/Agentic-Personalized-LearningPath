"""
Knowledge Graph Synchronizer for KAG Agent.

Per THESIS Section 3.5.5:
- Dual-KG: Layer 1 (Course) ↔ Layer 2 (Personal Notes) ↔ Layer 3 (Progress)
- NoteNode creation with REFERENCES to CourseConcept
- LINKSTO relationships for knowledge network
- MasteryNode updates in Layer 3
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KGSynchronizer:
    """
    Synchronize Dual-KG layers:
    - Layer 1: Course KG (read-only reference)
    - Layer 2: Personal Notes KG (NoteNodes, LINKSTO)
    - Layer 3: Progress KG (MasteryNodes, SessionNodes)
    """
    
    def __init__(self, neo4j_driver=None):
        self.neo4j = neo4j_driver
        self.logger = logging.getLogger(f"{__name__}.KGSynchronizer")
    
    async def sync_note_to_kg(self, note: Dict, learner_id: str) -> bool:
        """
        Create NoteNode in Personal KG (Layer 2) and links.
        
        Creates:
        - NoteNode with Zettelkasten fields
        - (Learner)-[:CREATED_NOTE]->(NoteNode)
        - (NoteNode)-[:ABOUT]->(CourseConcept)
        
        Returns: success bool
        """
        if not self.neo4j:
            self.logger.warning("No Neo4j driver available, skipping KG sync")
            return True  # Soft fail
        
        try:
            # Step 1: Create NoteNode
            create_query = """
            CREATE (n:NoteNode {
                note_id: $note_id,
                learner_id: $learner_id,
                concept_id: $concept_id,
                type: $type,
                title: $title,
                content: $content,
                key_insight: $key_insight,
                personal_example: $personal_example,
                common_mistake: $common_mistake,
                tags: $tags,
                created_at: datetime(),
                review_count: 0
            })
            RETURN n.note_id as note_id
            """
            
            await self.neo4j.run_query(
                create_query,
                note_id=note.get('note_id'),
                learner_id=learner_id,
                concept_id=note.get('concept_id', ''),
                type=note.get('type', 'ATOMIC_NOTE'),
                title=note.get('title', ''),
                content=note.get('content', ''),
                key_insight=note.get('key_insight', ''),
                personal_example=note.get('personal_example', ''),
                common_mistake=note.get('common_mistake', ''),
                tags=note.get('tags', [])
            )
            
            # Step 2: Link Learner → Note
            link_learner_query = """
            MATCH (l:Learner {learner_id: $learner_id})
            MATCH (n:NoteNode {note_id: $note_id})
            MERGE (l)-[:CREATED_NOTE]->(n)
            """
            await self.neo4j.run_query(
                link_learner_query,
                learner_id=learner_id,
                note_id=note.get('note_id')
            )
            
            # Step 3: Link Note → Concept (ABOUT)
            link_concept_query = """
            MATCH (n:NoteNode {note_id: $note_id})
            MATCH (c:CourseConcept {concept_id: $concept_id})
            MERGE (n)-[:ABOUT]->(c)
            """
            await self.neo4j.run_query(
                link_concept_query,
                note_id=note.get('note_id'),
                concept_id=note.get('concept_id')
            )
            
            # Step 4: Link to SessionNode if available
            session_id = note.get('source_session_id')
            if session_id:
                session_query = """
                MATCH (n:NoteNode {note_id: $note_id})
                MERGE (s:SessionNode {session_id: $session_id})
                MERGE (n)-[:DERIVED_FROM]->(s)
                """
                await self.neo4j.run_query(
                    session_query,
                    note_id=note.get('note_id'),
                    session_id=session_id
                )
            
            self.logger.info(f"Synced note {note.get('note_id')} to KG")
            return True
        
        except Exception as e:
            self.logger.exception(f"Error syncing note to KG: {e}")
            return False
    
    async def link_related_notes(
        self, 
        note_id: str, 
        learner_id: str,
        related_concept_ids: List[str],
        similarity_threshold: float = 0.75
    ) -> int:
        """
        Create LINKSTO relationships to related notes in Personal KG.
        
        Returns: number of links created
        """
        if not self.neo4j:
            return 0
        
        try:
            link_count = 0
            
            for related_concept in related_concept_ids:
                link_query = """
                MATCH (n1:NoteNode {note_id: $note_id})
                MATCH (l:Learner {learner_id: $learner_id})-[:CREATED_NOTE]->(n2:NoteNode)
                MATCH (n2)-[:ABOUT]->(c:CourseConcept {concept_id: $concept_id})
                WHERE n1.note_id <> n2.note_id
                  AND NOT (n1)-[:LINKSTO]->(n2)
                CREATE (n1)-[:LINKSTO]->(n2)
                RETURN count(*) as created
                """
                
                result = await self.neo4j.run_query(
                    link_query,
                    note_id=note_id,
                    learner_id=learner_id,
                    concept_id=related_concept
                )
                
                if result and len(result) > 0:
                    link_count += result[0].get('created', 0)
            
            self.logger.info(f"Created {link_count} LINKSTO relationships for {note_id}")
            return link_count
        
        except Exception as e:
            self.logger.exception(f"Error linking notes: {e}")
            return 0
    
    async def update_mastery_node(
        self, 
        learner_id: str, 
        concept_id: str,
        mastery_level: float, 
        bloom_level: str
    ) -> bool:
        """
        Update or create MasteryNode in Layer 3.
        
        Creates:
        - MasteryNode with level and bloom
        - (Learner)-[:HAS_MASTERY]->(MasteryNode)
        - (MasteryNode)-[:OF]->(CourseConcept)
        """
        if not self.neo4j:
            return True  # Soft fail
        
        try:
            query = """
            MATCH (l:Learner {learner_id: $learner_id})
            MATCH (c:CourseConcept {concept_id: $concept_id})
            MERGE (m:MasteryNode {learner_id: $learner_id, concept_id: $concept_id})
            SET m.mastery_level = $mastery_level,
                m.bloom_level = $bloom_level,
                m.updated_at = datetime(),
                m.attempt_count = COALESCE(m.attempt_count, 0) + 1
            MERGE (l)-[:HAS_MASTERY]->(m)
            MERGE (m)-[:OF]->(c)
            RETURN m.concept_id as updated
            """
            
            await self.neo4j.run_query(
                query,
                learner_id=learner_id,
                concept_id=concept_id,
                mastery_level=mastery_level,
                bloom_level=bloom_level
            )
            
            self.logger.debug(f"Updated mastery for {learner_id}/{concept_id}: {mastery_level:.2f}")
            return True
        
        except Exception as e:
            self.logger.exception(f"Error updating mastery node: {e}")
            return False
    
    async def update_error_pattern(
        self, 
        learner_id: str, 
        concept_id: str,
        error_data: Dict
    ) -> bool:
        """
        Track error patterns in Layer 3 for analytics.
        
        Creates/updates ErrorPatternNode linked to Learner and Concept.
        """
        if not self.neo4j:
            return True
        
        try:
            query = """
            MATCH (l:Learner {learner_id: $learner_id})
            MATCH (c:CourseConcept {concept_id: $concept_id})
            MERGE (e:ErrorPatternNode {
                learner_id: $learner_id, 
                concept_id: $concept_id,
                error_type: $error_type
            })
            SET e.frequency = COALESCE(e.frequency, 0) + 1,
                e.last_seen = datetime(),
                e.severity = $severity
            MERGE (l)-[:HAS_ERROR]->(e)
            MERGE (e)-[:ABOUT]->(c)
            """
            
            await self.neo4j.run_query(
                query,
                learner_id=learner_id,
                concept_id=concept_id,
                error_type=error_data.get('type', 'unknown'),
                severity=error_data.get('severity', 'MEDIUM')
            )
            
            return True
        
        except Exception as e:
            self.logger.exception(f"Error updating error pattern: {e}")
            return False
    
    # ==========================================
    # PKM QUERY SUPPORT (4 Query Types)
    # ==========================================
    
    async def query_temporal(self, learner_id: str, days: int = 7) -> List[Dict]:
        """
        Temporal Query: What notes did I create this week?
        """
        if not self.neo4j:
            return []
        
        query = """
        MATCH (l:Learner {learner_id: $learner_id})-[:CREATED_NOTE]->(n:NoteNode)
        WHERE n.created_at > datetime() - duration({days: $days})
        RETURN n.note_id as note_id, n.title as title, 
               n.concept_id as concept_id, n.created_at as created_at
        ORDER BY n.created_at DESC
        """
        
        result = await self.neo4j.run_query(query, learner_id=learner_id, days=days)
        return result if result else []
    
    async def query_retrieval(self, learner_id: str, concept_id: str) -> List[Dict]:
        """
        Retrieval Query: All my notes about concept X?
        """
        if not self.neo4j:
            return []
        
        query = """
        MATCH (l:Learner {learner_id: $learner_id})-[:CREATED_NOTE]->(n:NoteNode)
        MATCH (n)-[:ABOUT]->(c:CourseConcept {concept_id: $concept_id})
        RETURN n.note_id as note_id, n.title as title, 
               n.key_insight as key_insight, n.created_at as created_at
        ORDER BY n.created_at DESC
        """
        
        result = await self.neo4j.run_query(
            query, learner_id=learner_id, concept_id=concept_id
        )
        return result if result else []
    
    async def query_synthesis(self, learner_id: str) -> List[Dict]:
        """
        Synthesis Query: Most connected concepts in my notes?
        """
        if not self.neo4j:
            return []
        
        query = """
        MATCH (l:Learner {learner_id: $learner_id})-[:CREATED_NOTE]->(n1:NoteNode)
        MATCH (n1)-[:LINKSTO]->(n2:NoteNode)
        MATCH (n2)-[:ABOUT]->(c:CourseConcept)
        RETURN c.concept_id as concept_id, count(*) as connection_count
        ORDER BY connection_count DESC
        LIMIT 10
        """
        
        result = await self.neo4j.run_query(query, learner_id=learner_id)
        return result if result else []
    
    async def query_review(self, learner_id: str, mastery_threshold: float = 0.6) -> List[Dict]:
        """
        Review Query: Notes for concepts I'm struggling with?
        """
        if not self.neo4j:
            return []
        
        query = """
        MATCH (l:Learner {learner_id: $learner_id})-[:HAS_MASTERY]->(m:MasteryNode)
        WHERE m.mastery_level < $threshold
        MATCH (l)-[:CREATED_NOTE]->(n:NoteNode)-[:ABOUT]->(c:CourseConcept)
        WHERE c.concept_id = m.concept_id
        RETURN n.note_id as note_id, n.title as title,
               m.mastery_level as mastery, c.concept_id as concept_id
        ORDER BY m.mastery_level ASC
        """
        
        result = await self.neo4j.run_query(
            query, learner_id=learner_id, threshold=mastery_threshold
        )
        return result if result else []
