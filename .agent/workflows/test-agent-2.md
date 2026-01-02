---
description: Run verification tests for Agent 2 (Profiler).
---
# Test Agent 2 Workflow

This workflow describes how to run the automated test runner for Agent 2. Use this to verify the Profiler's logic (vectorization, locking, event handling) after making changes.

// turbo

1. **Mock Mode (Recommended for Logic Check)**
   Run the test runner in mock mode. This mocks Neo4j/Redis and allows you to verify the internal logic (vectorization, distributed lock fallback, event handling) without needing a database connection.
   
   `python scripts/test_agent_2.py --mode mock`

2. **Real Mode (Integration Test)**
   Run the test against actual databases. Requires `redis-server` and `neo4j` to be running and `.env` configured.
   
   `python scripts/test_agent_2.py --mode real`

## Troubleshooting

- **Lock Acquisition Failed**: If you see warnings about lock acquisition in Real Mode, ensure your Redis instance supports locking or that no other process is holding the lock for the test learner ID.
- **Import Errors**: If `Neo4jPropertyGraphStore` import fails, the test runner should gracefully skip Graph RAG features, but check if `llama-index-graph-stores-neo4j` is installed.
