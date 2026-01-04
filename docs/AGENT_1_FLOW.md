# Agent 1: Knowledge Extraction - Flow Documentation

> **Status**: Verified via Code Audit
> **Source Code**: `backend/agents/knowledge_extraction_agent.py`

## 1. High-Level Overview
Agent 1 is the "Librarian". It takes raw files (PDFs, Videos, Text) and converts them into a structured **Course Knowledge Graph** in Neo4j. It is designed to be **idempotent** (can run multiple times without duplicating data).

## 2. Input & Output

| Type | Data Structure | Description |
|------|----------------|-------------|
| **Input** | `DocumentInput` | `{ "file_path": str, "metadata": dict }` |
| **Output** | `KnowledgeExtractionOutput` | `{ "status": "COMPLETED", "stats": {...} }` |
| **Side Effect** | **Neo4j Graph** | Nodes (`CourseConcept`), Edges (`REQUIRES`, `IS_A`, etc.) |
| **Side Effect** | **Vector DB** | Embeddings for Semantic Search |

## 3. Detailed Execution Flow

### Step 1: Input Ingestion & Registry Check
*   **Component**: `DocumentRegistry`
*   **Logic**:
    1.  Calculates checksum.
    2.  Checks Registry.
    3.  **Dynamic Domain**: If `domain` is provided by user, it overrides auto-classification.
    4.  If existing & valid -> SKIP.

### Step 2: Semantic Chunking (AI-Driven)
*   **Component**: `SemanticChunker`
*   **Logic**:
    *   LLM-based segmentation (Intro, Sections).
*   **Output**: SemanticChunks.

### Step 3: 3-Layer Extraction
*   **Component**: `_process_chunk_layers`
*   **Logic**:
    *   **Layer 1 (Concepts)**: Key Concept Extraction + Stable ID generation (`{domain}.{name}`).
    *   **Layer 2 (Relationships)**: Prerequisite/Similarity detection.
    *   **Layer 3 (Metadata)**: Bloom's Level, Tags.
    *   **Layer 4 (Content Keywords)**: High-level thematic keywords for the chunk (LightRAG).
*   **Performance**: Parallel processing with `asyncio.gather` (Limit 5).

### Step 4: Component Validation
*   **Component**: `KGValidator`
*   **Logic**:
    *   14-Rule validation (Consistency check).

### Step 5: Entity Resolution
*   **Component**: `EntityResolver`
*   **Logic**:
    1.  **Candidate Retrieval**:
        *   Uses **Neo4j Fulltext Search** (`conceptNameIndex`) with Fuzzy Matching (`~0.8`) to find existing concepts.
        *   Fallback to `CONTAINS` if index missing.
    2.  **Filter**: Identifies potential duplicates or synonyms.
    3.  **Merge**: Unifies new concept with existing canonical node.

### Step 6: Staging & Persistence
*   **Component**: `Neo4jBatchUpserter`
*   **Logic**:
    *   Batch writes to Staging nodes.
    *   Promotes to `CourseConcept`.
    *   Creates Vector Index.

### Step 7: Finalization
*   **Event**: Emit `COURSEKG_UPDATED`.
*   **Log**: Update `DocumentRegistry` status to `PROCESSED`.

## 4. Key Data Structures

### Node: `CourseConcept`
```json
{
  "concept_id": "sql.joins.inner",
  "name": "INNER JOIN",
  "definition": "Returns rows when there is a match in both tables.",
  "bloom_level": "UNDERSTAND",
  "difficulty": 0.4
}
```

### Relationship: `IS_PREREQUISITE_OF`
```cypher
(sql.basics.select)-[:IS_PREREQUISITE_OF {
    keywords: ["query structure", "data retrieval"],
    summary: "SELECT is fundamental for retrieving data before joining."
}]->(sql.joins.inner)
```

## 5. Potential Issues / To-Do
- [ ] **Conflict Resolution**: How strictly to merge concepts? (Currently threshold = 0.85).
- [ ] **Error Handling**: Partial failures in batch upsert need manual review mechanism.
