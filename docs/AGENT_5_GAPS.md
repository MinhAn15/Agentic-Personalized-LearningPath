# Agent 5: Evaluator Agent Gaps

## 1. Hardcoded Configuration
**Severity:** Medium
**Location:** `backend/agents/evaluator_agent.py`

The following values are hardcoded and should be moved to `backend/core/constants.py`:
-   `MASTERY_WEIGHT = 0.6` (Weighted Moving Average factor)
-   `DIFFICULTY_ADJUSTMENT = 0.05`
-   `MASTERY_BOOST = 0.03`
-   Decision Thresholds: `0.9` (Mastered), `0.8` (Proceed), `0.6` (Alternate)
-   Instructor Alert Threshold: `score < 0.4`

## 2. Testing Gaps
**Severity:** High
**Location:** `scripts/`

-   No dedicated test script (`scripts/test_agent_5.py`) exists.
-   We need to verify:
    -   Scoring logic (Mock LLM response parsing).
    -   Error Classification (Taxonomy correctness).
    -   5-Path Decision Logic (Threshold boundary tests).
    -   Mastery WMA Calculation.

## 3. Instructor Notification
**Severity:** Low
**Location:** `execute`

-   The Notification Service `notify_failure` call is present but needs to be verified in Mock mode to ensure it handles failures gracefully without crashing the agent.

## 4. LLM JSON Parsing
**Severity:** Low
**Location:** `_score_response`

-   The regex fallback for JSON parsing is good, but unit tests should cover edge cases (e.g., malformed JSON, empty response) to ensure robustness.
