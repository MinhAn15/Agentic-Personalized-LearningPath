# Scientific Validation Journal: Agent 3 (Path Planner)

## 1. Audit Summary
*   **Agent**: Path Planner
*   **Source Code**: `backend/agents/path_planner_agent.py`
*   **Scientific Basis**: `docs/SCIENTIFIC_BASIS.md`
*   **Status**: 🟡 PARTIALLY VERIFIED

## 2. Claim Verification

| Claim | Source Paper | Status | Evidence in Code |
| :--- | :--- | :--- | :--- |
| **Zone of Proximal Development** | Vygotsky (1978) | ✅ **VERIFIED** | `prereqs_met` check (Line 701) ensures we only recommend concepts where prerequisites > Threshold. |
| **Contextual Bandits (LinUCB)** | Li et al. (2010) | ✅ **VERIFIED** | `_load_linucb_arms` (Line 137) and `RLEngine(LINUCB)`. `Ridge Regression` state is persisted to Redis. |
| **Spaced Repetition** | Ebbinghaus (1885) | ⚠️ **WEAK IMPLEMENTATION** | The current logic (Line 728) prioritizes *lower* mastery (`1.0 - mastery`). Ebbinghaus requires tracking `last_review_date` and using an exponential decay function ($R = e^{-t/S}$). The code has a `TODO` for this. |

## 3. Analysis & Gaps
### Gap 1: "Remediation" vs "Spaced Repetition"
The current code conflates two different things:
1.  **Remediation**: Re-teaching something you *don't* know (Low Mastery).
2.  **Spaced Repetition**: Reviewing something you *do* know (High Mastery) before you forget it.

**Current logic**: `review_score = 1.0 - mastery`.
*   If Mastery = 0.2 (Low), Score = 0.8 (High Priority) -> This is **Remediation**.
*   If Mastery = 0.9 (High), Score = 0.1 (Low Priority) -> This **ignores Spaced Repetition**.

**Scientific Requirement**: Even if Mastery = 0.9, if `last_review` was 30 days ago, Priority should be HIGH.

## 4. Next Steps (User Action)
Run **NotebookLM** to confirm the mathematical difference and request the correct formula.

**Context for NotebookLM**:
> "I am implementing Spaced Repetition for my 'Review Mode'.
> Current Logic: `Priority = 1.0 - CurrentMastery` (Focus on what I'm bad at).
> Goal: Prevent decay of what I'm *good* at (Ebbinghaus)."

**Question for NotebookLM**:
> "My logic prioritizes Remediation (fixing weak concepts) but ignores Spaced Repetition (maintaining strong concepts). What is the standard mathematical formula (e.g., from SuperMemo/Anki) to combine 'Current Mastery' and 'Time Since Last Review' into a single 'Review Priority' score?"
