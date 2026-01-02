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

## 4. Next Steps (User Action)
Run **NotebookLM** with the following prompt to determine if we *need* to implement Leiden Community Detection now or if our "Concept-Centric" approach is sufficient for a Tutoring System (vs a Summarization System).

**Context for NotebookLM**:
> "My Knowledge Extraction Agent successfully builds a graph with Entity Resolution (Fuzzy Search ~0.8). However, I have not implemented the 'Hierarchical Community Summarization' (Leiden algorithm) described in the GraphRAG paper. 
> My system's goal is personalized *Tutoring* (finding a specific path for a student), not general *Summarization* of the dataset."

**Question for NotebookLM**:
> "Given my goal of 'Personalized Pathfinding' (finding A->B->C), is the missing 'Global Summarization' layer critical? Or is a standard Local Graph Traversal sufficient for checking prerequisites (Grounding)?"
