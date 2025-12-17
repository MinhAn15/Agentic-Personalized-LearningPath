# Knowledge Extraction Agent - Production Version (V2)
"""
Production-grade Knowledge Extraction Agent with:
1. Document Registry (idempotent ingestion)
2. Semantic Chunking (by heading/section)
3. Staging Graph Pattern (extract → validate → promote)
4. Validation Rules enforcement
5. Real Entity Resolution (embedding + structural + contextual)
6. Provenance tracking
"""

import json
import uuid
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from backend.core.base_agent import BaseAgent, AgentType
from backend.models import DocumentInput, KnowledgeExtractionOutput
from backend.prompts import KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT
from backend.config import get_settings

# New production modules
from backend.models.document_registry import (
    DocumentRegistry, DocumentRecord, DocumentStatus, ExtractionVersion
)
from backend.utils.semantic_chunker import SemanticChunker, SemanticChunk
from backend.utils.kg_validator import KGValidator, ValidationResult, ValidationSeverity
from backend.utils.entity_resolver import EntityResolver, ResolutionResult
from backend.utils.neo4j_batch_upsert import Neo4jBatchUpserter
from backend.utils.provenance_manager import ProvenanceManager

from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Document, Settings
from backend.utils.file_lock import file_lock

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """7 Relationship Types per Thesis Specification"""
    REQUIRES = "REQUIRES"
    IS_PREREQUISITE_OF = "IS_PREREQUISITE_OF"
    NEXT = "NEXT"
    REMEDIATES = "REMEDIATES"
    HAS_ALTERNATIVE_PATH = "HAS_ALTERNATIVE_PATH"
    SIMILAR_TO = "SIMILAR_TO"
    IS_SUB_CONCEPT_OF = "IS_SUB_CONCEPT_OF"


class BloomLevel(str, Enum):
    """Bloom's Taxonomy Levels"""
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"


