# Scientific Validation Journal: Agent 1 (Knowledge Extraction)

## 1. Audit Summary
*   **Agent**: Knowledge Extraction
*   **Source Code**: `backend/agents/knowledge_extraction_agent.py`
*   **Scientific Basis**: `docs/SCIENTIFIC_BASIS.md`
*   **Status**: 🟡 PARTIALLY VERIFIED

## 2. Claim Verification

| Claim | Source Paper | Status | Evidence in Code |
| :--- | :--- | :--- | :--- |
| **Fuzzy Search** | Navarro (2001) | ✅ **VERIFIED** | `_get_candidate_concepts` uses `~0.8` Lucene operator (Line 765). Fallback to `CONTAINS` exists. |
| **Ontology-Driven** | Gruber (1993) | ✅ **VERIFIED** | Prompt (Line 489) enforces strict JSON schema. `RelationshipType` Enum (Line 46) enforces edge types. |
| **GraphRAG (Local)** | Edge et al. (2024) | ✅ **VERIFIED** | Extracts triples `(Subject, Predicate, Object)` and uses Entity Resolution to merge nodes. |
| **GraphRAG (Global)** | Edge et al. (2024) | ❌ **MISSING** | The paper describes "Community Detection" (Leiden) and "Hierarchical Summarization". The current agent *extracts* the graph but does not *summarize* communities. |

## 3. Analysis & Gaps
### Gap 1: Missing "Global Search" Mechanism
The Microsoft GraphRAG paper distinguishes between:
1.  **Local Search**: Traversing neighbors (Current Implementation ✅).
2.  **Global Search**: Aggregating community summaries to answer "What is the main theme?" (Missing ❌).

**Impact**: Use cases requiring high-level course abstraction (e.g., "Generate a syllabus based on these 500 documents") will rely on simple LLM context window rather than GraphRAG's summarized hierarchy.

## 5. NotebookLM Validation Feedback (2026-01-03)
*   **Fuzzy Search vs. Community Detection**:
    *   NotebookLM confirmed that Fuzzy Search is valid for *Entity Resolution* (cleaning data) but **does not replace Community Detection**.
    *   To find "Topic Clusters" (e.g., "All SQL Optimization concepts"), we need structural clustering, not just name similarity.
*   **Global Summarization Criticality**:
    *   Confirmed as **CRITICAL** for high-level queries (e.g., "Summarize the course module").
    *   Local RAG (current) is sufficient for prerequisite checking (A->B), but fails at "Sensemaking" (What is the big picture?).
*   **Recommendation**:
    *   Implement **Leiden Algorithm** recursively for Hierarchical Community Detection.
    *   This is a "Future Refinement" (Phase 4), as the current TUTORING goal (Local Pathfinding) is functional without it.

**Final Status**: 🟡 **Gap Confirmed** (Missing Leiden/Global Layer). Codebase is valid for *Local* operations but incomplete for *Global* RAG claims.
