# Neo4j Schema Setup for AuraDB Production
"""
Schema constraints and indexes for Course Knowledge Graph.
Run this once when setting up AuraDB or local Neo4j.

Usage:
    python -m backend.database.neo4j_schema
"""

import asyncio
import logging
from typing import List, Dict
from neo4j import AsyncGraphDatabase

from backend.config import get_settings

logger = logging.getLogger(__name__)


# ==========================================
# SCHEMA CONSTRAINTS (Uniqueness + Existence)
# ==========================================

CONSTRAINTS = [
    # ==========================================
    # DUAL-LAYER ID CONSTRAINTS
    # ==========================================
    # Unique constraint on CourseConcept.concept_id (= concept_code, business key)
    {
        "name": "unique_course_concept_id",
        "query": """
            CREATE CONSTRAINT unique_course_concept_id IF NOT EXISTS
            FOR (c:CourseConcept)
            REQUIRE c.concept_id IS UNIQUE
        """
    },
    # Unique constraint on CourseConcept.concept_uuid (internal GUID)
    {
        "name": "unique_course_concept_uuid",
        "query": """
            CREATE CONSTRAINT unique_course_concept_uuid IF NOT EXISTS
            FOR (c:CourseConcept)
            REQUIRE c.concept_uuid IS UNIQUE
        """
    },
    # Unique constraint on Learner.learner_id
    {
        "name": "unique_learner_id",
        "query": """
            CREATE CONSTRAINT unique_learner_id IF NOT EXISTS
            FOR (l:Learner)
            REQUIRE l.learner_id IS UNIQUE
        """
    },
    # Unique constraint on NoteNode.note_id
    {
        "name": "unique_note_id",
        "query": """
            CREATE CONSTRAINT unique_note_id IF NOT EXISTS
            FOR (n:NoteNode)
            REQUIRE n.note_id IS UNIQUE
        """
    },
    # Unique constraint on StagingConcept (for cleanup)
    {
        "name": "unique_staging_concept_id",
        "query": """
            CREATE CONSTRAINT unique_staging_concept_id IF NOT EXISTS
            FOR (s:StagingConcept)
            REQUIRE s.concept_id IS UNIQUE
        """
    },
    # ==========================================
    # PROVENANCE SUBGRAPH CONSTRAINTS
    # ==========================================
    # Unique constraint on SourceDocument.doc_id
    {
        "name": "unique_source_document_id",
        "query": """
            CREATE CONSTRAINT unique_source_document_id IF NOT EXISTS
            FOR (d:SourceDocument)
            REQUIRE d.doc_id IS UNIQUE
        """
    },
    # Unique constraint on ConceptSnapshot.snapshot_id
    {
        "name": "unique_concept_snapshot_id",
        "query": """
            CREATE CONSTRAINT unique_concept_snapshot_id IF NOT EXISTS
            FOR (s:ConceptSnapshot)
            REQUIRE s.snapshot_id IS UNIQUE
        """
    },
    # Unique constraint on RelSnapshot.snapshot_id
    {
        "name": "unique_rel_snapshot_id",
        "query": """
            CREATE CONSTRAINT unique_rel_snapshot_id IF NOT EXISTS
            FOR (s:RelSnapshot)
            REQUIRE s.snapshot_id IS UNIQUE
        """
    }
]

# ==========================================
# INDEXES (Performance)
# ==========================================

INDEXES = [
    # Full-text search on CourseConcept
    {
        "name": "idx_course_concept_name",
        "query": """
            CREATE INDEX idx_course_concept_name IF NOT EXISTS
            FOR (c:CourseConcept)
            ON (c.name)
        """
    },
    # Index on semantic_tags for filtering
    {
        "name": "idx_course_concept_tags",
        "query": """
            CREATE INDEX idx_course_concept_tags IF NOT EXISTS
            FOR (c:CourseConcept)
            ON (c.semantic_tags)
        """
    },
    # Index on source_document_ids for provenance queries
    {
        "name": "idx_course_concept_source",
        "query": """
            CREATE INDEX idx_course_concept_source IF NOT EXISTS
            FOR (c:CourseConcept)
            ON (c.source_document_ids)
        """
    },
    # Index on Learner for fast lookup
    {
        "name": "idx_learner_topic",
        "query": """
            CREATE INDEX idx_learner_topic IF NOT EXISTS
            FOR (l:Learner)
            ON (l.topic)
        """
    },
    # Composite index for mastery queries
    {
        "name": "idx_learner_skill_level",
        "query": """
            CREATE INDEX idx_learner_skill_level IF NOT EXISTS
            FOR (l:Learner)
            ON (l.skill_level)
        """
    }
]


