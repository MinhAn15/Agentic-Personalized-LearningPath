---
description: Test Agent 6 (KAG Agent) functionality
---

Steps to verify Agent 6 logic, specifically Zettelkasten Artifact Generation and System Learning Analysis.

1. **Mock Mode Test**
   Runs the agent in isolation using mocks for Neo4j, LLM, and LlamaIndex. Verifies:
   - Atomic Note Extraction (LLM JSON parsing).
   - Knowledge Graph Interaction (Note creation, linking).
   - System Statistics Calculation (Avg Mastery, Struggle Rate).
   - Recommendation Generation (Threshold logic).

   ```bash
   python scripts/test_agent_6.py --mode mock
   ```

2. **Real Mode Test (Optional)**
   Runs the agent against live local Neo4j instance.
   *ensure Neo4j is running before executing*

   ```bash
   # python scripts/test_agent_6.py --mode real
   ```

3. **Check Logs**
   Review the output for:
   - `✅ Artifact created`
   - `✅ KAG analysis complete`
   - `✅ MOCK TEST PASSED`
