# Scientific Validation Journal: Agent 2 (Profiler)

## 1. Audit Summary
*   **Agent**: Learner Profiler
*   **Source Code**: `backend/agents/profiler_agent.py`
*   **Scientific Basis**: `docs/SCIENTIFIC_BASIS.md`
*   **Status**: 🔴 CRITICAL MISMATCH

## 2. Claim Verification

| Claim | Source Paper | Status | Evidence in Code |
| :--- | :--- | :--- | :--- |
| **Hexagonal Arch** | Cockburn (2005) | ✅ **VERIFIED** | `LearnerProfile` (Line 149) is a pure domain entity. Redis (Line 277) and Postgres (Line 172) are separated adapters. |
| **Distributed Locking** | Kleppmann (2017) | ✅ **VERIFIED** | `redis_lock.acquire()` (Line 766) protects profile updates. |
| **Bayesian Knowledge Tracing** | Corbett & Anderson (1994) | ❌ **FAILED** | `SCIENTIFIC_BASIS.md` claims "Simplified BKT". However, the code (Line 799) uses a **Weighted Moving Average** (WMA) with fixed weights (0.3/0.7), which is mathematically distinct from Bayesian inference. |

## 3. Analysis & Gaps
### Gap 1: WMA != Bayesian Knowledge Tracing
The paper defines BKT as a Hidden Markov Model with 4 parameters:
*   $P(L_0)$: Initial learning prob.
*   $P(T)$: Transition prob (learning during step).
*   $P(Guess)$: Slip probability.
*   $P(Slip)$: Guess probability.

**Current Implementation**:
```python
new_mastery = (0.3 * old_mastery) + (0.7 * score)
```
This is a `Weighted Moving Average`, **not** BKT. It fails to account for "Guessing" (getting it right without knowing) or "Slipping" (knowing but making a mistake).

## 4. Next Steps (User Action)
We must decide: **Implement Real BKT or Rename the Algorithm?**

**User Action**: Run **NotebookLM** with this prompt to see if WMA is an acceptable "Proxy" or if it violates the core premise.

**Context that I (AI) extracted**:
> "I claim to use Simplified BKT.
> My Code Implementation: `new_mastery = (0.3 * old_mastery) + (0.7 * score)`.
> I do not calculate P(L|OBS) using Bayes theorem. I do not store P(Guess) or P(Slip)."

**Question for NotebookLM**:
> "Is a Weighted Moving Average (WMA) a mathematically valid approximation for Bayesian Knowledge Tracing? Or does it fundamentally fail to model the 'Hidden State' nature of knowledge?"