class KnowledgeExtractionAgentV2(BaseAgent):
    """
    Production-grade Knowledge Extraction Agent.
    
    Features:
    1. Idempotent ingestion via Document Registry
    2. Semantic chunking (by heading/section)
    3. Staging graph pattern (StagingConcept → validation → CourseConcept)
    4. Validation enforcement
    5. Real entity resolution (embedding + structural + contextual)
    6. Provenance tracking
    7. COURSEKG_UPDATED event
    
    Process Flow:
    1. Register document (check checksum for idempotency)
    2. Semantic chunking
    3. Per-chunk extraction (Layer 1, 2, 3)
    4. Create StagingConcept nodes
    5. Validate extracted data
    6. Entity resolution (merge with existing concepts)
    7. Promote to CourseConcept (with provenance)
    8. Emit COURSEKG_UPDATED
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        super().__init__(agent_id, AgentType.KNOWLEDGE_EXTRACTION, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or Gemini(
            model=self.settings.GEMINI_MODEL,
            api_key=self.settings.GOOGLE_API_KEY
        )
        self.logger = logging.getLogger(f"KnowledgeExtractionAgentV2.{agent_id}")
        
        # Initialize production modules
        self.document_registry = DocumentRegistry(state_manager)
        self.chunker = SemanticChunker(
            max_chunk_size=4000,
            min_chunk_size=500
        )
        self.validator = KGValidator(strict_mode=False)
        self.entity_resolver = EntityResolver(
            merge_threshold=0.85,
            use_embeddings=True
        )
        
        # Batch upserter for AuraDB production (initialized lazily)
        self._batch_upserter = None
        
        # Provenance manager for document-level overwrite (lazy init)
        self._provenance_manager = None
        
        # Extraction version for provenance
        self.extraction_version = ExtractionVersion.V3_ENTITY_RESOLUTION
        
        # Configure LlamaIndex Global Settings
        # This ensures VectorStoreIndex uses Gemini instead of OpenAI
        Settings.llm = self.llm
        Settings.embed_model = GeminiEmbedding(
            model_name="models/embedding-001",
            api_key=get_settings().GOOGLE_API_KEY
        )
    
    def _get_batch_upserter(self) -> Neo4jBatchUpserter:
        """Get or create batch upserter (lazy initialization)"""
        if self._batch_upserter is None:
            self._batch_upserter = Neo4jBatchUpserter(
                self.state_manager.neo4j,
                batch_size=100  # AuraDB optimized
            )
        return self._batch_upserter
    
    def _get_provenance_manager(self) -> ProvenanceManager:
        """Get or create provenance manager (lazy initialization)"""
        if self._provenance_manager is None:
            self._provenance_manager = ProvenanceManager(self.state_manager.neo4j)
        return self._provenance_manager
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution - Production ingestion pipeline.
        
        Args:
            document_content: str - Document text
            document_title: str - Title
            document_type: str - LECTURE, TUTORIAL, etc.
            force_reprocess: bool - Override idempotency check
        """
        try:
            document_content = kwargs.get("document_content")
            document_title = kwargs.get("document_title", "Untitled")
            document_type = kwargs.get("document_type", "LECTURE")
            force_reprocess = kwargs.get("force_reprocess", False)
            
            if not document_content:
                return self._error_response("document_content is required")
            
            self.logger.info(f"🔍 [V2] Processing: {document_title}")
            
            # ========================================
            # STEP 1: Document Registry (Idempotency)
            # ========================================
            document_id = f"doc_{uuid.uuid4().hex[:8]}"
            doc_record = await self.document_registry.register(
                document_id=document_id,
                filename=document_title,
                content=document_content
            )
            
            if doc_record.status == DocumentStatus.SKIPPED and not force_reprocess:
                self.logger.info(f"⏭️ Document already processed (checksum match)")
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "document_id": doc_record.document_id,
                    "status": "SKIPPED",
                    "message": "Document already processed"
                }
            
            # Update status to PROCESSING
            await self.document_registry.update_status(
                document_id, DocumentStatus.PROCESSING
            )
            
            # ========================================
            # STEP 2: Semantic Chunking
            # ========================================
            chunks = self.chunker.chunk(document_content, document_id)
            chunk_stats = self.chunker.get_stats(chunks)
            
            self.logger.info(f"📄 Chunked into {len(chunks)} semantic blocks")
            
            await self.document_registry.update_status(
                document_id, DocumentStatus.PROCESSING,
                chunk_count=len(chunks)
            )
            
            # ========================================
            # STEP 3: Per-Chunk Extraction
            # ========================================
            all_concepts = []
            all_relationships = []
            
            for i, chunk in enumerate(chunks):
                self.logger.debug(f"Processing chunk {i+1}/{len(chunks)}: {chunk.source_heading}")
                
                # Layer 1: Concept extraction
                chunk_concepts = await self._extract_concepts_from_chunk(chunk, document_title)
                
                # Layer 2: Relationship extraction
                chunk_relationships = await self._extract_relationships_from_chunk(
                    chunk, chunk_concepts
                )
                
                # Layer 3: Metadata enrichment
                enriched_concepts = await self._enrich_metadata(chunk_concepts)
                
                # Add provenance to each concept
                for concept in enriched_concepts:
                    concept["source_document_id"] = document_id
                    concept["source_chunk_id"] = chunk.chunk_id
                    concept["extraction_version"] = self.extraction_version.value
                    concept["extracted_at"] = datetime.now().isoformat()
                
                all_concepts.extend(enriched_concepts)
                all_relationships.extend(chunk_relationships)
            
            self.logger.info(f"📦 Raw extraction: {len(all_concepts)} concepts, {len(all_relationships)} relationships")
            
            # ========================================
            # STEP 4: Create Staging Nodes
            # ========================================
            staging_result = await self._create_staging_nodes(
                document_id, all_concepts, all_relationships
            )
            
            # ========================================
            # STEP 5: Validation
            # ========================================
            validation_result = self.validator.validate(all_concepts, all_relationships)
            
            if not validation_result.is_valid:
                self.logger.warning(f"⚠️ Validation issues found: {len(validation_result.errors)} errors")
                
                # Auto-fix if possible
                fixed_concepts, fixed_relationships = self.validator.auto_fix(
                    all_concepts, all_relationships, validation_result
                )
                
                # Re-validate
                validation_result = self.validator.validate(fixed_concepts, fixed_relationships)
                all_concepts = fixed_concepts
                all_relationships = fixed_relationships
            
            if not validation_result.is_valid:
                await self.document_registry.update_status(
                    document_id, DocumentStatus.FAILED,
                    error_message=f"Validation failed: {len(validation_result.errors)} errors"
                )
                return self._error_response(
                    f"Validation failed: {validation_result.errors[:3]}"
                )
            
            self.logger.info(f"✅ Validation passed: {validation_result.valid_nodes} nodes, {validation_result.valid_relationships} relationships")
            
            await self.document_registry.update_status(
                document_id, DocumentStatus.VALIDATED
            )
            
            # ========================================
            # STEP 6: Entity Resolution
            # ========================================
            existing_concepts = await self._get_existing_concepts()
            existing_relationships = await self._get_existing_relationships()
            
            resolution_result = self.entity_resolver.resolve(
                new_concepts=all_concepts,
                existing_concepts=existing_concepts,
                new_relationships=all_relationships,
                existing_relationships=existing_relationships
            )
            
            self.logger.info(
                f"🔗 Entity resolution: {resolution_result.stats['merged_concepts']} merges, "
                f"{resolution_result.stats['truly_new_concepts']} new concepts"
            )
            
            # ========================================
            # STEP 7: Promote to CourseConcept (Commit)
            # ========================================
            commit_result = await self._promote_to_course_kg(
                document_id=document_id,
                concepts=resolution_result.resolved_concepts,
                relationships=resolution_result.resolved_relationships,
                merge_mapping=resolution_result.merge_mapping
            )
            
            await self.document_registry.update_status(
                document_id, DocumentStatus.COMMITTED,
                concept_count=commit_result["concepts_created"],
                relationship_count=commit_result["relationships_created"],
                extracted_concept_ids=[c["concept_id"] for c in all_concepts]
            )
            
            # ========================================
            # STEP 8: Cleanup Staging + Emit Event
            # ========================================
            await self._cleanup_staging(document_id)
            
            # Persist to Local Vector Store (RAG)
            await self._persist_vector_index(chunks, document_id)
            
            # Emit COURSEKG_UPDATED event
            await self.send_message(
                receiver="planner",
                message_type="COURSEKG_UPDATED",
                payload={
                    "document_id": document_id,
                    "document_title": document_title,
                    "concepts_added": resolution_result.stats["truly_new_concepts"],
                    "concepts_merged": resolution_result.stats["merged_concepts"],
                    "total_concepts": commit_result["concepts_created"],
                    "total_relationships": commit_result["relationships_created"],
                    "extraction_version": self.extraction_version.value
                }
            )
            
            self.logger.info(f"✅ [V2] Extraction complete: {document_id}")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "document_id": document_id,
                "status": "COMMITTED",
                "chunking": chunk_stats,
                "validation": validation_result.to_dict(),
                "resolution": resolution_result.to_dict(),
                "commit": commit_result
            }
        
        except Exception as e:
            self.logger.error(f"❌ [V2] Extraction failed: {e}")
            
            # Update registry if we have document_id
            if 'document_id' in locals():
                await self.document_registry.update_status(
                    document_id, DocumentStatus.FAILED,
                    error_message=str(e)
                )
            
            return self._error_response(str(e))
    
    # ===========================================
    # EXTRACTION METHODS
    # ===========================================
    
    async def _extract_concepts_from_chunk(
        self, chunk: SemanticChunk, document_title: str
    ) -> List[Dict[str, Any]]:
        """
        Extract concepts from a single chunk.
        
        LLM provides raw fields (name, context, description, etc.)
        Backend builds concept_code using ConceptIdBuilder.
        """
        prompt = f"""
You are extracting learning concepts from a document section.

Document: {document_title}
Section: {chunk.source_heading}
Content:
{chunk.content}

Extract ALL learning concepts from this section. For each concept provide:
1. name: Human-readable name (e.g., "SELECT Statement")
2. context: Topic/category context (e.g., "SQL Queries", "Database Basics")
3. description: 1-2 sentence definition
4. learning_objective: What learner will be able to do
5. examples: 1-2 concrete examples
6. difficulty: 1-5 (1=beginner, 5=expert)

IMPORTANT: Do NOT generate concept IDs yourself. Just provide the name and context - 
the system will generate standardized IDs automatically.

Return ONLY valid JSON array:
[
  {{
    "name": "SELECT Statement",
    "context": "SQL Queries",
    "description": "SQL command to retrieve data from database tables",
    "learning_objective": "Learner will write basic SELECT queries",
    "examples": ["SELECT * FROM users", "SELECT name, email FROM customers"],
    "difficulty": 2
  }}
]

If no concepts found, return empty array: []
"""
        try:
            response = await self.llm.acomplete(prompt)
            raw_concepts = self._parse_json_array(response.text)
            
            # Build concept IDs using backend logic
            from backend.utils.concept_id_builder import get_concept_id_builder
            builder = get_concept_id_builder(domain=self._extract_domain(document_title))
            
            for concept in raw_concepts:
                ids = builder.build_from_llm_output(concept)
                concept["concept_id"] = ids.concept_code  # Use concept_code as primary ID
                concept["concept_uuid"] = ids.concept_uuid
                concept["concept_code"] = ids.concept_code
                concept["sanitized_concept"] = ids.sanitized_concept
            
            return raw_concepts
        except Exception as e:
            self.logger.error(f"Concept extraction error: {e}")
            return []
    
    def _extract_domain(self, document_title: str) -> str:
        """Extract domain from document title for concept_code generation"""
        # Simple heuristic: first word or known keywords
        title_lower = document_title.lower()
        
        known_domains = {
            "sql": "sql", "database": "sql", "mysql": "sql", "postgresql": "sql",
            "python": "python", "java": "java", "javascript": "js",
            "react": "react", "node": "node", "nodejs": "node",
            "machine": "ml", "learning": "ml", "deep": "dl",
            "statistics": "stats", "probability": "stats",
            "algorithm": "algo", "data structure": "ds",
        }
        
        for keyword, domain in known_domains.items():
            if keyword in title_lower:
                return domain
        
        # Default: first word
        first_word = title_lower.split()[0] if title_lower.split() else "course"
        return first_word[:10].replace(" ", "_")
    
    async def _extract_relationships_from_chunk(
        self, chunk: SemanticChunk, concepts: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships between concepts with SPR-compliant fields.
        
        SPR Spec Fields:
        - relationship_type: One of 7 types
        - weight: 0.0-1.0 importance/strength
        - dependency: STRONG, MODERATE, WEAK
        - confidence: LLM confidence in extraction
        """
        if len(concepts) < 2:
            return []
        
        concept_list = "\n".join([
            f"- {c.get('concept_id')}: {c.get('name', '')}" 
            for c in concepts
        ])
        
        prompt = f"""
Identify relationships between these concepts:

{concept_list}

For each relationship, specify:
1. source: Source concept_id (UPPERCASE_WITH_UNDERSCORES)
2. target: Target concept_id
3. relationship_type: One of [REQUIRES, IS_PREREQUISITE_OF, NEXT, REMEDIATES, HAS_ALTERNATIVE_PATH, SIMILAR_TO, IS_SUB_CONCEPT_OF]
4. weight: 0.0-1.0 (how important is this link for learning?)
5. dependency: STRONG (must learn first), MODERATE (recommended), or WEAK (optional)
6. confidence: 0.0-1.0 (your confidence in this relationship)
7. reasoning: Brief explanation why this relationship exists

Relationship Type Meanings:
- REQUIRES: A requires knowledge of B first
- IS_PREREQUISITE_OF: A is prerequisite for B
- NEXT: A should be learned before B (sequencing)
- REMEDIATES: A helps fix misunderstanding of B
- HAS_ALTERNATIVE_PATH: A and B are alternative ways to learn same concept
- SIMILAR_TO: A and B are semantically similar
- IS_SUB_CONCEPT_OF: A is a sub-concept/part of B

Return ONLY valid JSON array:
[
  {{
    "source": "CONCEPT_A_ID",
    "target": "CONCEPT_B_ID",
    "relationship_type": "REQUIRES",
    "weight": 0.8,
    "dependency": "STRONG",
    "confidence": 0.9,
    "reasoning": "Brief explanation..."
  }}
]

Return empty array [] if no relationships found.
"""
        try:
            response = await self.llm.acomplete(prompt)
            return self._parse_json_array(response.text)
        except Exception as e:
            self.logger.error(f"Relationship extraction error: {e}")
            return []
    
    async def _enrich_metadata(self, concepts: List[Dict]) -> List[Dict]:
        """Layer 3: Enrich with metadata"""
        if not concepts:
            return []
        
        concept_names = ", ".join([c.get("name", "") for c in concepts])
        
        prompt = f"""
Add metadata to these concepts: {concept_names}

For each concept, add:
1. bloom_level: REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, or CREATE
2. time_estimate: Minutes to learn (15-120)
3. semantic_tags: 3-5 keywords for search
4. focused_tags: 2-3 most specific keywords

Return JSON object mapping concept_id to metadata:
{{
  "CONCEPT_ID": {{
    "bloom_level": "UNDERSTAND",
    "time_estimate": 30,
    "semantic_tags": ["tag1", "tag2", "tag3"],
    "focused_tags": ["focused1", "focused2"]
  }}
}}
"""
        try:
            response = await self.llm.acomplete(prompt)
            metadata = self._parse_json_object(response.text)
            
            # Merge metadata into concepts
            for concept in concepts:
                cid = concept.get("concept_id", "")
                if cid in metadata:
                    concept.update(metadata[cid])
            
            return concepts
        except Exception as e:
            self.logger.error(f"Metadata enrichment error: {e}")
            return concepts
    
    # ===========================================
    # STAGING METHODS
    # ===========================================
    
    async def _create_staging_nodes(
        self, document_id: str, concepts: List[Dict], relationships: List[Dict]
    ) -> Dict[str, Any]:
        """Create staging nodes in Neo4j"""
        neo4j = self.state_manager.neo4j
        created = 0
        
        for concept in concepts:
            await neo4j.run_query(
                """
                CREATE (s:StagingConcept {
                    concept_id: $concept_id,
                    extraction_id: $extraction_id,
                    name: $name,
                    description: $description,
                    difficulty: $difficulty,
                    bloom_level: $bloom_level,
                    semantic_tags: $tags,
                    created_at: datetime()
                })
                """,
                concept_id=concept.get("concept_id"),
                extraction_id=document_id,
                name=concept.get("name", ""),
                description=concept.get("description", ""),
                difficulty=concept.get("difficulty", 2),
                bloom_level=concept.get("bloom_level", "UNDERSTAND"),
                tags=concept.get("semantic_tags", [])
            )
            created += 1
        
        return {"staging_concepts_created": created}
    
    async def _cleanup_staging(self, document_id: str) -> None:
        """Remove staging nodes after commit"""
        neo4j = self.state_manager.neo4j
        await neo4j.run_query(
            "MATCH (s:StagingConcept {extraction_id: $id}) DETACH DELETE s",
            id=document_id
        )
    
    # ===========================================
    # COMMIT METHODS
    # ===========================================
    
    async def _get_existing_concepts(self) -> List[Dict]:
        """Get all existing concepts from Course KG"""
        neo4j = self.state_manager.neo4j
        result = await neo4j.run_query(
            """
            MATCH (c:CourseConcept)
            RETURN c.concept_id as concept_id,
                   c.name as name,
                   c.description as description,
                   c.difficulty as difficulty,
                   c.semantic_tags as semantic_tags
            """
        )
        return result if result else []
    
    async def _get_existing_relationships(self) -> List[Dict]:
        """Get all existing relationships from Course KG"""
        neo4j = self.state_manager.neo4j
        result = await neo4j.run_query(
            """
            MATCH (a:CourseConcept)-[r]->(b:CourseConcept)
            RETURN a.concept_id as source,
                   b.concept_id as target,
                   type(r) as relationship_type
            """
        )
        return result if result else []
    
    async def _promote_to_course_kg(
        self,
        document_id: str,
        concepts: List[Dict],
        relationships: List[Dict],
        merge_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Promote validated concepts to CourseConcept using batch UNWIND.
        
        Features:
        - Batch operations for AuraDB performance
        - Provenance tracking with source_document_ids list
        - MERGE for idempotent upserts
        """
        upserter = self._get_batch_upserter()
        
        # Batch upsert concepts with provenance list
        concept_result = await upserter.upsert_concepts(
            concepts=concepts,
            source_document_id=document_id
        )
        
        # Batch upsert relationships
        rel_result = await upserter.upsert_relationships(
            relationships=relationships,
            source_document_id=document_id
        )
        
        self.logger.info(
            f"📊 Batch upsert: {concept_result['upserted']} concepts in {concept_result['batches']} batches, "
            f"{rel_result['upserted']} relationships"
        )
        
        return {
            "concepts_created": concept_result["upserted"],
            "relationships_created": rel_result["upserted"],
            "concept_batches": concept_result["batches"],
            "relationship_batches": rel_result["batches"]
        }
    
    # ===========================================
    # HELPER METHODS
    # ===========================================
    
    def _parse_json_array(self, text: str) -> List[Dict]:
        """Parse JSON array from LLM response"""
        try:
            json_start = text.find("[")
            json_end = text.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(text[json_start:json_end])
        except json.JSONDecodeError:
            pass
        return []
    
    def _parse_json_object(self, text: str) -> Dict:
        """Parse JSON object from LLM response"""
        try:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(text[json_start:json_end])
        except json.JSONDecodeError:
            pass
        return {}
    
    def _error_response(self, error: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "agent_id": self.agent_id,
            "error": error
        }
    
    # ===========================================
    # PROVENANCE-AWARE EXECUTION
    # ===========================================
    
    async def execute_with_provenance(self, **kwargs) -> Dict[str, Any]:
        """
        Execute with full provenance subgraph support.
        
        This method uses ConceptSnapshot/RelSnapshot pattern for:
        - Document-level overwrite (re-upload same filename)
        - Delta rebuild (only affected concepts)
        - Full audit trail
        
        Args:
            document_content: str - Document text
            document_title: str - Filename (used for overwrite detection)
            document_type: str - LECTURE, TUTORIAL, etc.
        """
        import hashlib
        
        try:
            document_content = kwargs.get("document_content")
            document_title = kwargs.get("document_title", "Untitled")
            document_type = kwargs.get("document_type", "LECTURE")
            
            if not document_content:
                return self._error_response("document_content is required")
            
            self.logger.info(f"🔍 [V2+Provenance] Processing: {document_title}")
            
            # Generate document ID and checksum
            checksum = hashlib.sha256(document_content.encode()).hexdigest()
            document_id = f"doc_{uuid.uuid4().hex[:8]}"
            
            provenance_manager = self._get_provenance_manager()
            
            # ========================================
            # STEP 1: Check for existing document (by filename)
            # ========================================
            existing = await provenance_manager.get_existing_doc_by_filename(document_title)
            
            if existing and existing.get("checksum") == checksum:
                self.logger.info(f"⏭️ Document unchanged (same checksum)")
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "document_id": existing["doc_id"],
                    "status": "SKIPPED",
                    "reason": "checksum_unchanged"
                }
            
            was_overwrite = bool(existing)
            if was_overwrite:
                self.logger.info(f"♻️ Re-upload detected, will overwrite: {existing['doc_id']}")
            
            # ========================================
            # STEP 2: Semantic Chunking
            # ========================================
            chunks = self.chunker.chunk(document_content, document_id)
            self.logger.info(f"📄 Chunked into {len(chunks)} semantic blocks")
            
            # ========================================
            # STEP 3: Per-Chunk Extraction
            # ========================================
            concept_snapshots = []
            rel_snapshots = []
            
            for i, chunk in enumerate(chunks):
                self.logger.debug(f"Processing chunk {i+1}/{len(chunks)}: {chunk.source_heading}")
                
                # Layer 1: Concept extraction
                chunk_concepts = await self._extract_concepts_from_chunk(chunk, document_title)
                
                # Layer 2: Relationship extraction
                chunk_relationships = await self._extract_relationships_from_chunk(
                    chunk, chunk_concepts
                )
                
                # Layer 3: Metadata enrichment
                enriched_concepts = await self._enrich_metadata(chunk_concepts)
                
                # Convert to snapshot format
                for concept in enriched_concepts:
                    concept_snapshots.append({
                        "concept_id": concept.get("concept_id"),
                        "name": concept.get("name", ""),
                        "description": concept.get("description", ""),
                        "bloom_level": concept.get("bloom_level", "UNDERSTAND"),
                        "time_estimate": concept.get("time_estimate", 30),
                        "semantic_tags": concept.get("semantic_tags", []),
                        "focused_tags": concept.get("focused_tags", []),
                        "difficulty": concept.get("difficulty", 2),
                        "learning_objective": concept.get("learning_objective", ""),
                        "examples": concept.get("examples", []),
                        "confidence": 0.85  # Default confidence
                    })
                
                for rel in chunk_relationships:
                    rel_snapshots.append({
                        "rel_type": rel.get("relationship_type", rel.get("type", "REQUIRES")),
                        "source_id": rel.get("source"),
                        "target_id": rel.get("target"),
                        "weight": 1.0,
                        "dependency": "STRONG",
                        "confidence": rel.get("confidence", 0.8),
                        "reasoning": ""
                    })
            
            self.logger.info(f"📦 Extracted: {len(concept_snapshots)} concepts, {len(rel_snapshots)} relationships")
            
            # ========================================
            # STEP 4: Validation
            # ========================================
            validation_result = self.validator.validate(concept_snapshots, rel_snapshots)
            
            if not validation_result.is_valid:
                fixed_concepts, fixed_rels = self.validator.auto_fix(
                    concept_snapshots, rel_snapshots, validation_result
                )
                validation_result = self.validator.validate(fixed_concepts, fixed_rels)
                concept_snapshots = fixed_concepts
                rel_snapshots = fixed_rels
            
            if not validation_result.is_valid:
                return self._error_response(
                    f"Validation failed: {validation_result.errors[:3]}"
                )
            
            self.logger.info(f"✅ Validation passed")
            
            # ========================================
            # STEP 5: Provenance Overwrite (delete + insert + rebuild)
            # ========================================
            result = await provenance_manager.overwrite_document(
                doc_id=document_id,
                filename=document_title,
                checksum=checksum,
                concept_snapshots=concept_snapshots,
                rel_snapshots=rel_snapshots
            )
            
            # ========================================
            # STEP 6: Emit COURSEKG_UPDATED event
            # ========================================
            await self.send_message(
                receiver="planner",
                message_type="COURSEKG_UPDATED",
                payload={
                    "document_id": document_id,
                    "document_title": document_title,
                    "was_overwrite": was_overwrite,
                    "concepts_inserted": result["snapshots"]["concepts_inserted"],
                    "relationships_inserted": result["snapshots"]["relationships_inserted"],
                    "concepts_rebuilt": result["canonical"]["concepts_rebuilt"],
                    "extraction_version": self.extraction_version.value
                }
            )
            
            self.logger.info(f"✅ [V2+Provenance] Complete: {document_id}")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "document_id": document_id,
                "status": "COMMITTED",
                "was_overwrite": was_overwrite,
                "provenance": result
            }
        
        except Exception as e:
            self.logger.error(f"❌ [V2+Provenance] Failed: {e}")
            return self._error_response(str(e))

    async def _persist_vector_index(self, chunks: List[SemanticChunk], document_id: str):
        """Persist chunks to local vector store"""
        try:
            # Safe path resolution: assume cwd is storage root
            storage_dir = os.path.join(os.getcwd(), "backend", "storage", "vector_store")
            
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)
                
            lock_file = os.path.join(storage_dir, "write.lock")
            
            # Convert chunks to Documents
            documents = []
            for chunk in chunks:
                doc = Document(
                    text=chunk.content,
                    metadata={
                        "document_id": document_id,
                        "chunk_id": chunk.chunk_id,
                        "heading": chunk.source_heading
                    }
                )
                documents.append(doc)
            
            self.logger.info(f"🔒 [RAG] Acquiring lock for vector store...")
            with file_lock(lock_file, timeout=60):
                # Check for existing index
                if os.path.exists(os.path.join(storage_dir, "docstore.json")):
                    self.logger.info("loading existing index")
                    storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
                    index = load_index_from_storage(storage_context)
                    # Loop and insert (safest for updates)
                    for doc in documents:
                        index.insert(doc)
                else:
                    self.logger.info("creating new index")
                    index = VectorStoreIndex.from_documents(documents)
                    
                # Persist
                index.storage_context.persist(persist_dir=storage_dir)
                
            self.logger.info(f"💾 [RAG] Persisted {len(documents)} chunks to local vector store")
            
        except Exception as e:
            self.logger.error(f"❌ [RAG] Vector persistence failed: {e}")
            # Don't fail the whole pipeline, just log

