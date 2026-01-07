---
description: Deep Dive into Agent 6 (KAG / MemGPT).
---
# Agent 6: KAG (The "Operating System")

This workflow provides a comprehensive technical view of Agent 6, focusing on its OS-like memory management and autonomous loop.

// turbo-all

1.  **🔬 Scientific Basis (Whitebox Analysis)**
    *Review the MemGPT and Dual-Process Memory theory.*
    `view_file docs/AGENT_6_WHITEBOX.md`

2.  **💓 Code Structure: Heartbeat Loop**
    *The `execute()` method implementing the OS kernel loop.*
    `view_file backend/agents/kag_agent.py --start_line 209 --end_line 299`

3.  **💾 Code Structure: Memory Management**
    *Auto-Archiving when pressure is high (System 2 Ops).*
    `view_file backend/agents/kag_agent.py --start_line 328 --end_line 357`

4.  **📝 Code Structure: Zettelkasten Generation**
    *Extracting Atomic Notes and linking them to KGs.*
    `view_file backend/agents/kag_agent.py --start_line 427 --end_line 513`

5.  **✅ Verification**
    *Run the test script to see the OS in action.*
    `python scripts/test_agent_6_memgpt.py`
