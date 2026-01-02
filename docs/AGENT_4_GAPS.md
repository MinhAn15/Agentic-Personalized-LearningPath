# Agent 4: Tutor Agent Gaps

## 1. Hardcoded Configuration
**Severity:** Medium
**Location:** `backend/agents/tutor_agent.py` (init, logic)

The following values are hardcoded and should be moved to `backend/core/constants.py`:
-   `W_DOC = 0.4`
-   `W_KG = 0.35`
-   `W_PERSONAL = 0.25`
-   `CONFIDENCE_THRESHOLD = 0.5`
-   `CONFLICT_THRESHOLD = 0.6`
-   `CONFLICT_PENALTY = 0.1`

## 2. Unused Imports & Dead Code
**Severity:** Low
**Location:** `backend/agents/tutor_agent.py`

-   `backend.core.grounding_manager.GroundingManager` is imported but the logic is implemented inline within `_three_layer_grounding`. Ideally, this should be refactored to use the manager or remove the import. For now, we will cleanup the import.
-   `import random` acts as a duplicate if not organized (handled in imports cleanup).

## 3. Testing Gaps
**Severity:** High
**Location:** `scripts/`

-   No dedicated test script (`scripts/test_agent_4.py`) exists.
-   We need to verify:
    -   Socratic State transitions (Machine logic).
    -   3-Layer Grounding aggregation (Mocked).
    -   Harvard Enforcer application.
    -   Conflict Detection logic.

## 4. Error Handling
**Severity:** Low
**Location:** `_rag_retrieve`

-   The LlamaIndex integration is wrapped in try/except, but if `self.query_engine` fails to load, it silently falls back to 0.0 without a clear metric in the response metadata indicating *why* RAG failed (e.g., "Retriever Unavailable" vs "No Results").
