from neo4j import AsyncGraphDatabase, AsyncSession, AsyncResult
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    Neo4j client for knowledge graph management.
    
    Manages:
    - Course Knowledge Graph (shared, static)
      Nodes: Concepts, Prerequisites, Difficulty
      Relationships: requires, similar_to, is_subconcept_of
    
    - Personal Knowledge Graph (individual, dynamic)
      Nodes: User's notes, mastery levels, error patterns
      Relationships: learned_from, confused_with, struggling_with
    
    Uses neo4j AsyncGraphDatabase for async operations.
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j URI (bolt://localhost:7687)
            user: Username (default: neo4j)
            password: Password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.logger = logging.getLogger("Neo4jClient")
    
    async def connect(self) -> bool:
        """Create connection to Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connection
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            
            self.logger.info(f"✅ Connected to Neo4j at {self.uri}")
            await self._initialize_indexes()
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close connection"""
        if self.driver:
            await self.driver.close()
            self.logger.info("✅ Disconnected from Neo4j")
    
    async def _initialize_indexes(self) -> None:
        """Create indexes for better query performance"""
        async with self.driver.session() as session:
            # Course KG indexes
            await session.run(
                "CREATE INDEX course_concept_id IF NOT EXISTS "
                "FOR (c:CourseConcept) ON (c.concept_id)"
            )
            await session.run(
                "CREATE INDEX course_difficulty IF NOT EXISTS "
                "FOR (c:CourseConcept) ON (c.difficulty)"
            )
            
            # Personal KG indexes
            await session.run(
                "CREATE INDEX personal_learner_id IF NOT EXISTS "
                "FOR (n:PersonalNote) ON (n.learner_id)"
            )
            await session.run(
                "CREATE INDEX personal_concept_id IF NOT EXISTS "
                "FOR (n:PersonalNote) ON (n.concept_id)"
            )
            
            self.logger.info("✅ Indexes initialized")
    
    # ============= COURSE KG OPERATIONS =============
    
    async def create_course_concept(
        self,
        concept_id: str,
        name: str,
        difficulty: int,
        description: str = ""
    ) -> bool:
        """Create concept node in Course KG"""
        try:
            async with self.driver.session() as session:
                await session.run(
                    """
                    CREATE (c:CourseConcept {
                        concept_id: $concept_id,
                        name: $name,
                        difficulty: $difficulty,
                        description: $description
                    })
                    """,
                    concept_id=concept_id,
                    name=name,
                    difficulty=difficulty,
                    description=description
                )
            self.logger.debug(f"✅ Created concept: {concept_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Create concept failed: {e}")
            return False
    
    async def add_prerequisite(
        self,
        concept_id: str,
        prerequisite_id: str
    ) -> bool:
        """Add 'requires' relationship between concepts"""
        try:
            async with self.driver.session() as session:
                await session.run(
                    """
                    MATCH (c:CourseConcept {concept_id: $concept_id})
                    MATCH (p:CourseConcept {concept_id: $prerequisite_id})
                    CREATE (c)-[:REQUIRES]->(p)
                    """,
                    concept_id=concept_id,
                    prerequisite_id=prerequisite_id
                )
            self.logger.debug(f"✅ Added prerequisite: {concept_id} requires {prerequisite_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Add prerequisite failed: {e}")
            return False
    
    async def get_prerequisites(self, concept_id: str) -> List[Dict]:
        """Get all prerequisites for a concept"""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:CourseConcept {concept_id: $concept_id})
                    MATCH (c)-[:REQUIRES*1..3]->(p:CourseConcept)
                    RETURN DISTINCT p.concept_id as concept_id, 
                                    p.name as name,
                                    p.difficulty as difficulty
                    ORDER BY p.difficulty ASC
                    """,
                    concept_id=concept_id
                )
                records = await result.data()
                return [dict(record) for record in records]
        except Exception as e:
            self.logger.error(f"❌ Get prerequisites failed: {e}")
            return []
    
    async def get_alternative_concepts(self, concept_id: str) -> List[Dict]:
        """Get similar concepts (alternative learning paths)"""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:CourseConcept {concept_id: $concept_id})
                    MATCH (c)-[:SIMILAR_TO]-(alt:CourseConcept)
                    RETURN alt.concept_id as concept_id,
                           alt.name as name,
                           alt.difficulty as difficulty
                    """,
                    concept_id=concept_id
                )
                records = await result.data()
                return [dict(record) for record in records]
        except Exception as e:
            self.logger.error(f"❌ Get alternatives failed: {e}")
            return []
    
    # ============= PERSONAL KG OPERATIONS =============
    
    async def create_personal_note(
        self,
        learner_id: str,
        concept_id: str,
        note_content: str,
        note_id: str = None
    ) -> bool:
        """Create personal note in Personal KG"""
        try:
            async with self.driver.session() as session:
                await session.run(
                    """
                    CREATE (n:PersonalNote {
                        note_id: $note_id,
                        learner_id: $learner_id,
                        concept_id: $concept_id,
                        content: $note_content,
                        created_at: datetime()
                    })
                    """,
                    note_id=note_id or f"{learner_id}_{concept_id}_{int(__import__('time').time())}",
                    learner_id=learner_id,
                    concept_id=concept_id,
                    note_content=note_content
                )
            self.logger.debug(f"✅ Created note: {learner_id} → {concept_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Create note failed: {e}")
            return False
    
    async def get_personal_notes(
        self,
        learner_id: str,
        concept_id: str = None
    ) -> List[Dict]:
        """Get learner's personal notes"""
        try:
            async with self.driver.session() as session:
                if concept_id:
                    result = await session.run(
                        """
                        MATCH (n:PersonalNote {
                            learner_id: $learner_id,
                            concept_id: $concept_id
                        })
                        RETURN n.note_id as note_id,
                               n.content as content,
                               n.created_at as created_at
                        ORDER BY n.created_at DESC
                        """,
                        learner_id=learner_id,
                        concept_id=concept_id
                    )
                else:
                    result = await session.run(
                        """
                        MATCH (n:PersonalNote {learner_id: $learner_id})
                        RETURN n.note_id as note_id,
                               n.concept_id as concept_id,
                               n.content as content,
                               n.created_at as created_at
                        ORDER BY n.created_at DESC
                        """,
                        learner_id=learner_id
                    )
                records = await result.data()
                return [dict(record) for record in records]
        except Exception as e:
            self.logger.error(f"❌ Get notes failed: {e}")
            return []
    
    # ============= GENERIC OPERATIONS =============
    
    async def run_query(self, query: str, **params) -> List[Dict]:
        """Run arbitrary Cypher query"""
        try:
            async with self.driver.session() as session:
                result = await session.run(query, **params)
                records = await result.data()
                return [dict(record) for record in records]
        except Exception as e:
            self.logger.error(f"❌ Query failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check Neo4j connection health"""
        try:
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            return True
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return False
