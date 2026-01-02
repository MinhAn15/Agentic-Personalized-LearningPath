# Agent 6: KAG Agent Flow (Knowledge Graph Aggregator)

## 1. High-Level Architecture

The KAG Agent is responsible for **Knowledge Alignment**, **Artifact Generation**, and **System-Wide Learning**.

```mermaid
graph TD
    subgraph Trigger
        EVAL[EVALUATION_COMPLETED Event] --> GENERATE
        TIMER[Scheduled Task] --> ANALYZE
    end

    subgraph Phase1_Artifact[Phase 1: Zettelkasten Generation]
        GENERATE --> EXTRACT[Extract Atomic Note]
        EXTRACT --> RELATED[Find Related Notes]
        RELATED --> TAG[Generate Semantic Tags]
        TAG --> CREATE[Create NoteNode in Personal KG]
        CREATE --> LINK[Link to Related Notes]
        LINK --> EMIT_ART[Emit ARTIFACT_CREATED]
    end

    subgraph Phase2_Sync[Phase 2: Dual-KG Synchronization]
        EMIT_ART --> UPD_MASTERY[Update Mastery Node]
        UPD_MASTERY --> SYNC_ERR[Sync Misconceptions]
    end

    subgraph Phase3_Analysis[Phase 3: System Learning]
        ANALYZE --> AGGREGATE[Aggregate All Learner Graphs]
        AGGREGATE --> STATS[Calculate Statistics]
        STATS --> PATTERNS[Identify Bottleneck Concepts]
        PATTERNS --> REC[Generate Recommendations]
        REC --> PREDICT[Predict Interventions]
        PREDICT --> EMIT_SYS[Emit KAG_ANALYSIS_COMPLETED]
    end
```

## 2. Core Workflows

### 2.1 Zettelkasten Generation (Real-time)
Triggered by `EVALUATION_COMPLETED` (Score >= 0.8).
1.  **Extraction**: LLM extracts `key_insight`, `personal_example`, `common_mistake` from session.
2.  **Grounding**: Finds related existing notes in Personal KG for context.
3.  **Storage**: Creates `NoteNode` and links via `[:LINKS_TO]`.

### 2.2 Dual-KG Sync (Personal <-> Course)
Ensures Personal KG stays aligned with Course KG updates.
-   **Mastery Sync**: Updates `[:HAS_MASTERY]` based on Evaluator scores.
-   **Misconception Sync**: Logs `[:HAS_MISCONCEPTION]` for persistent error tracking.

### 2.3 System Learning (Batch/Async)
Aggregates data across ALL learners (N > 5).
-   **Bottleneck Detection**:
    -   `Avg Mastery < 0.4` -> Difficult Concept.
    -   `Struggle Rate > 0.6` -> Priority Intervention.
-   **Recommendation Engine**: Suggests content improvements (e.g., "Add more examples for SQL_JOIN").
