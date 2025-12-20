# Agent 5: Evaluator Agent

## Overview

**File:** `backend/agents/evaluator_agent.py`  
**Purpose:** Assesses learner understanding, classifies errors, tracks mastery via weighted moving average, and makes 5-path pedagogical decisions.

---

## 🎯 Scoring & Classification Engine

Agent 5 uses a **Multi-Signal Semantic Scorer**:
$\text{Score} = 0.4 \times \text{SemanticSimilarity} + 0.5 \times \text{LLM\_Score} + 0.1 \times \text{GroundingBoost}$

### Error Types
| Type | Condition |
| :--- | :--- |
| **CORRECT** | Score ≥ 0.95 |
| **CARELESS** | High similarity but minor typos or case issues. |
| **INCOMPLETE** | Score 0.6-0.8; factually correct but lacks detail. |
| **PROCEDURAL** | Right concept but wrong application/method. |
| **CONCEPTUAL** | Fundamental misunderstanding (Trigger: Misconception Alert). |

---

## 🧠 Path Decision Engine (Thesis Table 3.10)

After every evaluation, the agent makes a critical decision for the Planner:

- **MASTERED**: Score ≥ 0.9; Advance to next concept.
- **PROCEED**: Score ≥ 0.8; Advance but flag for light review.
- **RETRY**: Score 0.6 - 0.79; Repeat the current concept with different content.
- **ALTERNATE**: Conceptual error present; Use `LATERAL` chaining (different explanation).
- **REMEDIATE**: Score < 0.4; Jump back to prerequisites (`BACKWARD` chaining).

---

## 📋 Mastery Tracking

Uses a **Weighted Moving Average** with Bloom context:
- Old Mastery: $M_{old}$
- New Score: $S$
- Update: $M_{new} = 0.7 \times M_{old} + 0.3 \times S$
- **Bloom Adjustment**: If evaluating higher-order skills (Apply/Analyze), the weight of $S$ increases to 0.5.

---

## 🔧 Event Triggers
- **Input**: Listens for `TUTOR_ASSESSMENT_READY`.
- **Output**: Emits `EVALUATION_COMPLETED` (Payload contains score, decision, and error_type).
- **Alert**: Triggers `INSTRUCTOR_ALERT` if score stays below 0.4 for multiple attempts.
