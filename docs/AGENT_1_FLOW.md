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
    1.  Calculate SHA-256 checksum of file content.
    2.  Check Redis/DB if checksum exists.
    3.  If exists and `force_reprocess=False` -> **SKIP** (Return "SKIPPED").
    4.  Else -> Register new document attempt.

### Step 2: Semantic Chunking (AI-Driven)
*   **Component**: `SemanticChunker`
*   **Logic**:
    1.  **Architect**: LLM identifies logical boundaries (Intro, Concept A, Concept B).
    2.  **Refiner**: LLM critiques boundaries for context consistency.
    3.  **Executor**: Maps logical boundaries to exact text offsets.
*   **Output**: List of `SemanticChunk` objects.

### Step 3: 3-Layer Extraction
*   **Component**: `_process_chunk_layers`
*   **Logic**:
    *   **Layer 1 (Concepts)**: Extract main entities + `concept_id` generation.
    *   **Layer 2 (Relationships)**: Identify connections (`IS_PREREQUISITE_OF`, `SIMILAR_TO`).
    *   **Layer 3 (Metadata)**: Bloom's Level, Estimated Time, Tags.

### Step 4: Component Validation
*   **Component**: `KGValidator`
*   **Logic**:
    *   Check 14 Rules (e.g., "No circular prerequisites", "Concept must have description").
    *   If invalid -> Attempt **Auto-Fix** or discard.

### Step 5: Entity Resolution
*   **Component**: `EntityResolver`
*   **Logic**:
    1.  **Embed**: Vectorize extracted concept names/definitions.
    2.  **Cluster**: Group similar concepts (e.g., "Inner Join" vs "INNER JOIN").
    3.  **Merge**: Combine duplicates into a single canonical concept.

### Step 6: Staging & Persistence
*   **Component**: `Neo4jBatchUpserter`
*   **Logic**:
    1.  Write valid concepts to `StagingConcept` nodes.
    2.  Run Cypher queries to Promote Staging -> `CourseConcept`.
    3.  Create Vector Index entries.

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
(sql.basics.select)-[:IS_PREREQUISITE_OF]->(sql.joins.inner)
```

## 5. Potential Issues / To-Do
- [ ] **Conflict Resolution**: How strictly to merge concepts? (Currently threshold = 0.85).
- [ ] **Error Handling**: Partial failures in batch upsert need manual review mechanism.
