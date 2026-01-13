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
import asyncio  # FIX Gap 1: Import asyncio
from typing import Dict, Any, List, Optional
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from backend.core.base_agent import BaseAgent, AgentType
from backend.models import DocumentInput, KnowledgeExtractionOutput
from backend.prompts import (
    KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT,
    LIGHTRAG_RELATIONSHIP_EXTRACTION_PROMPT,
    LIGHTRAG_CONTENT_KEYWORDS_PROMPT
)
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
from backend.utils.concept_id_builder import get_concept_id_builder  # FIX Issue 1: Move import to top

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


class KnowledgeExtractionAgent(BaseAgent):
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
    
    # FIX Issue 2: Class-level constants for configuration
    MERGE_THRESHOLD = 0.85  # Entity resolution merge threshold
    TOP_K_CANDIDATES = 20  # Number of candidates for entity resolution
    BATCH_SIZE = 100  # Neo4j batch upsert size
    CHUNK_MIN_SIZE = 500  # Minimum chunk size
    CHUNK_MAX_SIZE = 4000  # Maximum chunk size
    MAX_CONCURRENCY = 5   # FIX Gap 1: Limit parallel LLM calls to prevent throttling
    
    # FIX Issue 4: Domain detection as class constant
    KNOWN_DOMAINS = {
        "sql": "sql", "database": "sql", "mysql": "sql", "postgresql": "sql",
        "python": "python", "java": "java", "javascript": "js",
        "react": "react", "node": "node", "nodejs": "node",
        "machine": "ml", "learning": "ml", "deep": "dl",
        "statistics": "stats", "probability": "stats",
        "algorithm": "algo", "data structure": "ds",
    }
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        super().__init__(agent_id, AgentType.KNOWLEDGE_EXTRACTION, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or Gemini(
            model=self.settings.GEMINI_MODEL,
            api_key=self.settings.GOOGLE_API_KEY
        )
        self.logger = logging.getLogger(f"KnowledgeExtractionAgent.{agent_id}")
        
        # Initialize production modules
        self.document_registry = DocumentRegistry(state_manager)
        # Configure LlamaIndex Global Settings
        # This ensures VectorStoreIndex uses Gemini instead of OpenAI
        Settings.llm = self.llm
        self.embedding_model = GeminiEmbedding(
            model_name="models/embedding-001",
            api_key=self.settings.GOOGLE_API_KEY  # FIX Issue 7: Use self.settings
        )
        Settings.embed_model = self.embedding_model

        self.chunker = SemanticChunker(
            llm=self.llm,  # Pass LLM for Pure Agentic Chunking
            max_chunk_size=self.CHUNK_MAX_SIZE,  # FIX Issue 8: Use class constants
            min_chunk_size=self.CHUNK_MIN_SIZE
        )
        self.validator = KGValidator(strict_mode=False)
        self.entity_resolver = EntityResolver(
            embedding_model=self.embedding_model, # Pass Gemini Embedding
            merge_threshold=self.MERGE_THRESHOLD,  # FIX Issue 6: Use class constants
            use_embeddings=True
        )
        
        # Batch upserter for AuraDB production (initialized lazily)
        self._batch_upserter = None
        
        # Provenance manager for document-level overwrite (lazy init)
        self._provenance_manager = None
        
        # Extraction version for provenance
        self.extraction_version = ExtractionVersion.V3_ENTITY_RESOLUTION
        
        # Subscribe to inter-agent events
        if event_bus is not None:
            event_bus.subscribe('KAG_ANALYSIS_COMPLETED', self._on_kag_analysis_completed)
            self.logger.info("Subscribed to KAG_ANALYSIS_COMPLETED")
    
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

    async def _get_embedding_model(self):
        """Get embedding model (helper for async consistency)"""
        return self.embedding_model
    
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
            # FIX Issue 3: Strip input strings
            document_content = kwargs.get("document_content")
            document_title = (kwargs.get("document_title") or "Untitled").strip()
            document_type = (kwargs.get("document_type") or "LECTURE").strip()
            force_reprocess = kwargs.get("force_reprocess", False)
            
            # GLOBAL THEME: Domain is REQUIRED for accurate LLM extraction
            # Source: LightRAG (Guo 2024) - global theme helps LLM understand context
            user_domain = kwargs.get("domain")
            if not user_domain:
                # Try auto-suggest from document title/content
                from backend.config.domains import get_domain_registry
                registry = get_domain_registry()
                suggested = registry.suggest_domain(f"{document_title} {document_content[:500]}")
                if suggested:
                    user_domain = suggested.code
                    self.logger.info(f"🎯 Auto-suggested domain: {user_domain}")
                else:
                    # Fallback to LLM classification (existing behavior)
                    user_domain = await self._extract_domain(document_title, document_content)
                    self.logger.info(f"🤖 LLM-classified domain: {user_domain}")
            else:
                user_domain = user_domain.lower().strip()
                self.logger.info(f"📌 Admin-provided domain: {user_domain}")
            
            # Store domain for use in extraction layers
            self._current_domain = user_domain
            
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
                content=document_content,
                force_override=force_reprocess  # FIX Issue 5: Pass force flag
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
            # STEP 2: Pure Agentic Chunking (AI-driven)
            # Routes to MultiDocFusion for large docs (>10K tokens)
            # ========================================
            chunks = await self.chunker.chunk_with_ai(
                document_content, 
                document_id,
                document_title,
                domain=user_domain  # Pass domain for MultiDocFusion context
            )
            chunk_stats = self.chunker.get_stats(chunks)
            
            self.logger.info(f"🧠 Agentic Chunker: {len(chunks)} semantic blocks")
            
            await self.document_registry.update_status(
                document_id, DocumentStatus.PROCESSING,
                chunk_count=len(chunks)
            )
            
            # ========================================
            # STEP 3: Per-Chunk Extraction (Parallel)
            # ========================================
            # FIX Gap 1: Use asyncio.gather for parallel processing
            
            semaphore = asyncio.Semaphore(self.MAX_CONCURRENCY)
            
            async def semaphore_wrapped_process(chunk, idx, total):
                async with semaphore:
                    self.logger.debug(f"Processing chunk {idx+1}/{total} (Parallel): {chunk.source_heading}")
                    return await self._process_single_chunk(chunk, document_title, document_id, self._current_domain)

            tasks = [
                semaphore_wrapped_process(chunk, i, len(chunks)) 
                for i, chunk in enumerate(chunks)
            ]
            
            processing_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            failed_chunks = []
            all_concepts = []
            all_relationships = []
            all_content_keywords = set()
            
            for idx, result in enumerate(processing_results):
                if isinstance(result, Exception):
                    failed_chunks.append({
                        "chunk_index": idx,
                        "error": str(result),
                        "heading": chunks[idx].source_heading
                    })
                    self.logger.error(f"❌ Chunk {idx+1} failed: {result}")
                    continue
                    
                chunk_concepts, chunk_relationships, chunk_keywords = result
                all_concepts.extend(chunk_concepts)
                all_relationships.extend(chunk_relationships)
                if chunk_keywords:
                    all_content_keywords.update(chunk_keywords)
            
            if len(failed_chunks) == len(chunks) and len(chunks) > 0:
                raise Exception(f"All {len(chunks)} chunks failed processing")
            
            self.logger.info(f"📦 Raw extraction: {len(all_concepts)} concepts, {len(all_relationships)} relationships")
            
            # ========================================
            # STEP 4: Entity Resolution (Scalable)
            # ========================================
            # FIX Gap 2: Retrieve only relevant candidates (Top-K / Name-based)
            # instead of loading the entire graph into memory.
            
            new_names = [c.get("name", "") for c in all_concepts if c.get("name")]
            
            if new_names:
                existing_concepts = await self._get_candidate_concepts(new_names)
                
                # Get relevant relationships for the candidates + new concepts
                # We need relationships connected to either set to make structural decisions
                candidate_ids = [c["concept_id"] for c in existing_concepts]
                new_ids = [c.get("concept_id") for c in all_concepts if c.get("concept_id")]
                
                # Combine relevant IDs for relationship lookup
                relevant_ids = list(set(candidate_ids + new_ids))
                existing_relationships = await self._get_candidate_relationships(relevant_ids)
            else:
                existing_concepts = []
                existing_relationships = []
            
            resolution_result = self.entity_resolver.resolve(
                new_concepts=all_concepts,
                existing_concepts=existing_concepts,
                new_relationships=all_relationships,
                existing_relationships=existing_relationships
            )
            
            # Update all_concepts/all_relationships to the RESOLVED versions
            # resolved_concepts contains (existing + truly_new)
            # We only want to validate/stage the TRULY NEW ones for this document's scope
            # but wait, it's better to validate the final resolved concepts to ensure overall graph integrity
            all_concepts = resolution_result.resolved_concepts
            all_relationships = resolution_result.resolved_relationships

            self.logger.info(
                f"🔗 Resolution complete: {resolution_result.stats['merged_to_existing']} merged to KG, "
                f"{resolution_result.stats['truly_new_concepts']} truly new concepts"
            )

            # ========================================
            # STEP 5: Validation (On Clean Data)
            # ========================================
            validation_result = self.validator.validate(all_concepts, all_relationships)
            
            if not validation_result.is_valid:
                self.logger.warning(f"⚠️ Validation issues found in resolved graph")
                
                fixed_concepts, fixed_relationships = self.validator.auto_fix(
                    all_concepts, all_relationships, validation_result
                )
                
                validation_result = self.validator.validate(fixed_concepts, fixed_relationships)
                all_concepts = fixed_concepts
                all_relationships = fixed_relationships
            
            if not validation_result.is_valid:
                await self.document_registry.update_status(
                    document_id, DocumentStatus.FAILED,
                    error_message="Validation failed post-resolution"
                )
                return self._error_response("Validation failed after entity resolution")
            
            self.logger.info(f"✅ Clean Graph Validated")
            
            await self.document_registry.update_status(
                document_id, DocumentStatus.VALIDATED
            )
            
            # ========================================
            # STEP 6: Create Staging Nodes (Audit Trail)
            # ========================================
            # Only stage what is actually being added
            await self._create_staging_nodes(
                document_id, all_concepts, all_relationships
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
            
            final_status = DocumentStatus.COMMITTED
            if failed_chunks:
                final_status = DocumentStatus.PARTIAL_SUCCESS
                self.logger.warning(f"⚠️ Processed with {len(failed_chunks)} failed chunks")

            await self.document_registry.update_status(
                document_id, final_status,
                concept_count=commit_result["concepts_created"],
                relationship_count=commit_result["relationships_created"],
                extracted_concept_ids=[c["concept_id"] for c in all_concepts],
                error_message=f"Failed {len(failed_chunks)} chunks" if failed_chunks else None
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
                    "concepts_merged": resolution_result.stats["merged_to_existing"],
                    "total_concepts": commit_result["concepts_created"],
                    "total_relationships": commit_result["relationships_created"],
                    "total_concepts": commit_result["concepts_created"],
                    "total_relationships": commit_result["relationships_created"],
                    "extraction_version": self.extraction_version.value,
                    "content_keywords": list(all_content_keywords)
                }
            )
            
            self.logger.info(f"✅ [V2] Extraction complete: {document_id}")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "document_id": document_id,
                "status": final_status.value,
                "failed_chunks": failed_chunks,
                "chunking": chunk_stats,
                "validation": validation_result.to_dict(),
                "resolution": resolution_result.to_dict(),
                "resolution": resolution_result.to_dict(),
                "commit": commit_result,
                "content_keywords": list(all_content_keywords)
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

    async def _process_single_chunk(self, chunk, document_title, document_id, domain: str = None):
        """Helper for parallel processing of a single chunk"""
        try:
            # Layer 1: Concept extraction (with Global Theme domain context)
            chunk_concepts = await self._extract_concepts_from_chunk(chunk, document_title, domain)
            
            # Layer 2: Relationship extraction (LightRAG + Global Theme)
            chunk_relationships = await self._extract_relationships_from_chunk(
                chunk, chunk_concepts, domain
            )
            
            # Layer 3: Metadata enrichment (with domain context)
            enriched_concepts = await self._enrich_metadata(chunk_concepts, domain)
            
            # Layer 4: Content Keywords (LightRAG)
            content_keywords = await self._extract_content_keywords(chunk)
            
            # Layer 5: Embedding Computation (Standard Pipeline)
            enriched_concepts = await self._compute_embeddings(enriched_concepts)
            
            # Add provenance to each concept
            for concept in enriched_concepts:
                concept["source_document_id"] = document_id
                concept["source_chunk_id"] = chunk.chunk_id
                concept["extraction_version"] = self.extraction_version.value
                concept["extracted_at"] = datetime.now().isoformat()
                
            return enriched_concepts, chunk_relationships, content_keywords
            
        except Exception as e:
            self.logger.error(f"Error processing chunk {chunk.chunk_id}: {e}")
            raise e
    
    # ===========================================
    # EXTRACTION METHODS
    # ===========================================
    
    async def _compute_embeddings(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compute embeddings for a list of concepts"""
        if not concepts:
            return concepts
            
        embed_model = await self._get_embedding_model()
        
        for concept in concepts:
            # Skip if already has embedding
            if concept.get("embedding") and len(concept["embedding"]) > 0:
                continue
                
            try:
                # Semantic Signature: Name + Description + Context
                # Include tags for better disambiguation power
                tags = " ".join(concept.get("semantic_tags", []) or [])
                text = f"{concept.get('name', '')} | {concept.get('context', '')} | {concept.get('description', '')} | {tags}"
                
                embedding = await embed_model.aget_text_embedding(text)
                concept["embedding"] = embedding
            except Exception as e:
                self.logger.error(f"⚠️ Failed to compute embedding for {concept.get('name')}: {e}")
                # Don't fail the concept, just missing embedding
                concept["embedding"] = []
                
        return concepts

    async def _extract_concepts_from_chunk(
        self, chunk: SemanticChunk, document_title: str, domain: str = None
    ) -> List[Dict[str, Any]]:
        """
        Extract concepts from a single chunk.
        
        LLM provides raw fields (name, context, description, etc.)
        Backend builds concept_code using ConceptIdBuilder.
        
        Args:
            chunk: SemanticChunk to extract from
            document_title: Document title for context
            domain: Global Theme domain for LLM context (LightRAG principle)
        """
        # GLOBAL THEME: Include domain in prompt for better LLM accuracy
        domain_context = f"\nDomain/Subject Area: {domain.upper()}" if domain else ""
        
        prompt = f"""
You are extracting learning concepts from a document section.
{domain_context}
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
            
            # Use provided domain or fallback to extraction
            if not domain:
                domain = await self._extract_domain(document_title, chunk.content)
            builder = get_concept_id_builder(domain=domain)
            
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
    
    async def _extract_domain(self, document_title: str, document_content: str = "", user_domain: str = None) -> str:
        """
        Extract domain from document title for concept_code generation.
        
        Strategy:
        0. Use user_domain if provided.
        1. Try KNOWN_DOMAINS lookup (fast, cheap).
        2. If not found, use LLM to classify domain (fallback).
        """
        # Step 0: User Input (High Priority)
        if user_domain:
            return user_domain.lower().strip()
            
        title_lower = document_title.lower()
        
        # Step 1: Try KNOWN_DOMAINS lookup (fast path)
        for keyword, domain in self.KNOWN_DOMAINS.items():
            if keyword in title_lower:
                return domain
        
        # Step 2: LLM Fallback - classify domain using AI
        self.logger.info(f"🤖 Domain not in KNOWN_DOMAINS, using LLM classification for: {document_title}")
        
        try:
            # Take first 1000 chars of content for context (if available)
            content_preview = document_content[:1000] if document_content else ""
            
            prompt = f"""Classify this educational document into a domain/subject area.

Document Title: {document_title}
Content Preview: {content_preview}

Known domains (prefer these if applicable):
{', '.join(sorted(set(self.KNOWN_DOMAINS.values())))}

Instructions:
1. If document fits a known domain, return that domain name
2. If document is a new subject, suggest a short domain name (lowercase, no spaces, max 15 chars)
3. Domain should be general enough to group related concepts (e.g., "sql" not "select_statement")

Return ONLY the domain name, nothing else. Example: sql
"""
            response = await self.llm.acomplete(prompt)
            llm_domain = response.text.strip().lower().replace(" ", "_")[:15]
            
            # Sanitize LLM response
            domain = ''.join(c for c in llm_domain if c.isalnum() or c == '_')
            
            if domain:
                self.logger.info(f"✅ LLM classified domain: {domain}")
                return domain
        except Exception as e:
            self.logger.warning(f"LLM domain classification failed: {e}")
        
        # Step 3: Ultimate fallback - first word of title
        first_word = title_lower.split()[0] if title_lower.split() else "course"
        return first_word[:10].replace(" ", "_")
    
    async def _extract_relationships_from_chunk(
        self, chunk: SemanticChunk, concepts: List[Dict], domain: str = None
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships between concepts with SPR-compliant fields.
        
        Args:
            chunk: SemanticChunk for context
            concepts: List of concepts to find relationships between
            domain: Global Theme domain for LLM context (LightRAG principle)
        
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
        
        # GLOBAL THEME: Include domain context for better relationship accuracy
        domain_context = f"\nDomain/Subject Area: {domain.upper()}\n" if domain else ""
        
        prompt = LIGHTRAG_RELATIONSHIP_EXTRACTION_PROMPT.format(
            concept_list=concept_list,
            domain_context=domain_context
        )
        try:
            response = await self.llm.acomplete(prompt)
            return self._parse_json_array(response.text)
        except Exception as e:
            self.logger.error(f"Relationship extraction error: {e}")
            return []
    
    async def _enrich_metadata(self, concepts: List[Dict], domain: str = None) -> List[Dict]:
        """
        Layer 3: Enrich with metadata.
        
        Args:
            concepts: List of concepts to enrich
            domain: Global Theme domain for LLM context (LightRAG principle)
        """
        if not concepts:
            return []
        
        # GLOBAL THEME: Include domain context for better classification
        domain_context = f"Domain/Subject Area: {domain.upper()}\n\n" if domain else ""
        
        # FIX Issue 2: Include full concept context for better Bloom level assessment
        concept_details = "\n".join([
            f"- {c.get('concept_id')}: {c.get('name', '')} - {c.get('description', '')[:100]}"
            for c in concepts
        ])
        
        prompt = f"""
{domain_context}Add metadata to these concepts:

{concept_details}

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
                else:
                    # FIX Issue 3: Log warning for missing metadata
                    self.logger.warning(f"No metadata found for concept: {cid}")
            
            return concepts
        except Exception as e:
            self.logger.error(f"Metadata enrichment error: {e}")
            return concepts
    
    async def _extract_content_keywords(self, chunk: SemanticChunk) -> List[str]:
        """Layer 4: Extract LightRAG Content Keywords"""
        prompt = LIGHTRAG_CONTENT_KEYWORDS_PROMPT.format(
            content=chunk.content[:2000]  # Limit context window if needed
        )
        try:
            response = await self.llm.acomplete(prompt)
            result = self._parse_json_object(response.text)
            return result.get("content_keywords", [])
        except Exception as e:
            self.logger.warning(f"Content keyword extraction failed for chunk {chunk.chunk_id}: {e}")
            return []
    
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
    
    async def _get_candidate_concepts(self, lookup_names: List[str]) -> List[Dict]:
        """
        Get relevant existing concepts based on Fuzzy Fulltext Search.
        FIX Gap 2: Scalable retrieval + Fuzzy Matching to catch Synonyms.
        """
        if not lookup_names:
            return []
            
        neo4j = self.state_manager.neo4j
        
        # Construct Lucene Query: "name1~0.8 OR name2~0.8 ..."
        # We sanitize names to prevent Lucene syntax errors
        sanitized_names = [
            n.replace('"', '').replace("'", "").replace('~', '') 
            for n in lookup_names
            if n
        ]
        
        if not sanitized_names:
            return []
            
        lucene_query = " OR ".join([f'"{n}"~0.8' for n in sanitized_names])
        
        try:
            # Try Fulltext Search
            result = await neo4j.run_query(
                """
                // Scientific Basis: Approximate String Matching
                // Source: Navarro, G. (2001). "A guided tour to approximate string matching."
                // Application: Handling phonetic/typo variations in concept names.
                CALL db.index.fulltext.queryNodes("conceptNameIndex", $query) 
                YIELD node, score
                RETURN DISTINCT node.concept_id as concept_id,
                       node.name as name,
                       node.description as description,
                       node.difficulty as difficulty,
                       node.semantic_tags as semantic_tags
                LIMIT 100
                """,
                query=lucene_query
            )
            if result:
                return result
                
        except Exception as e:
            self.logger.warning(f"⚠️ Fulltext Search failed (falling back to legacy filter): {e}")
        
        # Fallback to exact/contains match if Index missing or query fails
        result = await neo4j.run_query(
            """
            // NOTE: Global Summarization (Leiden Algorithm) is NOT implemented (Local Search Only)
            // See: Edge, D., et al. (2024) - GraphRAG
            UNWIND $names AS lookup_name
            MATCH (c:CourseConcept)
            WHERE toLower(c.name) = toLower(lookup_name) 
               OR toLower(c.name) CONTAINS toLower(lookup_name)
               OR toLower(lookup_name) CONTAINS toLower(c.name)
            RETURN DISTINCT c.concept_id as concept_id,
                   c.name as name,
                   c.description as description,
                   c.difficulty as difficulty,
                   c.semantic_tags as semantic_tags
            LIMIT 100
            """,
            names=lookup_names
        )
        return result if result else []

    async def _ensure_fulltext_index(self):
        """Ensure Neo4j fulltext index exists"""
        if self._index_checked:
            return
            
        try:
            neo4j = self.state_manager.neo4j
            # Create fulltext index on 'name' property of 'CourseConcept' nodes
            # Syntax compatible with Neo4j 5.x
            await neo4j.run_query("""
                CREATE FULLTEXT INDEX conceptNameIndex IF NOT EXISTS
                FOR (n:CourseConcept) ON EACH [n.name]
            """)
            self._index_checked = True
            self.logger.info("Checked/Created 'conceptNameIndex' fulltext index")
        except Exception as e:
            self.logger.warning(f"Could not create fulltext index: {e}")
    
    async def _get_candidate_relationships(self, concept_ids: List[str]) -> List[Dict]:
        """Get existing relationships ONLY for the relevant concepts"""
        if not concept_ids:
            return []
            
        neo4j = self.state_manager.neo4j
        result = await neo4j.run_query(
            """
            MATCH (a:CourseConcept)-[r]->(b:CourseConcept)
            WHERE a.concept_id IN $ids OR b.concept_id IN $ids
            RETURN a.concept_id as source,
                   b.concept_id as target,
                   type(r) as relationship_type
            """,
            ids=concept_ids
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
            domain: str (Optional) - User-provided domain override
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
            
            # Ensure Fulltext Index for better Entity Resolution
            await self._ensure_fulltext_index()
            
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
            # STEP 0: Domain Extraction (Dynamic)
            # ========================================
            user_domain = kwargs.get("domain")
            domain_name = await self._extract_domain(document_title, document_content, user_domain)
            self.logger.info(f"🏷️ Domain identified: {domain_name} (User-provided: {bool(user_domain)})")
            
            # Use a builder factory with the domain
            self.concept_builder = get_concept_id_builder(domain_name)
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
                
                # Compute embeddings (NEW for Vector Search)
                # Reuse helper to modify concepts in-place
                enriched_concepts = await self._compute_embeddings(enriched_concepts)
                
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
                        "confidence": 0.85,
                        "embedding": concept.get("embedding", [])  # Pass to provenance
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
            # Use unified payload schema matching execute()
            await self.send_message(
                receiver="planner",
                message_type="COURSEKG_UPDATED",
                payload={
                    "document_id": document_id,
                    "document_title": document_title,
                    "concepts_added": result["canonical"]["concepts_rebuilt"],
                    "concepts_merged": 0,  # Provenance mode doesn't merge, it overwrites
                    "total_concepts": result["snapshots"]["concepts_inserted"],
                    "total_relationships": result["snapshots"]["relationships_inserted"],
                    "extraction_version": self.extraction_version.value,
                    # Additional provenance info
                    "was_overwrite": was_overwrite
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

    # ==========================================
    # EVENT HANDLERS
    # ==========================================
    
    async def _on_kag_analysis_completed(self, event: Dict[str, Any]):
        """
        Handle KAG_ANALYSIS_COMPLETED event from KAG Agent.
        
        Uses analysis recommendations to improve Course KG.
        
        Event payload:
        {
            'recommendations': list,
            'bottleneck_concepts': list of {concept_id, avg_mastery}
        }
        """
        try:
            recommendations = event.get('recommendations', [])
            bottleneck_concepts = event.get('bottleneck_concepts', [])
            analysis_timestamp = event.get('timestamp', datetime.now().isoformat())
            
            self.logger.info(f"📊 Received KAG analysis: {len(recommendations)} recommendations, {len(bottleneck_concepts)} bottlenecks")
            
            if self.state_manager and hasattr(self.state_manager, 'neo4j'):
                neo4j = self.state_manager.neo4j
                
                # Issue 6 Fix: Persist recommendations to Course KG
                if recommendations:
                    for rec in recommendations:
                        self.logger.info(f"📋 Recommendation: {rec}")
                    
                    # Store recommendations as a KAGAnalysis node
                    await neo4j.run_query("""
                        CREATE (a:KAGAnalysis {
                            analysis_id: $analysis_id,
                            recommendations: $recommendations,
                            bottleneck_count: $bottleneck_count,
                            created_at: datetime()
                        })
                    """,
                        analysis_id=f"kag_{analysis_timestamp}",
                        recommendations=recommendations,
                        bottleneck_count=len(bottleneck_concepts)
                    )
                    self.logger.info(f"💾 Persisted {len(recommendations)} recommendations to KAGAnalysis node")
                
                # Issue 7 Fix: Atomic reset + set in single query
                if bottleneck_concepts:
                    batch_data = [
                        {
                            "concept_id": c.get("concept_id"),
                            "avg_mastery": c.get("avg_mastery", 0)
                        }
                        for c in bottleneck_concepts
                        if c.get("concept_id")
                    ]
                    
                    if batch_data:
                        # Atomic: Reset all + Set new in one transaction
                        await neo4j.run_query("""
                            // Step 1: Reset all bottleneck flags
                            MATCH (c:CourseConcept)
                            WHERE c.is_bottleneck = true
                            SET c.is_bottleneck = false,
                                c.bottleneck_cleared_at = datetime()
                            WITH count(c) AS reset_count
                            
                            // Step 2: Set new bottlenecks (in same transaction)
                            UNWIND $batch AS row
                            MATCH (c:CourseConcept {concept_id: row.concept_id})
                            SET c.is_bottleneck = true,
                                c.avg_mastery = row.avg_mastery,
                                c.flagged_at = datetime()
                            RETURN count(c) AS flagged_count
                        """, batch=batch_data)
                        
                        self.logger.info(f"🚩 Flagged {len(batch_data)} bottleneck concepts in Course KG (atomic)")
                
        except Exception as e:
            self.logger.error(f"Error in _on_kag_analysis_completed: {e}")
            # Re-raise to notify event bus of failure
            raise
