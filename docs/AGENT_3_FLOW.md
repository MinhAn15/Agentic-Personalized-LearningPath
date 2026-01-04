# Agent 3: Path Planner Agent - Flow Documentation

> **Status**: Verified via Code Audit
> **Source Code**: `backend/agents/path_planner_agent.py`

## 1. High-Level Overview
Agent 3 ("The Architect") generates optimal curriculum paths. It is currently in a **Hybrid State**, transitioning from LinUCB Bandits to Tree of Thoughts (ToT).

## 2. Input & Output

| Type | Data Structure | Description |
|------|----------------|-------------|
| **Input** | `goal` | Target Topic/Mastery requirements |
| **Input** | `LearnerProfile` | Mastery State + Learning Style |
| **Output** | `LearningPath` | Sequence of `ConceptID`s + Resource Recommendations |

## 3. Detailed Execution Flow

### Step 1: Context Loading
*   **Method**: `execute`
*   **Logic**:
    1.  Loads `LearnerProfile`.
    2.  Queries `Neo4j` for relevant `CourseConcepts` (Candidate Pool).
    3.  Loads MAB Stats (Redis) + LinUCB Arms (Contextual Bandit).

### Step 2: Planning Strategy Selection
*   **Logic**:
    *   **Cold Start**: Returns top single step.
    *   **Active**: Triggers `_explore_learning_paths`.

### Step 3: Beam Search (The ToT Skeleton)
*   **Method**: `_beam_search` (Logic present but disconnected)
*   **Parameters**: Beam Width ($b=3$), Depth ($d=3$).
*   **Logic**:
    1.  **Frontier**: Starts with [Initial Concepts].
    2.  **Expansion**: For each path, find neighbors via `_get_reachable_concepts`.
    3.  **Evaluation**: Score each new path via `_evaluate_path_viability`.
    4.  **Pruning**: Keep top 3 paths.
*   **Current Issue**: `_get_reachable_concepts` returns empty list `[]`, rendering this flow non-functional.

### Step 4: LinUCB Fallback (The Active Logic)
*   **Method**: `_generate_adaptive_path`
*   **Logic**:
    *   While time_available > 0:
        1.  Get Candidates (Forward/Backward/Lateral).
        2.  **Filter**: Probabilistic Gate (Block progress if Mastery < threshold).
        3.  **Select**: Use `rl_engine.select_concept` (LinUCB).

## 4. Potential Issues
*   **Broken ToT**: The Beam Search method exists but relies on an unimplemented helper (`_get_reachable_concepts`).
*   **Prompt Weakness**: The simplistic `_evaluate_path_viability` prompt does not perform "Mental Simulation".
*   **Hybrid Confusion**: The code mixes a functional Bandit loop (`_generate_adaptive_path`) with a non-functional Beam Search (`_explore_learning_paths`).
