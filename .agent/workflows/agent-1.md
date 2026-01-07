---
description: Deep Dive into Agent 1 (Knowledge Extraction / LightRAG).
---
# Agent 1: Knowledge Extraction (The "Hippocampus")

This workflow provides a comprehensive technical view of Agent 1, from Scientific Theory to Code Implementation.

// turbo-all

1.  **🔬 Scientific Basis (Whitebox Analysis)**
    *Review the dual-graph indexing theory (LightRAG).*
    `view_file docs/AGENT_1_WHITEBOX.md`

2.  **🏗️ Code Structure: Pipeline Entry**
    *The `execute()` method orchestrates parallel document processing.*
    `view_file backend/agents/knowledge_extraction_agent.py --start_line 171 --end_line 260`

3.  **🧠 Code Structure: Entity Extraction**
    *The `_extract_entities_and_relations()` method implementation.*
    `view_file backend/agents/knowledge_extraction_agent.py --start_line 429 --end_line 460`

4.  **🧪 Code Structure: Resolution Logic**
    *How fuzzy matching works for deduplication.*
    `view_file backend/agents/knowledge_extraction_agent.py --start_line 744 --end_line 805`

5.  **✅ Verification**
    *Run the test script to verify the offline ingestion pipeline.*
    `python scripts/test_agent_1.py`
