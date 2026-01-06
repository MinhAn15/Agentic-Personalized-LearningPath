# Agent 5: Evaluator Agent Flow

## 1. High-Level Control Flow

The Evaluator Agent implements a **Multi-Factor Rubric** to assess student understanding and determine the next pedagogical step.

```mermaid
graph TD
    subgraph Input
        RESP[Learner Response]
        EXP[Expected Answer]
        KG[Course KG]
    end

    subgraph Phase1_Context[Phase 1: Context Gathering]
        RESP --> CACHE{Concept in Cache?}
        CACHE -->|Yes| LOAD[Load Cache]
        CACHE -->|No| QUERY[Query Neo4j]
        QUERY --> LOAD
    end

    subgraph Phase2_Scoring[Phase 2: JudgeLM Scoring]
        LOAD --> SCORE[JudgeLM (Reference-as-Prior)]
        EXP --> SCORE
        SCORE --> TRACE[CoT Reasoning Trace]
        TRACE --> CALC[Weighted Score (0-10)]
        CALC --> THRESHOLD{Score >= 0.8?}
    end

    subgraph Phase3_Analysis[Phase 3: Error Analysis]
        THRESHOLD -->|No| CLASSIFY[Classify Error]
        CLASSIFY --> DETECT[Detect Misconception]
        DETECT --> FEEDBACK[Generate Feedback]
        THRESHOLD -->|Yes| PRAISE[Generate Praise]
    end

    subgraph Phase4_Decision[Phase 4: Path Decision]
        FEEDBACK --> DECIDE{Decision Engine}
        PRAISE --> DECIDE
        DECIDE -->|>=0.9| M[MASTERED]
        DECIDE -->|>=0.8| P[PROCEED]
        DECIDE -->|>=0.6| A[ALTERNATE]
        DECIDE -->|<0.6+Conceptual| R[REMEDIATE]
        DECIDE -->|<0.6+Other| RT[RETRY]
    end

    subgraph Phase5_Update[Phase 5: Update & Output]
        DECIDE --> UPDATE[Update Mastery WMA]
        UPDATE --> EVENT[Emit EVALUATION_COMPLETED]
        UPDATE --> ALERT{Score < 0.4?}
        ALERT -->|Yes| NOTIFY[Notify Instructor]
        ALERT -->|No| OUT[Return Result]
    end
```

## 2. Key Components

### 2.1 Multi-Factor Rubric (Scoring)
-   **Semantic Similarity**: LLM-based comparison of learner response vs expected answer.
-   **Scale**: 0.0 (Completely Wrong) to 1.0 (Correct).
-   **Thresholds**:
    -   `MASTERED`: >= 0.9 (Adjusted by difficulty/current mastery)
    -   `PROCEED`: >= 0.8
    -   `ALTERNATE`: >= 0.6

### 2.2 Error Classification (Taxonomy)
If score < 0.8, the error is classified into:
1.  **CONCEPTUAL**: Fundamental misunderstanding (Triggers REMEDIATE).
2.  **PROCEDURAL**: Wrong steps or application.
3.  **INCOMPLETE**: Missing key elements.
4.  **CARELESS**: Typos or calculation errors.

### 2.3 5-Path Decision Engine
Determines the next step in the learning path:
1.  **MASTERED**: Skip ahead / Mark complete.
2.  **PROCEED**: Move to next concept.
3.  **ALTERNATE**: Try a different explanation or modality.
4.  **REMEDIATE**: Go back to prerequisites (triggered by CONCEPTUAL errors).
5.  **RETRY**: Try again (triggered by other errors).

### 2.4 Mastery Tracking (WMA)
Updates the learner's mastery using Weighted Moving Average:
`New = (Current * 0.4) + (Score * 0.6)`
(Weight needs standardization to 0.3/0.7 per Thesis or config).
