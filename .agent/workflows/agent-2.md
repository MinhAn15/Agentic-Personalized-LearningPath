---
description: Deep Dive into Agent 2 (Profiler / Semantic LKT).
---
# Agent 2: Profiler (The "Semantic Mapper")

This workflow provides a comprehensive technical view of Agent 2, focusing on its ability to map learner states without historical data (Cold Start).

// turbo-all

1.  **🔬 Scientific Basis (Whitebox Analysis)**
    *Review the Semantic LKT and Cold Start theory.*
    `view_file docs/AGENT_2_WHITEBOX.md`

2.  **🏗️ Code Structure: Goal Parsing**
    *Extracting Intent, Topic, and Constraints from natural language.*
    `view_file backend/agents/profiler_agent.py --start_line 346 --end_line 404`

3.  **🧠 Code Structure: Semantic Diagnostic**
    *The "Cold Start" Logic: Graph RAG -> Vector -> Cypher Fallback.*
    `view_file backend/agents/profiler_agent.py --start_line 460 --end_line 574`

4.  **📉 Code Structure: Profile Vectorization**
    *Creating the 10-Dimensional Learner State Vector.*
    `view_file backend/agents/profiler_agent.py --start_line 636 --end_line 713`

5.  **✅ Verification**
    *Run the test script to verify "Cold Start" detection.*
    `python scripts/test_agent_2_lkt.py`
