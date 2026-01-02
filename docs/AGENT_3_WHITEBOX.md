# Agent 3: Path Planner Whitebox Analysis [RESOLVED]

## 1. Internal Architecture

Agent 3 is the system's "navigator," responsible for generating the optimal sequence of learning concepts. Unlike static rule-based planners, it employs a hybrid approach combining **Graph Traversal (Adaptive Chaining)** and **Reinforcement Learning (LinUCB)**.

### 1.1 Process Flow (6 Phases)

1.  **Input & Context Loading**:
    -   Receives `learner_id`, `goal`, and `last_result`.
    -   Loads robust Leaerner Profile (vector + preferred style).
    -   Queries Personal Knowledge Graph (Neo4j) to identify candidates.

2.  **Smart Filtering**:
    -   **Personal Subgraph Expansion**: Instead of scanning the entire KG, it starts from known concepts (`:MasteryNode` in Neo4j) and expands to immediate neighbors (`NEXT`, `REQUIRES`). This ensures O(1) scalability relative to graph size.

3.  **Probabilistic Mastery Gate (Scientific Upgrade)**:
    -   Replacing binary pass/fail logic.
    -   Formula: `gate_prob = min(1.0, current_score / GATE_FULL_PASS_SCORE)`
    -   Logic:
        -   If `random() > gate_prob`: **Force Remediation** (BACKWARD mode).
        -   Else: Allow normal progression (FORWARD/ACCELERATE).
    -   *Benefit:* Prevents "lucky guesses" from causing long-term knowledge gaps.

4.  **Adaptive Chaining (Heuristic Layer)**:
    -   Determines the *direction* of movement based on `ChainingMode`:
        -   **FORWARD (Standard)**: Follows `NEXT` edges.
        -   **BACKWARD (Remediation)**: Follows `REQUIRES` edges (prerequisites).
        -   **ACCELERATE (High Mastery)**: Skips intermediate nodes if prerequisites met.
        -   **REVIEW (Spaced Repetition)**: Random 10% chance (configurable via `REVIEW_CHANCE`) to revisit old concepts.

5.  **LinUCB Selection (Stochastic Layer)**:
    -   Selects the *best single step* from the valid candidates.
    -   Uses Contextual Bandit algorithm (Li et al., 2010).

6.  **Output Generation**:
    -   Produces `LearningPath` JSON.
    -   Calculates success probability and pacing.

---

## 2. Algorithms & Data Structures

### 2.1 LinUCB Implementation
-   **Context**: 10-dimensional vector from Learner Profile.
-   **Arms**: Each Concept ID in the candidate list is an arm.
-   **State**: Per-arm matrices stored in Redis (`linucb:{concept_id}`).
    -   `A` (10x10): Covariance matrix (inverse approximated).
    -   `b` (10x1): Reward history vector.
-   **Selection Goal**: Maximize Upper Confidence Bound (UCB).

### 2.2 Adaptive Chaining Logic
The agent maintains a state machine for `ChainingMode`:

| Trigger | Mode | Action |
| :--- | :--- | :--- |
| `last_result="PROCEED"` | **FORWARD** | Move to next concept in sequence. |
| `last_result="REMEDIATE"` | **BACKWARD** | Identify unmastered prerequisites. |
| `last_result="MASTERED"` | **ACCELERATE** | Check 2-hop neighbors (`NEXT` -> `NEXT`). |
| `random() < REVIEW_CHANCE` | **REVIEW** | Select unvisited or old concepts. |

---

## 3. Resilience & Concurrency [FIXED]

### 3.1 Distributed Locking (Redis)
**Gap Identified**: Concurrent feedback events (e.g., rapid quiz completion) caused race conditions in LinUCB matrix updates (`read-modify-write`).

**Solution**:
-   Implemented `redis.lock(name=f"lock:concept:{concept_id}", timeout=5)` inside `_on_evaluation_feedback`.
-   Ensures atomic updates to the global `A` and `b` matrices for each concept.
-   **Impact**: Prevents matrix corruption and divergent learning policies.

### 3.2 Configuration Management
**Gap Identified**: Hardcoded thresholds (`0.8`, `0.7`) scattered in code.
**Solution**:
-   Centralized all thresholds in `backend/core/constants.py`.
-   Imported into Agent 3 (`MASTERY_PROCEED_THRESHOLD`, `GATE_FULL_PASS_SCORE`).
-   Enhances maintainability and experimental tuning.

### 3.3 Lazy Initialization & Error Handling
-   **JSON Handling**: Added missing imports to prevent `NameError`.
-   **Mock Resilience**: Test runner explicitly mocks `redis.pipeline` as synchronous to match real-world usage patterns, preventing `coroutine` attribute errors during testing.

---

## 4. Verification Strategy

The agent is verified using `scripts/test_agent_3.py` which supports:
1.  **Mock Mode**:
    -   Simulates Neo4j graph and Redis state.
    -   Patches `random` to test Probabilistic Gate deterministically.
    -   Verifies Lock acquisition.
2.  **Real Mode**:
    -   Connects to live services for end-to-end flow validation.

**Status**: Verified. All tests passed locally.
