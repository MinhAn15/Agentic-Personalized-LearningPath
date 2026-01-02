---
description: Test Agent 3 (Path Planner) functionality
---

Steps to verify Agent 3 logic, specifically the new Distributed Locking and Adaptive Chaining mechanisms.

1. **Mock Mode Test**
   Runs the agent in isolation using mocks for Neo4j, Redis, and EventBus. Verifies:
   - Path generation logic (LinUCB, Gating).
   - Distributed Lock acquisition.
   - Resilience (missing imports, mocks).

   ```bash
   python scripts/test_agent_3.py --mode mock
   ```

2. **Real Mode Test (Optional)**
   Runs the agent against live local Neo4j and Redis instances.
   *ensure Redis and Neo4j are running before executing*

   ```bash
   # python scripts/test_agent_3.py --mode real
   ```

3. **Check Logs**
   Review the output for `[SUCCESS] PATH GENERATED` and `✅ Redis Lock correctly requested`.
