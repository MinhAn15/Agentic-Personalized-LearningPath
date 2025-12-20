# Agent 3: Path Planner Agent

## Overview

**File:** `backend/agents/path_planner_agent.py`  
**Purpose:** Generates optimal learning sequences using Multi-Armed Bandit (RL) with adaptive chaining.

---

## 🏗️ RL Engine: Multi-Armed Bandit (MAB)

The agent uses a **LinUCB-based Multi-Armed Bandit** strategy to balance pedagogical consistency (exploitation) with discovery of better sequences (exploration).

### Reward Function
The agent learns from the Evaluator's feedback:
$R = 0.6 \times \text{Score} + 0.4 \times \text{Completion} - \text{Penalty}$

- **Score:** 0.0 - 1.0 (from Agent 5).
- **Completion:** Binary success of the node.
- **Penalty:** Deduction for immediate dropouts or frustration signals.

---

## 🧠 Adaptive Chaining Modes

Agent 3 shifts its sequencing logic based on the learner's current state:

| Mode | Trigger | Logic |
| :--- | :--- | :--- |
| **FORWARD** | Success (0.8 - 0.9) | Follows `NEXT` or `IS_PREREQUISITE_OF` links. |
| **BACKWARD** | Failure (< 0.6) | **Remediation**: Jumps back to `REQUIRES` prerequisites. |
| **LATERAL** | Struggle (Stuck) | **Stabilization**: Switches to `SIMILAR_TO` concepts (alternative explanations). |
| **ACCELERATE** | Mastery (> 0.95) | **Flow State**: Skips basics, jumps to sub-concepts or higher complexity. |
| **REVIEW** | New Session | **Spaced Repetition**: Injects review of old nodes based on decay. |

---

## 📋 Mastery Gate (Strict)
The planner enforces a **Blocking Gate**:
- If current concept mastery < 0.8:
  - ⛔ **BLOCKS** FORWARD progression.
  - ⚠️ Forces BACKWARD/LATERAL modes.

---

## 🔧 Output Structure

| Field | Description |
| :--- | :--- |
| `learning_path` | Ordered list of concept objects with metadata. |
| `success_probability` | Prediction based on mastery vs difficulty. |
| `pacing` | COMFORTABLE, MODERATE, or TIGHT (derived from time budget). |
| `chain_mode` | The logic used for this generation (e.g., REMEDIATE). |
