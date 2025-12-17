# Batch Upsert Utility for Neo4j AuraDB
"""
Batch upsert using UNWIND for efficient Neo4j ingestion.
Designed for AuraDB production with high throughput.

Key Features:
- UNWIND $batch for single-query batch operations
- Provenance tracking with source_document_ids list
- Idempotent MERGE operations
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Neo4jBatchUpserter:
    """
    Batch upsert utility for Neo4j.
    
    Uses UNWIND pattern for efficient bulk operations:
    - Single query per batch (not per record)
    - Supports provenance tracking
    - Idempotent MERGE operations
    
    Usage:
        upserter = Neo4jBatchUpserter(neo4j_client)
        result = await upserter.upsert_concepts(concepts, document_id)
    """
    
    # Batch size for UNWIND operations
    DEFAULT_BATCH_SIZE = 100
    
    def __init__(self, neo4j_client, batch_size: int = None):
        """
        Initialize batch upserter.
        
        Args:
            neo4j_client: Neo4j async client with run_query method
            batch_size: Number of records per batch (default: 100)
        """
        self.neo4j = neo4j_client
        self.batch_size = batch_size or self.DEFAULT_BATCH_SIZE
    
    async def upsert_concepts(
        self,
        concepts: List[Dict[str, Any]],
        source_document_id: str
    ) -> Dict[str, Any]:
        """
        Batch upsert concepts with provenance tracking.
        
        Provenance: source_document_ids is a LIST that accumulates
        all documents that contributed to this concept.
        
        Args:
            concepts: List of concept dictionaries
            source_document_id: Document ID for provenance
            
        Returns:
            Dict with upserted count and stats
        """
        if not concepts:
            return {"upserted": 0, "batches": 0}
        
        total_upserted = 0
        batch_count = 0
        
        # Process in batches
        for i in range(0, len(concepts), self.batch_size):
            batch = concepts[i:i + self.batch_size]
            
            # Prepare batch data
            batch_data = []
            for concept in batch:
                batch_data.append({
                    "concept_id": concept.get("concept_id"),
                    "name": concept.get("name", ""),
                    "description": concept.get("description", ""),
                    "difficulty": concept.get("difficulty", 2),
                    "bloom_level": concept.get("bloom_level", "UNDERSTAND"),
                    "time_estimate": concept.get("time_estimate", 30),
                    "semantic_tags": concept.get("semantic_tags", []),
                    "focused_tags": concept.get("focused_tags", []),
                    "learning_objective": concept.get("learning_objective", ""),
                    "examples": concept.get("examples", []),
                    "extraction_version": concept.get("extraction_version", "v3"),
                    "source_document_id": source_document_id
                })
            
            # UNWIND batch upsert with provenance list
            query = """
            UNWIND $batch AS row
            MERGE (c:CourseConcept {concept_id: row.concept_id})
            ON CREATE SET
                c.name = row.name,
                c.description = row.description,
                c.difficulty = row.difficulty,
                c.bloom_level = row.bloom_level,
                c.time_estimate = row.time_estimate,
                c.semantic_tags = row.semantic_tags,
                c.focused_tags = row.focused_tags,
                c.learning_objective = row.learning_objective,
                c.examples = row.examples,
                c.extraction_version = row.extraction_version,
                c.source_document_ids = [row.source_document_id],
                c.created_at = datetime(),
                c.updated_at = datetime()
            ON MATCH SET
                c.name = row.name,
                c.description = row.description,
                c.difficulty = row.difficulty,
                c.bloom_level = row.bloom_level,
                c.time_estimate = row.time_estimate,
                c.semantic_tags = row.semantic_tags,
                c.focused_tags = row.focused_tags,
                c.learning_objective = row.learning_objective,
                c.examples = row.examples,
                c.extraction_version = row.extraction_version,
                c.source_document_ids = CASE 
                    WHEN row.source_document_id IN c.source_document_ids 
                    THEN c.source_document_ids 
                    ELSE c.source_document_ids + row.source_document_id 
                END,
                c.updated_at = datetime()
            RETURN count(c) AS upserted
            """
            
            try:
                result = await self.neo4j.run_query(query, batch=batch_data)
                if result:
                    total_upserted += result[0].get("upserted", len(batch))
                else:
                    total_upserted += len(batch)
                batch_count += 1
                
                logger.debug(f"Batch {batch_count}: upserted {len(batch)} concepts")
                
            except Exception as e:
                logger.error(f"Batch upsert error: {e}")
                raise
        
        logger.info(f"✅ Upserted {total_upserted} concepts in {batch_count} batches")
        
        return {
            "upserted": total_upserted,
            "batches": batch_count,
            "batch_size": self.batch_size
        }
    
    async def upsert_relationships(
        self,
        relationships: List[Dict[str, Any]],
        source_document_id: str
    ) -> Dict[str, Any]:
        """
        Batch upsert relationships.
        
        Args:
            relationships: List of relationship dictionaries
                - source: source concept_id
                - target: target concept_id
                - relationship_type: one of 7 types
                - confidence: 0-1 score
            source_document_id: Document ID for provenance
            
        Returns:
            Dict with upserted count and stats
        """
        if not relationships:
            return {"upserted": 0, "batches": 0}
        
        total_upserted = 0
        batch_count = 0
        
        # Group by relationship type for efficiency
        by_type: Dict[str, List] = {}
        for rel in relationships:
            rel_type = rel.get("relationship_type", rel.get("type", "REQUIRES"))
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel)
        
        # Upsert each type
        for rel_type, rels in by_type.items():
            for i in range(0, len(rels), self.batch_size):
                batch = rels[i:i + self.batch_size]
                
                batch_data = []
                for rel in batch:
                    batch_data.append({
                        "source": rel.get("source"),
                        "target": rel.get("target"),
                        "confidence": rel.get("confidence", 0.8),
                        "source_document_id": source_document_id
                    })
                
                # Dynamic relationship type in query
                query = f"""
                UNWIND $batch AS row
                MATCH (s:CourseConcept {{concept_id: row.source}})
                MATCH (t:CourseConcept {{concept_id: row.target}})
                MERGE (s)-[r:{rel_type}]->(t)
                ON CREATE SET
                    r.confidence = row.confidence,
                    r.source_document_ids = [row.source_document_id],
                    r.created_at = datetime()
                ON MATCH SET
                    r.confidence = row.confidence,
                    r.source_document_ids = CASE 
                        WHEN row.source_document_id IN r.source_document_ids 
                        THEN r.source_document_ids 
                        ELSE r.source_document_ids + row.source_document_id 
                    END,
                    r.updated_at = datetime()
                RETURN count(r) AS upserted
                """
                
                try:
                    result = await self.neo4j.run_query(query, batch=batch_data)
                    if result:
                        total_upserted += result[0].get("upserted", len(batch))
                    else:
                        total_upserted += len(batch)
                    batch_count += 1
                    
                except Exception as e:
                    logger.error(f"Relationship batch upsert error: {e}")
                    # Continue with other batches
        
        logger.info(f"✅ Upserted {total_upserted} relationships in {batch_count} batches")
        
        return {
            "upserted": total_upserted,
            "batches": batch_count,
            "relationship_types": list(by_type.keys())
        }
    
    async def remove_stale_provenance(
        self,
        source_document_id: str
    ) -> Dict[str, int]:
        """
        Remove concepts/relationships that only came from a now-deleted document.
        
        Used when a document is removed from the system.
        Concepts with multiple sources are NOT deleted, just updated.
        
        Args:
            source_document_id: Document to remove from provenance
            
        Returns:
            Dict with counts of updated/deleted items
        """
        # Remove from source_document_ids list
        update_query = """
        MATCH (c:CourseConcept)
        WHERE $doc_id IN c.source_document_ids
        SET c.source_document_ids = [x IN c.source_document_ids WHERE x <> $doc_id]
        RETURN count(c) AS updated
        """
        
        result = await self.neo4j.run_query(update_query, doc_id=source_document_id)
        updated = result[0].get("updated", 0) if result else 0
        
        # Delete concepts with empty source_document_ids
        delete_query = """
        MATCH (c:CourseConcept)
        WHERE size(c.source_document_ids) = 0
        DETACH DELETE c
        RETURN count(c) AS deleted
        """
        
        result = await self.neo4j.run_query(delete_query)
        deleted = result[0].get("deleted", 0) if result else 0
        
        logger.info(f"Removed provenance: {updated} updated, {deleted} deleted")
        
        return {"updated": updated, "deleted": deleted}
    
    async def get_concept_provenance(
        self,
        concept_id: str
    ) -> Dict[str, Any]:
        """
        Get provenance information for a concept.
        
        Returns:
            Dict with source_document_ids and other metadata
        """
        query = """
        MATCH (c:CourseConcept {concept_id: $concept_id})
        RETURN c.source_document_ids AS source_documents,
               c.extraction_version AS extraction_version,
               c.created_at AS created_at,
               c.updated_at AS updated_at
        """
        
        result = await self.neo4j.run_query(query, concept_id=concept_id)
        
        if result:
            return {
                "concept_id": concept_id,
                "source_documents": result[0].get("source_documents", []),
                "extraction_version": result[0].get("extraction_version"),
                "created_at": result[0].get("created_at"),
                "updated_at": result[0].get("updated_at")
            }
        
        return {"concept_id": concept_id, "source_documents": [], "error": "Not found"}
