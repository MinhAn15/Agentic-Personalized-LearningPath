---
description: Deep Dive into Agent 3 (Path Planner / Tree of Thoughts).
---
# Agent 3: Path Planner (The "Strategist")

This workflow provides a comprehensive technical view of Agent 3, focusing on its Tree of Thoughts (ToT) lookahead capabilities.

// turbo-all

1.  **🔬 Scientific Basis (Whitebox Analysis)**
    *Review the BFS (Beam Search) and Lookahead theory.*
    `view_file docs/AGENT_3_WHITEBOX.md`

2.  **🧠 Code Structure: Tree of Thoughts (ToT)**
    *The Beam Search implementation (BFS with Lookahead).*
    `view_file backend/agents/path_planner_agent.py --start_line 170 --end_line 223`

3.  **🔮 Code Structure: Mental Simulation**
    *Evaluating future path viability (Self-Reflection).*
    `view_file backend/agents/path_planner_agent.py --start_line 225 --end_line 268`

4.  **💡 Code Structure: Thought Generator**
    *Generating candidate next steps (Expansion).*
    `view_file backend/agents/path_planner_agent.py --start_line 270 --end_line 306`

5.  **✅ Verification**
    *Run the test script to verify "Strategic" path selection.*
    `python scripts/test_agent_3_tot.py`