class Neo4jSchemaManager:
    """
    Manage Neo4j schema constraints and indexes.
    
    Usage:
        manager = Neo4jSchemaManager()
        await manager.setup_schema()
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        settings = get_settings()
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self.driver = None
    
    async def connect(self):
        """Connect to Neo4j"""
        self.driver = AsyncGraphDatabase.driver(
            self.uri, 
            auth=(self.user, self.password)
        )
        logger.info(f"Connected to Neo4j: {self.uri}")
    
    async def close(self):
        """Close connection"""
        if self.driver:
            await self.driver.close()
    
    async def setup_schema(self) -> Dict[str, any]:
        """
        Set up all constraints and indexes.
        Idempotent - safe to run multiple times.
        """
        await self.connect()
        
        results = {
            "constraints_created": [],
            "constraints_skipped": [],
            "indexes_created": [],
            "indexes_skipped": [],
            "errors": []
        }
        
        try:
            async with self.driver.session() as session:
                # Create constraints
                for constraint in CONSTRAINTS:
                    try:
                        await session.run(constraint["query"])
                        results["constraints_created"].append(constraint["name"])
                        logger.info(f"✅ Created constraint: {constraint['name']}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            results["constraints_skipped"].append(constraint["name"])
                            logger.debug(f"⏭️ Constraint exists: {constraint['name']}")
                        else:
                            results["errors"].append(f"{constraint['name']}: {str(e)}")
                            logger.error(f"❌ Error creating constraint {constraint['name']}: {e}")
                
                # Create indexes
                for index in INDEXES:
                    try:
                        await session.run(index["query"])
                        results["indexes_created"].append(index["name"])
                        logger.info(f"✅ Created index: {index['name']}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            results["indexes_skipped"].append(index["name"])
                            logger.debug(f"⏭️ Index exists: {index['name']}")
                        else:
                            results["errors"].append(f"{index['name']}: {str(e)}")
                            logger.error(f"❌ Error creating index {index['name']}: {e}")
        
        finally:
            await self.close()
        
        return results
    
    async def drop_all_constraints(self) -> List[str]:
        """Drop all constraints (USE WITH CAUTION)"""
        await self.connect()
        dropped = []
        
        try:
            async with self.driver.session() as session:
                # Get existing constraints
                result = await session.run("SHOW CONSTRAINTS")
                constraints = await result.data()
                
                for constraint in constraints:
                    name = constraint.get("name")
                    if name:
                        try:
                            await session.run(f"DROP CONSTRAINT {name} IF EXISTS")
                            dropped.append(name)
                            logger.info(f"Dropped constraint: {name}")
                        except Exception as e:
                            logger.error(f"Error dropping {name}: {e}")
        
        finally:
            await self.close()
        
        return dropped
    
    async def show_schema(self) -> Dict[str, List]:
        """Show current schema"""
        await self.connect()
        schema = {"constraints": [], "indexes": []}
        
        try:
            async with self.driver.session() as session:
                # Get constraints
                result = await session.run("SHOW CONSTRAINTS")
                schema["constraints"] = await result.data()
                
                # Get indexes
                result = await session.run("SHOW INDEXES")
                schema["indexes"] = await result.data()
        
        finally:
            await self.close()
        
        return schema


async def main():
    """CLI entry point"""
    logging.basicConfig(level=logging.INFO)
    
    manager = Neo4jSchemaManager()
    
    print("🔧 Setting up Neo4j schema for AuraDB...")
    results = await manager.setup_schema()
    
    print("\n📊 Results:")
    print(f"  Constraints created: {len(results['constraints_created'])}")
    print(f"  Constraints skipped: {len(results['constraints_skipped'])}")
    print(f"  Indexes created: {len(results['indexes_created'])}")
    print(f"  Indexes skipped: {len(results['indexes_skipped'])}")
    
    if results["errors"]:
        print(f"\n❌ Errors: {results['errors']}")
    else:
        print("\n✅ Schema setup complete!")


if __name__ == "__main__":
    asyncio.run(main())
