---
description: Deep Dive into Agent 1 (Knowledge Extraction / LightRAG).
---
# Agent 1: Knowledge Extraction (The "Hippocampus")

This workflow provides a comprehensive technical view of Agent 1, from Scientific Theory to Code Implementation.

// turbo-all

1.  **🔬 Scientific Basis (Whitebox Analysis)**
    *Review the dual-graph indexing theory (LightRAG), Global Theme/Domain Context, and 3-Layer Extraction mechanism.*
    `view_file docs/AGENT_1_WHITEBOX.md`

2.  **🌐 NEW: Global Theme (Domain Context) - LightRAG Principle**
    *Domain registry with predefined domains and add-new mechanism.*
    `view_file backend/config/domains.py`

3.  **🏗️ Code Structure: Pipeline Entry**
    *The `execute()` method with domain determination (Admin → Auto-suggest → LLM fallback).*
    `view_file backend/agents/knowledge_extraction_agent.py --start_line 185 --end_line 275`

4.  **🧠 Code Structure: 3-Layer Extraction (with Domain Injection)**
    *Layer 1 (Concepts + Domain), Layer 2 (Relationships + Domain), Layer 3 (Metadata + Domain).*
    `view_file backend/agents/knowledge_extraction_agent.py --start_line 465 --end_line 570`

5.  **🔗 Code Structure: Entity Resolution**
    *3-Way Similarity với MERGE_THRESHOLD=0.80 để dedup semantic duplicates.*
    `view_file backend/utils/entity_resolver.py --start_line 68 --end_line 150`

6.  **🧪 Code Structure: Fulltext Search Fallback**
    *How fuzzy matching works for deduplication trong Neo4j.*
    `view_file backend/agents/knowledge_extraction_agent.py --start_line 770 --end_line 840`

7.  **✅ Verification**
    *Run the test script to verify the offline ingestion pipeline.*
    `python scripts/test_agent_1.py`
