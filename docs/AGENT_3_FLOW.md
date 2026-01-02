# Agent 3 Flow: Path Planner

## 1. Execution Flow (`execute`)

The `PathPlannerAgent` generates a personalized learning path in 8 steps:

### Step 1: Context Loading
- **Input**: `learner_id`, `goal`
- **Action**: Fetch `LearnerProfile` from Redis/Postgres via `state_manager`.
- **Validation**: Ensure profile exists.

### Step 2: Goal-Centric Filtering (Personal Subgraph)
- **Objective**: Reduce search space from entire KG to relevant subgraph.
- **Query (Neo4j)**:
    - Start with `MasteryNode` (concepts user knows).
    - Expand to neighbors (`NEXT`, `REQUIRES`, `SIMILAR_TO`).
    - fallback: If profile is empty (Cold Start), search by Topic + Centrality.
- **Limit**: Max 100 concepts.

### Step 3: RL Engine Initialization
- **Action**: Register valid concepts as "Arms" in the Multi-Armed Bandit (MAB) engine.
- **State**: Arms track `pulls` and `total_reward`.

### Step 4: Relationship Mapping
- **Action**: Query Neo4j for ALL relationships between selected concepts.
- **Output**: `relationship_map` dict (`REQUIRES`, `NEXT`, etc.).

### Step 5: Chaining Mode Selection
- **Logic**: Determine strategy based on `last_result` (from Agent 5).
    - `MASTERED` -> `ACCELERATE`
    - `PROCEED` -> `FORWARD`
    - `REMEDIATE` -> `BACKWARD`
    - `STUCK` -> `LATERAL`
    - `NEW_SESSION` -> `REVIEW` (10% chance) or `FORWARD`.

### Step 6: Adaptive Path Generation (Loop)
Iterate until `time_available` is filled (80% capacity):

1.  **Probabilistic Gating**:
    - Check score of last added concept.
    - `GateProb = min(1.0, score / 0.8)`.
    - If `random > GateProb`: Force `BACKWARD` mode (Remediation).

2.  **Candidate Selection** (`_get_chain_candidates`):
    - Filter neighbors based on `chain_mode` rules (e.g., `FORWARD` uses `NEXT`).
    - **Filter**: Must trigger `prereqs_met` (Mastery >= 0.7).
    - **Cold Start**: If no path, pick "Root Concepts" (0 prereqs).

3.  **LinUCB Selection**:
    - Load `linucb:{cid}` state from Redis.
    - **Context**: 10-dim `profile_vector`.
    - **Selection**: `rl_engine.select_concept()` returns best concept.

4.  **Update Path**:
    - Add concept to list.
    - Update `hours_used`, `current_mastery` (simulated).
    - Save context to Redis (`linucb_context:{cid}`) for later feedback.

### Step 7: Resource Recommendation
- **Logic**: Append placeholder resources (`VIDEO`, `EXERCISE`) based on Learning Style (`VISUAL` vs `READING`).

### Step 8: Success Probability
- **Formula**: `0.4*Mastery + 0.4*TimeFit - 0.2*Diff`.

## 2. Feedback Loop (`_on_evaluation_feedback`)

Triggered by `EVALUATION_COMPLETED` event:

1.  **Reward Calculation**: `R = 0.6*score + 0.4*completion`.
2.  **MAB Update**: Update `mab_stats:{cid}` (Simple Ops).
3.  **LinUCB Update**:
    - Retrieve `context_vector` (from Event or Redis).
    - Load `linucb_arm` (Ridge Regression key) from Redis.
    - Update Matrix A and Vector b.
    - Save back to Redis.
