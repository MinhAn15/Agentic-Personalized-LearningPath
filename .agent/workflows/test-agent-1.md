---
description: Run verification tests for Agent 1 (Knowledge Extraction).
---
# Test Agent 1 Workflow

This workflow describes how to run the automated test runner for Agent 1. This is useful for regressions testing after code modifications.

// turbo

1. **Mock Mode (Recommended for Logic Check)**
   Run the test runner in mock mode. This mocks all external dependencies (Neo4j, Redis, other Agents) and tests the internal flow of Agent 1.
   
   `python scripts/test_agent_1.py --mode mock`

2. **Real Mode (Integration Test)**
   Run the test against actual databases. Requires `.env` to be configured with valid credentials.
   
   `python scripts/test_agent_1.py --mode real --file "path/to/your/document.txt"`

## Troubleshooting

- If you see `ModuleNotFoundError` for other agents (e.g., Profiler), the runner script has a Hotfix to mock them. Ensure you are using the latest version of `scripts/test_agent_1.py`.
- If `EventBus` errors occur, ensure `MockEventBus` has a synchronous `subscribe` method.
