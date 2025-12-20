# Agent 4: Tutor Agent

## Overview

**File:** `backend/agents/tutor_agent.py`  
**Purpose:** Teaches using Harvard 7 Principles and a Reverse Socratic Method supported by a 3-layer grounding system.

---

## 🧠 Reverse Socratic State Machine

The tutor moves through cognitive states to facilitate active learning rather than passive reading:

1.  **PROBING** (State 0): Asks open-ended questions to assess current knowledge.
2.  **SCAFFOLDING** (State 1): Provides basic conceptual hints (Level 1).
3.  **GUIDING** (State 2): Provides structural hints/analogies (Level 2).
4.  **EXPLAINING** (State 3): Direct instruction (only if the learner is truly stuck).
5.  **CONCLUSION** (State 4): Synthesizes the answer and provides a final insight.

---

## 🛡️ 3-Layer Grounding (The "Anti-Hallucination" Stack)

| Layer | Source | Role |
| :--- | :--- | :--- |
| **Layer 1: RAG** | Vector DB | Retrieves raw document chunks for factual accuracy. |
| **Layer 2: Course KG** | Neo4j | Provides structured definitions and "Common Errors". |
| **Layer 3: Personal KG** | Neo4j | Learner's history (Prev. misconceptions, past notes). |

---

## 📋 Harvard 7 Principles Enforcement

Every response is audited by the `Harvard7Enforcer` to ensure it:
- Encourages **Active Learning**.
- Provides **Immediate Feedback**.
- Adapts to **Prior Knowledge**.
- Manages **Cognitive Load**.

---

## 🔧 Interaction Cycle

1.  **Receive Question/Path**: Handled via `PATH_PLANNED` event or direct query.
2.  **State Selection**: Checks `DialogueState` to see how many hints have been given.
3.  **Grounding**: Queries RAG + KG to build context.
4.  **Generation**: LLM constructs response using the current Socratic State prompt.
5.  **Handoff**: Once the learner demonstrates understanding, it triggers `TUTOR_ASSESSMENT_READY` for Agent 5.
