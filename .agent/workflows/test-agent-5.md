---
description: Test Agent 5 (Evaluator Agent) functionality
---

Steps to verify Agent 5 logic, specifically the Multi-Factor Rubric, Error Classification, and 5-Path Decision Engine.

1. **Mock Mode Test**
   Runs the agent in isolation using mocks for Neo4j, Redis, LLM, and LlamaIndex. Verifies:
   - Scoring Logic (0.0 - 1.0 scale).
   - Error Classification (Conceptual, Procedural, Careless).
   - 5-Path Decision Boundaries (Mastered, Proceed, Alternate, Remediate, Retry).
   - Mastery Weighted Moving Average (WMA) calculation.
   - Alerting Logic (Score < 0.4).

   ```bash
   python scripts/test_agent_5.py --mode mock
   ```

2. **Real Mode Test (Optional)**
   Runs the agent against live local Neo4j and Redis instances.
   *ensure Redis and Neo4j are running before executing*

   ```bash
   # python scripts/test_agent_5.py --mode real
   ```

3. **Check Logs**
   Review the output for:
   - `✅ Evaluation complete`
   - `✅ MOCK TEST PASSED`
