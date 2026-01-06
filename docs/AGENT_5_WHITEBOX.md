# Agent 5: Evaluator Agent Whitebox Analysis [RESOLVED]

## 1. Internal Architecture

Agent 5 serves as the **Pedagogical Judge**, assessing learner performance using a standardized Multi-Factor Rubric and determining the optimal next step in the learning path.

### 1.1 Process Flow (8 Phases)

1.  **Context Gathering**:
    -   Loads Concept Metadata (Difficulty, Misconceptions) from Neo4j (Cached, TTL=1h).
    -   Loads Learner Profile (Current Mastery) from Personal KG.

3.  **JudgeLM Scoring (SOTA)**:
    -   **Technique**: Reference-as-Prior (Zhu 2023).
    -   **Prompt**: "Assistant 1" (Golden) vs "Assistant 2" (Student).
    -   **Format**: `10.0 {score}` notation + JSON CoT.
    -   **Rubric**: Correctness (0.6), Completeness (0.2), Clarity (0.2).

3.  **Error Classification** (if Score < 0.8):
    -   Taxonomy: `CONCEPTUAL` (Fundamental), `PROCEDURAL`, `INCOMPLETE`, `CARELESS`.
    -   Misconception Detection: Matches error against known misconceptions in KG.

4.  **Feedback Generation**:
    -   Personalized response addressing the specific misconception.

5.  **5-Path Decision Logic**:
    -   Determines `PathDecision` based on Score, Error Type, and Difficulty.
    -   **MASTERED** (>= 0.9): Skip ahead.
    -   **PROCEED** (>= 0.8): Next concept.
    -   **ALTERNATE** (>= 0.6): Different modality.
    -   **REMEDIATE** (< 0.6 + Conceptual): Go back.
    -   **RETRY** (< 0.6 + Other): Try again.

6.  **Mastery Update**:
    -   Apps Weighted Moving Average (WMA).
    -   `New = (Current * 0.4) + (Score * 0.6)` (Standardized weight).

7.  **Alerting**:
    -   Triggers Instructor Alert if `score < 0.4` (Critical Failure).

8.  **Output**:
    -   Emits `EVALUATION_COMPLETED` event to Path Planner.

---

## 2. Algorithms & Data Structures

### 2.1 5-Path Decision Engine
Implemented in `_make_path_decision`:

| Decision | Base Condition | Adjustment |
| :--- | :--- | :--- |
| **MASTERED** | Score >= 0.9 | -0.05 if Diff>=4, -0.03 if High Mastery |
| **PROCEED** | Score >= 0.8 | -0.05 if Diff>=4 |
| **ALTERNATE** | Score >= 0.6 | -0.05 if Diff>=4 |
| **REMEDIATE** | < 0.6 AND Error=CONCEPTUAL | N/A |
| **RETRY** | < 0.6 AND Error!=CONCEPTUAL | N/A |

### 2.2 Configuration
Standardized in `constants.py`:
-   `EVAL_MASTERY_WEIGHT = 0.6`
-   `THRESHOLD_ALERT = 0.4`

---

## 3. Resilience

### 3.1 Error Handling
-   **Empty Response**: Logs warning, returns score 0.0.
-   **LLM Failure**: Falls back to keyword overlap scoring.
-   **Event Emit Failure**: Swallows error to prevent crashing the evaluation return.

---

## 4. Verification Strategy

Verified via `scripts/test_agent_5_judgelm.py`:

1.  **Prompt Structure**: Validated exact match with JudgeLM System Prompt (Figure 5).
2.  **Scoring Notation**: Verified parsing of `10.0 X` and JSON fallback.
3.  **Rubric Weights**: Verified roughly linear updates.

**Status**: Verified (Test Passed).
