# Scientific Validation Journal: Agent 2 (Profiler)
**Status**: IN_PROGRESS
**Target Scientific Basis**: Deep Knowledge Tracing (DKT) / LLM-based Tracing
**Primary Sources**:
- Piech, C., et al. (2015). "Deep Knowledge Tracing"
- Liu, Y., et al. (2024). "LLM-based Knowledge Tracing"

## 1. Initial State (Classical Basis)
*   **Current Model**: Simplified Bayesian Knowledge Tracing (BKT).
*   **Mechanism**: Scalar probability updates using Bayes' theorem ($P(L_t|Obs)$).
*   **Limitation**: Assumes concepts are independent (naive assumption) and cannot capture complex "forgetting curves" or cross-concept dependencies as well as RNNs/Transformers (DKT).

## 2. NotebookLM Validation (Session 1)
*   **Date**: 2026-01-03
*   **Prompt**: "Critique this LLM-based approach against standard DKT..."
*   **Input Papers**:
    *   *Deep Knowledge Tracing* (Piech 2015)
    *   *LLM-based Knowledge Tracing* (Liu 2024)

### Expected Feedback Areas:
1.  **Long-Term Dependencies**: Can an LLM Context prompt replicate the LSTM memory cell of DKT?
2.  **Cold Start**: How to handle empty history better than BKT (which uses a fixed prior)?
3.  **Efficiency**: Is calling an LLM for every mastery update too slow compared to BKT?

### 3. NotebookLM Critique (2026-01-03)
**Analysis**:
*   **[CRITICAL] Missing Recurrence**: Simple Prompting lacks the "Forget Gates" and "Multiplicative Interactions" of LSTM that capture subtle long-term dependencies ($W_{hh}$).
*   **[CRITICAL] Calibration Risk**: LLMs optimize for plausibility, not probability (NLL), leading to "Hallucinated Competence" (e.g., 99% mastery from one lucky guess).
*   **[MISSING] Cold Start Handling**: DKT uses a bias parameter ($b_z$) for community average pass rate. The current plan lacks this "Prior Belief".

**Refinement Strategy (Hybrid DKT-LLM)**:
*   **Action**: Instead of pure LLM prediction, use **Hybrid Anchoring**.
    *   **Prior**: Start with Community Average Pass Rate (derived from Difficulty).
    *   **Adjustment**: Ask LLM to *adjust* this prior based on the qualitative history (e.g., "Student struggled with prerequisites, so lower the 60% prior").
    *   **Benefit**: Anchors the LLM (preventing hallucination) while allowing it to capture "Long-term" semantic patterns (e.g., "confused conceptual understanding") that DKT might miss (because DKT treats IDs as symbols).

## 4. Refinement Log (2026-01-03)
- [2026-01-03] **Implementation Implemented**:
  - **Resolution**: Implemented "Hybrid DKT-LLM Anchoring".
  - **Code**: `evaluator_agent.py` -> `_update_learner_mastery` now uses `community_prior` + `_calculate_hybrid_mastery`.
  - **Logic**: 
    1. Base Probability = $1.0 - (Difficulty * 0.15)$.
    2. Context Summary = "Current Mastery + Latest Outcome + Misconception".
    3. LLM adjusts the Base Probability based on Context.
  - **Validation Status**: Ready for experimental verification.
