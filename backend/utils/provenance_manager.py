# Provenance Manager for Knowledge Graph
"""
Provenance Layer: Track document-level contributions with snapshots.

Schema:
- (:SourceDocument) - Document lifecycle management
- (:ConceptSnapshot) - Concept version per document
- (:RelSnapshot) - Relationship version per document
- (:CourseConcept) - Canonical "single latest truth"

Features:
1. Document-level overwrite (re-upload same lecture)
2. Delta rebuild (only affected concepts)
3. Multi-document merge policy (highest confidence)
4. Full audit trail
"""

import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class DocumentStatus(str, Enum):
    """SourceDocument status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    DELETED = "DELETED"


@dataclass
class ConceptSnapshot:
    """Snapshot of a concept from a specific document"""
    doc_id: str
    concept_id: str
    name: str
    description: str
    bloom_level: str = "UNDERSTAND"
    time_estimate: int = 30
    semantic_tags: List[str] = None
    focused_tags: List[str] = None
    difficulty: int = 2
    learning_objective: str = ""
    examples: List[str] = None
    confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "concept_id": self.concept_id,
            "name": self.name,
            "description": self.description,
            "bloom_level": self.bloom_level,
            "time_estimate": self.time_estimate,
            "semantic_tags": self.semantic_tags or [],
            "focused_tags": self.focused_tags or [],
            "difficulty": self.difficulty,
            "learning_objective": self.learning_objective,
            "examples": self.examples or [],
            "confidence": self.confidence
        }


@dataclass
class RelSnapshot:
    """Snapshot of a relationship from a specific document"""
    doc_id: str
    rel_type: str
    source_id: str
    target_id: str
    weight: float = 1.0
    dependency: str = "STRONG"  # STRONG, MODERATE, WEAK
    confidence: float = 0.8
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "rel_type": self.rel_type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "weight": self.weight,
            "dependency": self.dependency,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


class ProvenanceManager:
    """
    Manage provenance subgraph with document-level overwrite.
    
    Pattern:
    1. SourceDocument tracks document lifecycle
    2. ConceptSnapshot/RelSnapshot store per-doc extractions
    3. CourseConcept is rebuilt from snapshots with merge policy
    
    Merge Policy:
    - Choose snapshot with highest confidence
    - If tied, choose most recent (uploaded_at)
    """
    
    BATCH_SIZE = 100
    
    def __init__(self, neo4j_client):
        self.neo4j = neo4j_client
        self.logger = logging.getLogger("ProvenanceManager")
    
    # ==========================================
    # SOURCE DOCUMENT MANAGEMENT
    # ==========================================
    
    async def create_source_document(
        self,
        doc_id: str,
        filename: str,
        checksum: str,
        status: DocumentStatus = DocumentStatus.PENDING
    ) -> bool:
        """Create or update SourceDocument node"""
        query = """
        MERGE (d:SourceDocument {doc_id: $doc_id})
        ON CREATE SET
            d.filename = $filename,
            d.checksum = $checksum,
            d.status = $status,
            d.uploaded_at = datetime(),
            d.created_at = datetime()
        ON MATCH SET
            d.filename = $filename,
            d.checksum = $checksum,
            d.status = $status,
            d.uploaded_at = datetime()
        RETURN d.doc_id AS id
        """
        
        result = await self.neo4j.run_query(
            query,
            doc_id=doc_id,
            filename=filename,
            checksum=checksum,
            status=status.value
        )
        
        return bool(result)
    
    async def get_existing_doc_by_filename(self, filename: str) -> Optional[Dict]:
        """Find existing document by filename (for re-upload detection)"""
        query = """
        MATCH (d:SourceDocument {filename: $filename})
        WHERE d.status <> 'DELETED'
        RETURN d.doc_id AS doc_id,
               d.checksum AS checksum,
               d.uploaded_at AS uploaded_at,
               d.status AS status
        ORDER BY d.uploaded_at DESC
        LIMIT 1
        """
        
        result = await self.neo4j.run_query(query, filename=filename)
        return result[0] if result else None
    
    async def update_doc_status(self, doc_id: str, status: DocumentStatus) -> bool:
        """Update document status"""
        query = """
        MATCH (d:SourceDocument {doc_id: $doc_id})
        SET d.status = $status, d.updated_at = datetime()
        RETURN d.doc_id AS id
        """
        result = await self.neo4j.run_query(query, doc_id=doc_id, status=status.value)
        return bool(result)
    
    # ==========================================
    # SNAPSHOT MANAGEMENT
    # ==========================================
    
    async def delete_snapshots_for_doc(self, doc_id: str) -> Dict[str, int]:
        """
        Delete all snapshots for a document (before re-upload).
        
        This is the "overwrite" operation - clear old extractions
        before inserting new ones.
        """
        # Delete ConceptSnapshots
        concept_query = """
        MATCH (d:SourceDocument {doc_id: $doc_id})-[:EXTRACTED]->(s:ConceptSnapshot)
        DETACH DELETE s
        RETURN count(s) AS deleted
        """
        concept_result = await self.neo4j.run_query(concept_query, doc_id=doc_id)
        concepts_deleted = concept_result[0].get("deleted", 0) if concept_result else 0
        
        # Delete RelSnapshots
        rel_query = """
        MATCH (d:SourceDocument {doc_id: $doc_id})-[:EXTRACTED]->(s:RelSnapshot)
        DETACH DELETE s
        RETURN count(s) AS deleted
        """
        rel_result = await self.neo4j.run_query(rel_query, doc_id=doc_id)
        rels_deleted = rel_result[0].get("deleted", 0) if rel_result else 0
        
        self.logger.info(f"🗑️ Deleted {concepts_deleted} concept snapshots, {rels_deleted} rel snapshots for {doc_id}")
        
        return {
            "concepts_deleted": concepts_deleted,
            "relationships_deleted": rels_deleted
        }
    
    async def insert_concept_snapshots(
        self,
        doc_id: str,
        snapshots: List[Dict[str, Any]]
    ) -> int:
        """
        Insert concept snapshots with batch UNWIND.
        Also upserts canonical CourseConcept nodes.
        """
        if not snapshots:
            return 0
        
        total_inserted = 0
        
        for i in range(0, len(snapshots), self.BATCH_SIZE):
            batch = snapshots[i:i + self.BATCH_SIZE]
            
            query = """
            MATCH (d:SourceDocument {doc_id: $doc_id})
            UNWIND $batch AS row
            
            // Upsert canonical CourseConcept
            MERGE (c:CourseConcept {concept_id: row.concept_id})
            ON CREATE SET c.created_at = datetime()
            
            // Create snapshot linked to document and concept
            CREATE (s:ConceptSnapshot {
                snapshot_id: randomUUID(),
                concept_id: row.concept_id,
                name: row.name,
                description: row.description,
                bloom_level: row.bloom_level,
                time_estimate: row.time_estimate,
                semantic_tags: row.semantic_tags,
                focused_tags: row.focused_tags,
                difficulty: row.difficulty,
                learning_objective: row.learning_objective,
                examples: row.examples,
                confidence: row.confidence,
                created_at: datetime()
            })
            
            // Link snapshot to document and concept
            CREATE (d)-[:EXTRACTED]->(s)
            CREATE (s)-[:ABOUT]->(c)
            
            RETURN count(s) AS inserted
            """
            
            result = await self.neo4j.run_query(query, doc_id=doc_id, batch=batch)
            if result:
                total_inserted += result[0].get("inserted", len(batch))
        
        self.logger.info(f"📝 Inserted {total_inserted} concept snapshots for {doc_id}")
        return total_inserted
    
    async def insert_rel_snapshots(
        self,
        doc_id: str,
        snapshots: List[Dict[str, Any]]
    ) -> int:
        """Insert relationship snapshots with batch UNWIND."""
        if not snapshots:
            return 0
        
        total_inserted = 0
        
        for i in range(0, len(snapshots), self.BATCH_SIZE):
            batch = snapshots[i:i + self.BATCH_SIZE]
            
            query = """
            MATCH (d:SourceDocument {doc_id: $doc_id})
            UNWIND $batch AS row
            
            // Find source and target concepts
            MATCH (a:CourseConcept {concept_id: row.source_id})
            MATCH (b:CourseConcept {concept_id: row.target_id})
            
            // Create relationship snapshot
            CREATE (s:RelSnapshot {
                snapshot_id: randomUUID(),
                rel_type: row.rel_type,
                source_id: row.source_id,
                target_id: row.target_id,
                weight: row.weight,
                dependency: row.dependency,
                confidence: row.confidence,
                reasoning: row.reasoning,
                created_at: datetime()
            })
            
            // Link to document and concepts
            CREATE (d)-[:EXTRACTED]->(s)
            CREATE (s)-[:FROM]->(a)
            CREATE (s)-[:TO]->(b)
            
            RETURN count(s) AS inserted
            """
            
            result = await self.neo4j.run_query(query, doc_id=doc_id, batch=batch)
            if result:
                total_inserted += result[0].get("inserted", len(batch))
        
        self.logger.info(f"🔗 Inserted {total_inserted} rel snapshots for {doc_id}")
        return total_inserted
    
    # ==========================================
    # CANONICAL REBUILD
    # ==========================================
    
    async def rebuild_canonical_concepts(
        self,
        concept_ids: Optional[List[str]] = None
    ) -> int:
        """
        Rebuild canonical CourseConcept from snapshots.
        
        Policy:
        1. Choose snapshot with highest confidence
        2. If tied, choose most recent (uploaded_at)
        
        Args:
            concept_ids: If provided, only rebuild these concepts (delta)
                        If None, rebuild all
        """
        if concept_ids:
            # Delta rebuild - only specified concepts
            query = """
            UNWIND $concept_ids AS cid
            MATCH (c:CourseConcept {concept_id: cid})
            
            // Find best snapshot (highest confidence, then most recent)
            OPTIONAL MATCH (d:SourceDocument)-[:EXTRACTED]->(s:ConceptSnapshot)-[:ABOUT]->(c)
            WHERE d.status = 'COMMITTED'
            
            WITH c, s, d
            ORDER BY s.confidence DESC, d.uploaded_at DESC
            
            WITH c, collect(s)[0] AS best
            
            // Update canonical from best snapshot
            SET c.name = COALESCE(best.name, c.name),
                c.description = COALESCE(best.description, c.description),
                c.bloom_level = COALESCE(best.bloom_level, c.bloom_level),
                c.time_estimate = COALESCE(best.time_estimate, c.time_estimate),
                c.semantic_tags = COALESCE(best.semantic_tags, c.semantic_tags),
                c.focused_tags = COALESCE(best.focused_tags, c.focused_tags),
                c.difficulty = COALESCE(best.difficulty, c.difficulty),
                c.learning_objective = COALESCE(best.learning_objective, c.learning_objective),
                c.examples = COALESCE(best.examples, c.examples),
                c.canonical_confidence = best.confidence,
                c.updated_at = datetime()
            
            RETURN count(c) AS rebuilt
            """
            result = await self.neo4j.run_query(query, concept_ids=concept_ids)
        else:
            # Full rebuild - all concepts
            query = """
            MATCH (c:CourseConcept)
            
            // Find best snapshot for each concept
            OPTIONAL MATCH (d:SourceDocument)-[:EXTRACTED]->(s:ConceptSnapshot)-[:ABOUT]->(c)
            WHERE d.status = 'COMMITTED'
            
            WITH c, s, d
            ORDER BY s.confidence DESC, d.uploaded_at DESC
            
            WITH c, collect(s)[0] AS best
            
            SET c.name = COALESCE(best.name, c.name),
                c.description = COALESCE(best.description, c.description),
                c.bloom_level = COALESCE(best.bloom_level, c.bloom_level),
                c.time_estimate = COALESCE(best.time_estimate, c.time_estimate),
                c.semantic_tags = COALESCE(best.semantic_tags, c.semantic_tags),
                c.focused_tags = COALESCE(best.focused_tags, c.focused_tags),
                c.difficulty = COALESCE(best.difficulty, c.difficulty),
                c.learning_objective = COALESCE(best.learning_objective, c.learning_objective),
                c.examples = COALESCE(best.examples, c.examples),
                c.canonical_confidence = best.confidence,
                c.updated_at = datetime()
            
            RETURN count(c) AS rebuilt
            """
            result = await self.neo4j.run_query(query)
        
        rebuilt = result[0].get("rebuilt", 0) if result else 0
        self.logger.info(f"🔄 Rebuilt {rebuilt} canonical concepts")
        return rebuilt
    
    async def rebuild_canonical_relationships(
        self,
        concept_ids: Optional[List[str]] = None
    ) -> int:
        """
        Rebuild canonical relationships from RelSnapshots.
        
        For each unique (source, target, type) combination:
        - If multiple snapshots, use highest confidence
        - Create/update the actual relationship
        """
        if concept_ids:
            # Delta rebuild - relationships involving these concepts
            query = """
            UNWIND $concept_ids AS cid
            
            // Find rel snapshots involving these concepts
            MATCH (d:SourceDocument)-[:EXTRACTED]->(s:RelSnapshot)
            WHERE (s.source_id = cid OR s.target_id = cid)
              AND d.status = 'COMMITTED'
            
            MATCH (s)-[:FROM]->(a:CourseConcept)
            MATCH (s)-[:TO]->(b:CourseConcept)
            
            WITH s.rel_type AS rel_type, a, b, s
            ORDER BY s.confidence DESC
            
            WITH rel_type, a, b, collect(s)[0] AS best
            
            // Create/update canonical relationship
            CALL apoc.merge.relationship(a, rel_type, {}, {
                weight: best.weight,
                dependency: best.dependency,
                confidence: best.confidence,
                updated_at: datetime()
            }, b, {}) YIELD rel
            
            RETURN count(rel) AS rebuilt
            """
        else:
            # Full rebuild - simpler without APOC
            query = """
            MATCH (d:SourceDocument)-[:EXTRACTED]->(s:RelSnapshot)
            WHERE d.status = 'COMMITTED'
            MATCH (s)-[:FROM]->(a:CourseConcept)
            MATCH (s)-[:TO]->(b:CourseConcept)
            
            WITH s.rel_type AS rel_type, a, b, s
            ORDER BY s.confidence DESC
            
            WITH rel_type, a, b, collect(s)[0] AS best
            
            // Note: Dynamic relationship types require APOC or separate queries per type
            // This returns data for application-level processing
            RETURN a.concept_id AS source, b.concept_id AS target, 
                   rel_type, best.weight AS weight, best.dependency AS dependency,
                   best.confidence AS confidence
            """
        
        # For non-APOC Neo4j, we need to process relationships per type
        result = await self._rebuild_relationships_by_type(concept_ids)
        return result
    
    async def _rebuild_relationships_by_type(
        self,
        concept_ids: Optional[List[str]] = None
    ) -> int:
        """Rebuild relationships - one query per relationship type (APOC-free)"""
        
        rel_types = [
            "REQUIRES", "IS_PREREQUISITE_OF", "NEXT", "REMEDIATES",
            "HAS_ALTERNATIVE_PATH", "SIMILAR_TO", "IS_SUB_CONCEPT_OF"
        ]
        
        total_rebuilt = 0
        
        for rel_type in rel_types:
            if concept_ids:
                query = f"""
                UNWIND $concept_ids AS cid
                
                MATCH (d:SourceDocument)-[:EXTRACTED]->(s:RelSnapshot)
                WHERE s.rel_type = $rel_type
                  AND (s.source_id = cid OR s.target_id = cid)
                  AND d.status = 'COMMITTED'
                
                MATCH (s)-[:FROM]->(a:CourseConcept)
                MATCH (s)-[:TO]->(b:CourseConcept)
                
                WITH a, b, s
                ORDER BY s.confidence DESC
                WITH a, b, collect(s)[0] AS best
                
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.weight = best.weight,
                    r.dependency = best.dependency,
                    r.confidence = best.confidence,
                    r.updated_at = datetime()
                
                RETURN count(r) AS rebuilt
                """
                result = await self.neo4j.run_query(
                    query, concept_ids=concept_ids, rel_type=rel_type
                )
            else:
                query = f"""
                MATCH (d:SourceDocument)-[:EXTRACTED]->(s:RelSnapshot)
                WHERE s.rel_type = $rel_type AND d.status = 'COMMITTED'
                
                MATCH (s)-[:FROM]->(a:CourseConcept)
                MATCH (s)-[:TO]->(b:CourseConcept)
                
                WITH a, b, s
                ORDER BY s.confidence DESC
                WITH a, b, collect(s)[0] AS best
                
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.weight = best.weight,
                    r.dependency = best.dependency,
                    r.confidence = best.confidence,
                    r.updated_at = datetime()
                
                RETURN count(r) AS rebuilt
                """
                result = await self.neo4j.run_query(query, rel_type=rel_type)
            
            if result:
                total_rebuilt += result[0].get("rebuilt", 0)
        
        self.logger.info(f"🔄 Rebuilt {total_rebuilt} canonical relationships")
        return total_rebuilt
    
    # ==========================================
    # DOCUMENT OVERWRITE (MAIN ENTRY POINT)
    # ==========================================
    
    async def overwrite_document(
        self,
        doc_id: str,
        filename: str,
        checksum: str,
        concept_snapshots: List[Dict],
        rel_snapshots: List[Dict]
    ) -> Dict[str, Any]:
        """
        Main entry point: Overwrite a document's contributions.
        
        Steps:
        1. Check if document exists (by filename)
        2. If exists with different checksum, delete old snapshots
        3. Create/update SourceDocument
        4. Insert new snapshots
        5. Delta rebuild affected concepts
        
        Returns:
            Dict with operation stats
        """
        self.logger.info(f"📄 Processing document overwrite: {filename}")
        
        # Step 1: Check for existing document
        existing = await self.get_existing_doc_by_filename(filename)
        
        affected_concept_ids = set()
        deleted_stats = {"concepts_deleted": 0, "relationships_deleted": 0}
        
        if existing:
            if existing["checksum"] == checksum:
                self.logger.info(f"⏭️ Document unchanged (same checksum)")
                return {
                    "status": "SKIPPED",
                    "reason": "same_checksum",
                    "doc_id": existing["doc_id"]
                }
            
            # Step 2: Delete old snapshots
            old_doc_id = existing["doc_id"]
            
            # Get affected concept IDs before deletion
            affected = await self.neo4j.run_query(
                """
                MATCH (:SourceDocument {doc_id: $doc_id})-[:EXTRACTED]->(s:ConceptSnapshot)
                RETURN collect(DISTINCT s.concept_id) AS concept_ids
                """,
                doc_id=old_doc_id
            )
            if affected:
                affected_concept_ids.update(affected[0].get("concept_ids", []))
            
            deleted_stats = await self.delete_snapshots_for_doc(old_doc_id)
            
            # Mark old document as deleted
            await self.update_doc_status(old_doc_id, DocumentStatus.DELETED)
        
        # Step 3: Create new SourceDocument
        await self.create_source_document(
            doc_id=doc_id,
            filename=filename,
            checksum=checksum,
            status=DocumentStatus.PROCESSING
        )
        
        # Step 4: Insert new snapshots
        concepts_inserted = await self.insert_concept_snapshots(doc_id, concept_snapshots)
        rels_inserted = await self.insert_rel_snapshots(doc_id, rel_snapshots)
        
        # Add new concept IDs to affected set
        affected_concept_ids.update(s.get("concept_id") for s in concept_snapshots)
        
        # Step 5: Update status to COMMITTED
        await self.update_doc_status(doc_id, DocumentStatus.COMMITTED)
        
        # Step 6: Delta rebuild affected concepts
        if affected_concept_ids:
            rebuilt_concepts = await self.rebuild_canonical_concepts(list(affected_concept_ids))
            rebuilt_rels = await self.rebuild_canonical_relationships(list(affected_concept_ids))
        else:
            rebuilt_concepts = 0
            rebuilt_rels = 0
        
        result = {
            "status": "COMMITTED",
            "doc_id": doc_id,
            "was_overwrite": bool(existing),
            "snapshots": {
                "concepts_deleted": deleted_stats["concepts_deleted"],
                "concepts_inserted": concepts_inserted,
                "relationships_deleted": deleted_stats["relationships_deleted"],
                "relationships_inserted": rels_inserted
            },
            "canonical": {
                "concepts_rebuilt": rebuilt_concepts,
                "relationships_rebuilt": rebuilt_rels
            }
        }
        
        self.logger.info(f"✅ Document overwrite complete: {result}")
        return result
    
    # ==========================================
    # AUDIT / QUERY METHODS
    # ==========================================
    
    async def get_concept_sources(self, concept_id: str) -> List[Dict]:
        """Get all documents that contributed to a concept"""
        query = """
        MATCH (d:SourceDocument)-[:EXTRACTED]->(s:ConceptSnapshot)-[:ABOUT]->(c:CourseConcept {concept_id: $concept_id})
        WHERE d.status = 'COMMITTED'
        RETURN d.doc_id AS doc_id,
               d.filename AS filename,
               d.uploaded_at AS uploaded_at,
               s.confidence AS confidence
        ORDER BY s.confidence DESC, d.uploaded_at DESC
        """
        return await self.neo4j.run_query(query, concept_id=concept_id) or []
    
    async def get_document_contributions(self, doc_id: str) -> Dict[str, List]:
        """Get all concepts and relationships from a document"""
        concepts_query = """
        MATCH (d:SourceDocument {doc_id: $doc_id})-[:EXTRACTED]->(s:ConceptSnapshot)
        RETURN s.concept_id AS concept_id, s.name AS name, s.confidence AS confidence
        """
        concepts = await self.neo4j.run_query(concepts_query, doc_id=doc_id) or []
        
        rels_query = """
        MATCH (d:SourceDocument {doc_id: $doc_id})-[:EXTRACTED]->(s:RelSnapshot)
        RETURN s.source_id AS source, s.target_id AS target, 
               s.rel_type AS type, s.confidence AS confidence
        """
        rels = await self.neo4j.run_query(rels_query, doc_id=doc_id) or []
        
        return {"concepts": concepts, "relationships": rels}
