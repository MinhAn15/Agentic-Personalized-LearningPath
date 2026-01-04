# Walkthrough: Scientific Refinement (Agent 1 - Knowledge Extraction / LightRAG)

## 1. Goal

Upgrade Agent 1 from standard GraphRAG to **LightRAG (Guo et al. 2024)**.

* **Gap Fixed**: Standard RAG loses global context.
* **Solution**: **Dual-Level Retrieval** via "Edge-Attribute Thematic Indexing" and "Content Keyword" extraction.

## 2. Changes

### Backend (`knowledge_extraction_agent.py`)

* **Layer 2 (Relationship)**: Updated prompt to extract `keywords` on every edge (e.g., ["prerequisites", "database theory"]). These serve as the "Global Theme" index.
* **Layer 4 (Content)**: Added `_extract_content_keywords` to identify high-level topics (e.g., "SQL Optimization") from the text chunk.
* **Integration**: `execute` now returns `content_keywords` and persists them to `DocumentRegistry`.

### Data Model (`document_registry.py`)

* **Added**: `content_keywords: list` field to `DocumentRecord` dataclass to ensure high-level metadata is preserved.

### Prompts (`prompts.py`)

* **Added**: `LIGHTRAG_RELATIONSHIP_EXTRACTION_PROMPT`
* **Added**: `LIGHTRAG_CONTENT_KEYWORDS_PROMPT`

## 3. Verification

* **Script**: `scripts/test_agent_1.py`
* **Test Case**: Mocked the extraction pipeline to ensure `content_keywords` and `relationship.keywords` are correctly propagated from the LLM to the final result object.
* **Result**: Pipeline successfully captures and returns both structural (graph) and thematic (keyword) data.

## 4. Scientific Alignment

* **LightRAG Principle**: "Graph Pattern for detailed questions, High-Level Keywords for broad questions."
* **Implementation**:
  * **Low-Level**: Entity Nodes + Relationships.
  * **High-Level**: `content_keywords` (Document-level) + Edge Keywords (Thematic).
