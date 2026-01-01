---
description: Display the detailed code structure and key methods of Agent 1.
---
# Agent 1 Code Structure Walkthrough

This workflow opens the key code segments of `knowledge_extraction_agent.py` to demonstrate the "Engineering Pipeline" structure (Parallelism, 3-Layer Extraction, Entity Resolution).

// turbo-all

1. **Imports & Constants (Lines 1-65)**
   *Defines Dependencies and Configs like MAX_CONCURRENCY.*
   `view_file backend/agents/knowledge_extraction_agent.py --start_line 1 --end_line 65`

2. **Public Interface: execute() (Lines 171-260)**
   *The Main Entry Point & Parallel Orchestrator (Asyncio Gather).*
   `view_file backend/agents/knowledge_extraction_agent.py --start_line 171 --end_line 260`

3. **Core Logic: _process_single_chunk() (Lines 429-460)**
   *The Controller for processing one text chunk.*
   `view_file backend/agents/knowledge_extraction_agent.py --start_line 429 --end_line 460`

4. **Entity Resolution: _get_candidate_concepts() (Lines 744-805)**
   *The Scalability Logic with Fulltext Search & Fuzzy Matching.*
   `view_file backend/agents/knowledge_extraction_agent.py --start_line 744 --end_line 805`
