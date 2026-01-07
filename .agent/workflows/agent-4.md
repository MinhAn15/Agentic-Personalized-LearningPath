---
description: Deep Dive into Agent 4 (Tutor / Chain of Thought).
---
# Agent 4: Tutor (The "Metacognitive Teacher")

This workflow provides a comprehensive technical view of Agent 4, focusing on its "Think before Speak" architecture.

// turbo-all

1.  **🔬 Scientific Basis (Whitebox Analysis)**
    *Review the Chain of Thought (CoT) and Scaffolding theory.*
    `view_file docs/AGENT_4_WHITEBOX.md`

2.  **🧠 Code Structure: CoT Generation**
    *Generating multiple internal reasoning traces (Wei 2022).*
    `view_file backend/agents/tutor_agent.py --start_line 229 --end_line 275`

3.  **⚖️ Code Structure: Self-Consistency**
    *Selecting the best pedagogical strategy (Consensus).*
    `view_file backend/agents/tutor_agent.py --start_line 308 --end_line 321`

4.  **💬 Code Structure: Harvard Enforcer**
    *Ensuring response aligns with pedagogical principles.*
    `view_file backend/agents/tutor_agent.py --start_line 552 --end_line 559`

5.  **✅ Verification**
    *Run the test script to see the "Hidden" thought process.*
    `python scripts/test_agent_4_cot.py`
