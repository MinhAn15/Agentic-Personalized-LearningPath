# Agent 4: Tutor Agent Whitebox Analysis [RESOLVED]

## 1. Internal Architecture

Agent 4 serves as the **AI Tutor**, delivering personalized Socratic guidance. It moves beyond simple Q&A by maintaining a pedagogical state machine and enforcing educational principles.

### 1.1 Process Flow (7 Phases)

1.  **Context Gathering**:
    -   Queries Neo4j (Course KG) for facts.
    -   Queries Neo4j (Personal KG) for user history/mastery.
    -   (Optional) Retrieves RAG documents.

2.  **Intent Classification**:
    -   Uses LLM to categorize learner intent:
        -   `HELP_SEEKING`: Frustrated, blocked -> Needs **Scaffolding**.
        -   `SENSE_MAKING`: Curious, exploring -> Needs **Probing**.

3.  **Reverse Socratic State Machine**:
    -   Determines the pedagogical *mode* of interaction.
    -   Logic is deterministic based on `hint_level` and `mastery`, stochastic for advanced strategies (`TEACH_BACK`).

4.  **3-Layer Grounding (Anti-Hallucination)**:
    -   parallel retrieval from 3 sources with weighted confidence.
    -   **Conflict Detection**: If RAG contradicts Course KG (Similarity < 0.6), KG wins, and confidence is reduced (Penalty -0.1).

5.  **Response Generation**:
    -   LLM generates text guided by "Socratic Prompt" templates specific to the current state.

6.  **Harvard 7 Enforcement**:
    -   Post-processing check to ensure response adheres to principles (e.g., Active Learning, Feedback).

7.  **State Persistence**:
    -   Session state saved to Redis (`ttl=24h`).

---

## 2. Algorithms & Data Structures

### 2.1 Socratic State Logic
Implemented in `_determine_socratic_state`:

| State | Trigger Criteria |
| :--- | :--- |
| **REFUTATION** | `has_misconception=True` |
| **SCAFFOLDING** | `intent=HELP_SEEKING` OR `hint_level=1` |
| **PROBING** | `intent=SENSE_MAKING` OR default |
| **TEACH_BACK** | `mastery > 0.7` AND `rounds > 2` (40% chance) |
| **CONCLUSION** | `hint_level >= 4` OR `rounds >= 5` |

### 2.2 3-Layer Grounding Weights
Standardized in `constants.py`:

-   `TUTOR_W_DOC = 0.4` (Broad coverage)
-   `TUTOR_W_KG = 0.35` (Structured facts)
-   `TUTOR_W_PERSONAL = 0.25` (User context)
-   **Threshold**: 0.5 (below this = "I don't know")

---

## 3. Resilience & Configuration

### 3.1 Configuration Management
-   All thresholds (`0.6` conflict, `0.4` weights) are imported from `backend/core/constants.py`.
-   This allows global tuning of the "Tutor Personality" without code changes.

### 3.2 Error Handling
-   **RAG Fallback**: If `vector_store` is missing (common in test/dev), RAG layer returns 0.0 confidence but doesn't crash the agent.
-   **Mocking**: Unit tests use `sys.modules` patching to handle `llama_index` dependencies gracefully.

---

## 4. Verification Strategy

Verified via `scripts/test_agent_4.py`:

1.  **State Machine Tests**: Confirmed correct transition from Probing -> Scaffolding based on intent.
2.  **Protege Effect**: Verified `TEACH_BACK` triggers for high-mastery learners.
3.  **Math Verification**: Validated Weighted Sum calculation for Grounding Confidence.
4.  **Conflict Logic**: Verified confidence penalty when `_detect_conflict` returns True.

**Status**: Verified. All mock tests passed.
