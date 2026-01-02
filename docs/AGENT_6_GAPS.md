# Agent 6: KAG Agent Gaps

## 1. Hardcoded Configuration
**Severity:** Medium
**Location:** `backend/agents/kag_agent.py`

The following analysis thresholds are hardcoded and should be moved to `backend/core/constants.py`:
-   `MIN_LEARNERS_FOR_ANALYSIS = 5`
-   `MASTERY_THRESHOLD = 0.8` (Bloom's 2-Sigma reference)
-   `DIFFICULT_THRESHOLD = 0.4`
-   `EASY_THRESHOLD = 0.8`
-   `PRIORITY_STRUGGLE_THRESHOLD = 0.6`
-   `STRUGGLE_MASTERY_THRESHOLD = 0.5`

## 2. Code Duplication
**Severity:** Low
**Location:** `ID_PATTERN`

-   The regex `r'^[a-zA-Z0-9_-]+$'` is redefined appearing in every agent. It should be centralized (e.g., in `constants.py` or `BaseAgent`).

## 3. Testing Gaps
**Severity:** High
**Location:** `scripts/`

-   No proper test script (`scripts/test_agent_6.py`) exists.
-   We need to verify:
    -   Zettelkasten Note Generation (Mock LLM JSON).
    -   Dual-KG Synchronization logic (Neo4j Mock).
    -   System Analysis Aggregation (Statistics calculation).

## 4. Error Handling
**Severity:** Medium
**Location:** `_generate_artifact`

-   The JSON parsing logic uses a fallback manual extraction (lines 294-306) which is fragile. Mocks should test malformed JSON scenarios.
