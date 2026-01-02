# Agent 6: KAG Agent Whitebox Analysis [RESOLVED]

## 1. Internal Architecture

Agent 6 serves as the **Knowledge Graph Aggregator**, responsible for aligning personal learning artifacts with the course structure and detecting system-wide patterns.

### 1.1 Process Flow (3 Phases)

1.  **Zettelkasten Generation** (Real-time):
    -   Trigger: `EVALUATION_COMPLETED` (Score >= 0.8).
    -   LLM Extraction: Extracts `Key Insight`, `Personal Example`, `Common Mistake` from the session.
    -   Tagging: Semantic tags generated from content + mapped concepts.
    -   Linking: Queries Personal KG for related notes and creates `[:LINKS_TO]` relationships.

2.  **Dual-KG Synchronization** (Async):
    -   Aligns **Personal KG** with **Course KG**.
    -   Updates `[:HAS_MASTERY]` based on Evaluator scores.
    -   Logs `[:HAS_MISCONCEPTION]` for error tracking.

3.  **System Learning** (Batch):
    -   Aggregates mastery data from all learners (Minimum N=5).
    -   Calculates `Avg Mastery` and `Struggle Rate` per concept.
    -   **Pattern Recognition**:
        -   **Difficult Concept**: Avg Mastery < 0.4.
        -   **Priority Struggle**: Struggle Rate > 0.6.
    -   Generates Recommendations (e.g., "Add more examples").

---

## 2. Algorithms & Configuration

### 2.1 Thresholds (Standardized in `constants.py`)
-   `KAG_MASTERY_THRESHOLD = 0.8`: Distinguishes Atomic Notes from Misconception Notes.
-   `KAG_DIFFICULT_THRESHOLD = 0.4`: Concepts below this are flagged as difficult.
-   `KAG_PRIORITY_STRUGGLE_THRESHOLD = 0.6`: Triggers urgent content intervention.

### 2.2 Zettelkasten Logic
-   **Atomic Note**: Smallest unit of knowledge.
-   **Connections**: Dynamic linking via Cypher queries (`MATCH (n:NoteNode) WHERE n.tag IN ...`).

---

## 3. Resilience

### 3.1 Error Handling
-   **JSON Parsing**: Fragile LLM output parsing has fallback manual extraction (partially mitigated).
-   **KG Sync**: Checks for Neo4j availability before execution to prevent crashes.

---

## 4. Verification Strategy

Verified via `scripts/test_agent_6.py`:

1.  **Artifact Generation**: Verified creation of `AtomicNote` and linking.
2.  **System Analysis**:
    -   Verified Statistics Calculation (Avg Mastery, Struggle Rate).
    -   Verified Recommendation Logic (Triggered when Struggle Rate > 0.6 AND Mastery < 0.4).

**Status**: Verified. Mock tests passed.
