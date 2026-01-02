# Agent 2: Learner Profiler Agent - Flow Documentation

> **Status**: Verified via Code Audit
> **Source Code**: `backend/agents/profiler_agent.py`

## 1. High-Level Overview
Agent 2 ("The Psychologist") constructs and maintains a **Learner Profile** (10-dimensional vector + Personal Knowledge Graph). It adapts in real-time based on learner interactions.

## 2. Input & Output

| Type | Data Structure | Description |
|------|----------------|-------------|
| **Input** | `learner_message` | Start/Update message (e.g., "I want to learn SQL") |
| **Output** | `LearnerProfile` | Struct with goal, dimensions, mastery map |
| **Side Effect** | **Redis** | Hot cache of profile + vector |
| **Side Effect** | **Neo4j** | Personal KG (`:Learner`, `:MasteryNode`) |
| **Side Effect** | **PostgreSQL** | Persistent profile record |

## 3. Detailed Execution Flow

### Step 1: Intent Extraction & Cold Start
*   **Method**: `_parse_goal_with_intent`
*   **Logic**:
    1.  Uses LLM to extract: `topic`, `purpose`, `current_level`, `learning_style`.
    2.  Generates structured Goal JSON.

### Step 2: Diagnostic Assessment (Hybrid RAG)
*   **Method**: `_run_diagnostic_assessment`
*   **Logic**:
    1.  **Priority 1**: Graph RAG (`PropertyGraphIndex`) to find topographic concepts.
    2.  **Priority 2**: Vector Search fallback.
    3.  **Priority 3**: LLM Generation fallback.
    4.  **Action**: Generates 5 diagnostic questions to estimate initial mastery (0.0 - 1.0).

### Step 3: Profile Vectorization
*   **Method**: `_vectorize_profile`
*   **Logic**: Creates 10-dim feature vector for LinUCB bandit (Agent 3).
    *   Dim 0: Knowledge State
    *   Dim 1-4: Learning Style (VARK One-Hot)
    *   Dim 5: Skill Level
    *   Dim 6-9: Context (Time, Bloom, Velocity, Scope)

### Step 4: Dual Persistence
*   **Logic**:
    1.  **PostgreSQL**: Saves structured profile (JSONB).
    2.  **Neo4j**: Merges `:Learner` node. Creates `:SessionEpisode` and `:MasteryNode`s.
    3.  **Redis**: Caches profile (TTL 1 hour).

### Step 5: Event Emission
*   **Event**: `LEARNER_PROFILED`
*   **Target**: Agent 3 (Planner)

## 4. Real-Time Event Handling
Agent 2 subscribes to events to update the profile dynamically:

| Event | Handler | Logic |
|-------|---------|-------|
| `EVALUATION_COMPLETED` | `_on_evaluation_completed` | Updates Mastery & Bloom Level. Applies Interest Decay. |
| `PACE_CHECK_TRIGGERED` | `_on_pace_check` | Adjusts Learning Velocity. |

## 5. Potential Issues
*   **Concurrency**: Uses `asyncio.Lock` which is not distributed-safe.
*   **Config**: Hardcoded paths for Vector Index.
*   **Dependency**: Strict dependency on `llama-index-graph-stores-neo4j`.
