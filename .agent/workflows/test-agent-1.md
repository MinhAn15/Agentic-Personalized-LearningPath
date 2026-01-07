---
   `python scripts/test_agent_1.py --mode real --file "path/to/your/document.txt"`

## Troubleshooting

- If you see `ModuleNotFoundError` for other agents (e.g., Profiler), the runner script has a Hotfix to mock them. Ensure you are using the latest version of `scripts/test_agent_1.py`.
- If `EventBus` errors occur, ensure `MockEventBus` has a synchronous `subscribe` method.
