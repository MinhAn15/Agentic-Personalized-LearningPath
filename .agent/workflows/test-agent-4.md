---
description: Test Agent 4 (Tutor Agent) functionality
---

Steps to verify Agent 4 logic, specifically the Socratic State Machine, 3-Layer Grounding, and Harvard Enforcer.

1. **Mock Mode Test**
   Runs the agent in isolation using mocks for Neo4j, Redis, LLM, and LlamaIndex. Verifies:
   - Socratic State transitions (Probing -> Scaffolding, Protege Effect).
   - 3-Layer Grounding Score Calculation.
   - Conflict Detection & Confidence Penalty.

   ```bash
   python scripts/test_agent_4.py --mode mock
   ```

2. **Real Mode Test (Optional)**
   Runs the agent against live local Neo4j and Redis instances.
   *ensure Redis and Neo4j are running before executing*

   ```bash
   # python scripts/test_agent_4.py --mode real
   ```

3. **Check Logs**
   Review the output for:
   - `✅ Confidence Score Correct`
   - `✅ Conflict Penalty Applied`
   - `✅ MOCK TEST PASSED`
