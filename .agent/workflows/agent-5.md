---
description: Deep Dive into Agent 5 (Evaluator / JudgeLM).
---
# Agent 5: Evaluator (The "AI Judge")

This workflow provides a comprehensive technical view of Agent 5, focusing on its bias-minimized grading and error classification.

// turbo-all

1.  **🔬 Scientific Basis (Whitebox Analysis)**
    *Review the JudgeLM and Rubric-based evaluation theory.*
    `view_file docs/AGENT_5_WHITEBOX.md`

2.  **⚖️ Code Structure: JudgeLM Scoring**
    *The Reference-as-Prior scoring logic (Zhu 2023).*
    `view_file backend/agents/evaluator_agent.py --start_line 392 --end_line 487`

3.  **🏷️ Code Structure: Error Classification**
    *Categorizing mistakes (Conceptual vs Procedural).*
    `view_file backend/agents/evaluator_agent.py --start_line 489 --end_line 530`

4.  **📈 Code Structure: Mastery Prediction (LKT)**
    *Zero-shot mastery update using textual history.*
    `view_file backend/agents/evaluator_agent.py --start_line 784 --end_line 826`

5.  **✅ Verification**
    *Run the test script to verify grading accuracy.*
    `python scripts/test_agent_5_judgelm.py`
