# Agent 2: Learner Profiler Agent

## Overview

**File:** `backend/agents/profiler_agent.py`  
**Purpose:** Constructs and maintains a multidimensional **Learner Profile** (17-dim vector + Personal Knowledge Graph). It acts as the "State Manager" for the personalized learning experience, evolving in real-time based on learner interactions.

---

## 🏗️ Detailed Architecture & Pipeline

```mermaid
graph TD
    subgraph "1. Intent & Cold Start"
        IN1[/"🗣️ Input: Learner Message (Goal)"/]
        VEC_STORE[(Vector Store)]
        IN1 --> INTENT[Intent Extraction: Goal/Topic/Style]
        INTENT --> DIAG[Diagnostic Assessment: Hybrid Retrieval]
        VEC_STORE -.-> DIAG
        DIAG --> OUT1[/"📋 Output: Initial Profile JSON"/]
    end

    subgraph "2. Profile Vectorization"
        OUT1 --> VECTOR[Profile Vectorizer]
        VECTOR --> VEC_OUT[/"Output: 17-Dim Feature Vector"/]
    end

    subgraph "3. State Persistence (Dual-Layer)"
        VEC_OUT --> POSTGRES[(PostgreSQL: Structured Data)]
        VEC_OUT --> REDIS[(Redis: Hot State / Locks)]
        VEC_OUT --> NEO4J_INIT[Personal KG Initialization]
        NEO4J_INIT --> NEO_OUT[/"Output: :Learner & :MasteryNode"/]
    end

    subgraph "4. Real-Time Event Handling"
        EVENT1(EVALUATION_COMPLETED) --> H_EVAL[Update Mastery & Bloom Level]
        EVENT2(PACE_CHECK_TRIGGERED) --> H_PACE[Update Velocity & Difficulty]
        EVENT3(ARTIFACT_CREATED) --> H_ART[Track Note Taking]
        
        H_EVAL --> LOCK{Per-Learner Lock}
        H_PACE --> LOCK
        H_ART --> LOCK
        
        LOCK --> STATE_UPD[Atomic State Update]
        STATE_UPD --> PUB(Emit: PROFILE_ADVANCED)
    end
    
    subgraph "Data Stores"
        PG[(Postgres: LProfiles)]
        RD[(Redis: Cache)]
        N4J[(Neo4j: Personal KG)]
    end

    POSTGRES -.-> PG
    REDIS -.-> RD
    NEO4J_INIT -.-> N4J
    STATE_UPD -.-> RD
    STATE_UPD -.-> N4J
```

---

## 🧠 Core Technical Mechanisms (Deep Dive)

### 1. Intent Extraction & Cold-Start

| Step | Input | Process | Output |
|------|-------|---------|--------|
| **Intent Extraction** | User Message ("I want to learn SQL for my job") | LLM Extracts: Topic (SQL), Purpose (Job), Constraint (Time) | Structured Goal JSON |
| **Diagnostic** | Topic + Skill Level | **Hybrid Retrieval Strategy**:<br>1. **Vector Search**: Find semantic matches via `_retrieve_vector_candidates` (LlamaIndex).<br>2. **Graph Search**: Find centrality anchors via Cypher (Neo4j).<br>3. **Merge**: Combine Top-5 candidates.<br>4. **Generate**: Dynamic questions via LLM. | Initial `concept_mastery_map` |

### 2. Profile Vectorization (17-Dimensional)

Converts the rich profile object into a mathematical vector for similarity matching (Peer Matching) and difficulty adjustment.

**Key Dimensions:**
- **Dim 0:** `knowledge_state` (Average Mastery)
- **Dim 1-4:** `learning_style` (One-hot: Visual/Audit/Read/Kinesthetic)
- **Dim 5:** `skill_level` (Normalized: 0.2/0.5/0.8)
- **Dim 7:** `bloom_avg` (Weighted average of Bloom's Taxonomy level)
- **Dim 8:** `learning_velocity` (Concepts completed / hour)
- **Dim 9:** `topic_length` (Normalized scope)

### 3. Personal KG Initialization (Dual-KG Layer 3)

Instead of just storing a JSON profile, Agent 2 initializes a private subgraph for the learner in Neo4j.

| Entity Type | Cypher Pattern | Purpose |
|-------------|----------------|---------|
| `:Learner` | `(l:Learner {learner_id: ...})` | Root node for the learner. |
| `:MasteryNode` | `(l)-[:HAS_MASTERY]->(m)-[:MAPS_TO_CONCEPT]->(c)` | Bridge node linking Learner to Course Concepts. Stores `score`, `bloom_level`. |
| `:SessionEpisode` | `(l)-[:HAS_SESSION]->(s)` | Tracks active learning sessions. |

### 4. Real-Time Event Handling (Async State Machine)

Agent 2 acts as a reactive state machine, handling events from other agents.

#### Event: `EVALUATION_COMPLETED`
- **Source:** Agent 5 (Evaluator)
- **Trigger:** Learner finishes a quiz/test.
- **Process:**
  1. Acquire **Async Lock** (`learner_id`) to prevent race conditions.
  2. Update `concept_mastery_map` with new score.
  3. **Bloom Logic:** Calculate Bloom Level using multi-signal formula:
     $$Bloom = 0.6 \times Score + 0.25 \times Difficulty + 0.15 \times QuestionType$$
  4. **Interest Decay:** Apply $\lambda = 0.95$ to fade old tags.
  5. **Optimistic Locking:** Increment `version` to ensure consistency.

#### Event: `PACE_CHECK_TRIGGERED`
- **Source:** System Timer / Agent 3
- **Trigger:** Periodic check of learning speed.
- **Process:**
  1. Calculate `learning_velocity = concepts_done / hours_spent`.
  2. **Auto-Adjust:**
     - If `velocity > 1.2` (Too fast) → Set `difficulty_next = HARD`.
     - If `velocity < 0.8` (Too slow) → Set `difficulty_next = EASY`.

---

## 🔧 Developer Reference

- `execute()`: Main entry point for initial profiling.
- `_parse_goal_with_intent()`: LLM-based goal structuring.
- `_vectorize_profile()`: Converts object to 17-dim list.
- `_on_evaluation_completed()`: Critical event handler for mastery updates.
- `VersionConflictError`: Raised if Optimistic Locking fails.
