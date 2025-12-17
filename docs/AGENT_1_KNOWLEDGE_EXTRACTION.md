# Agent 1: Knowledge Extraction Agent (V2)

## Overview

**File:** `backend/agents/knowledge_extraction_agent.py`  
**Lines:** 860 | **Methods:** 21

Production-grade agent for building the Course Knowledge Graph from educational documents.

## Key Features

1. **Document Registry** - Idempotent ingestion (no duplicate processing)
2. **Semantic Chunking** - Split documents by heading/section
3. **Staging Graph Pattern** - Extract → Validate → Promote workflow
4. **Batch Operations** - Optimized for AuraDB performance

## Core Enums

```python
RelationshipType:  # 7 relationship types
    REQUIRES, IS_PREREQUISITE_OF, NEXT, REMEDIATES,
    HAS_ALTERNATIVE_PATH, SIMILAR_TO, IS_SUB_CONCEPT_OF

BloomLevel:  # Bloom's Taxonomy
    REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE
```

## Main Methods

| Method                                | Purpose                                     |
| ------------------------------------- | ------------------------------------------- |
| `execute()`                           | Main ingestion pipeline                     |
| `_extract_concepts_from_chunk()`      | LLM-based concept extraction                |
| `_extract_relationships_from_chunk()` | Extract 7 relationship types with weights   |
| `_enrich_metadata()`                  | Add Bloom level, difficulty, time estimates |
| `_create_staging_nodes()`             | Create temporary nodes for validation       |
| `_promote_to_course_kg()`             | Batch MERGE to production CourseConcept     |

## Algorithm Flow

```
Document → Semantic Chunking → LLM Extraction → Staging Graph
    → Deduplication Check → Batch MERGE → CourseConcept Nodes
```

## Dependencies

- `SemanticChunker` - Heading-based document splitting
- `Neo4jBatchUpserter` - Batch UNWIND operations
- `ProvenanceManager` - Track source documents
- `ConceptIdBuilder` - Build hierarchical concept codes

## Output

- CourseConcept nodes with 15+ properties
- 7 relationship types with weight/dependency fields
- Provenance tracking (source_document_ids)
