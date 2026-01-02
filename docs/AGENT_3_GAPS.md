# Agent 3 Gaps: Path Planner

> **Priority**: Medium-High

## 1. Concurrency: Feedback Race Condition
- **Status**: 🔴 **OPEN**
- **Description**: `_on_evaluation_feedback` performs "Read-Modify-Write" on Redis data (`mab_stats` and `linucb_arm`) without locking.
- **Impact**: If multiple learners complete evaluations simultaneously (or same learner rapid-fires), updates to the LinUCB model (Matrix A) could be overwritten (Lost Update), corrupting the learning model.
- **Proposed Fix**: Implement **Redis Distributed Lock**, similar to Agent 2.

## 2. Config: Hardcoded Thresholds
- **Status**: 🟡 **OPEN**
- **Description**: Constants like `0.8` (Gate), `0.7` (Prereq), `0.1` (Review Chance) are hardcoded in the logic.
- **Impact**: Difficult to tune or experiment with different pedagogical strategies without code changes.
- **Proposed Fix**: Extract to `backend.core.constants` or `backend.config.Settings`.

## 3. Testability: Non-Deterministic Logic
- **Status**: 🟡 **OPEN**
- **Description**: The Probabilistic Gate uses `random.random()` directly.
- **Impact**: Tests are flaky or require complex mocking of the random module.
- **Proposed Fix**: Inject a `seed` or wrap random logic in a helper that can be mocked/controlled.

## 4. Performance: Synchronous Loops
- **Status**: 🟢 **LOW**
- **Description**: `_get_chain_candidates` iterates and checks prereqs in Python loops.
- **Impact**: Likely negligible for now (Limit 100 concepts), but could scale poorly if graph grows.
- **Proposed Fix**: Keep as is for now, monitor.
