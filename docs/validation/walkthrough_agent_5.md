# Walkthrough: Scientific Refinement (Agent 5 - Evaluator)

## 1. Goal
Upgrade the Evaluator Agent from basic Bloom's Taxonomy scoring to **JudgeLM (LLM-as-a-Judge)**, aiming for higher correlation with expert grading and scientific validity (Zhu 2023).

## 2. Changes
### Backend (`evaluator_agent.py`)
*   **Removed**: `_score_response` logic based on simple word overlap and Bloom Prompt.
*   **Added**: `_score_with_judgelm` logic implementing:
    *   **Reference-as-Prior**: The "Golden Answer" is explicitly set as the standard (10/10).
    *   **CoT Grading**: The LLM generates a "Justification Trace" before outputting the score.
    *   **Weighted Scoring**: Correctness (0.6), Completeness (0.2), Clarity (0.2).

### Logic Refinement (Scientific Basis)
*   **Position Bias Mitigation**: By presenting the Reference *first* and declaring it the standard, we turn the task into a similarity comparison, reducing the LLM's tendency to just "pick the first one".
*   **Reliability**: The forced "Justification Trace" ensures the score is grounded in analysis, not hallucinated.

## 3. Verification
*   **Script**: `scripts/verify_judgelm.py`
*   **Tests**:
    1.  **Perfect Match**: Confirmed score of 1.0 when Learner ~= Reference.
    2.  **Partial Match**: Confirmed score of ~0.6 for incomplete answers.
    3.  **Robustness**: Confirmed graceful handling of malformed JSON outputs.

## 4. Documentation
*   Updated `SCIENTIFIC_BASIS.md` to reference JudgeLM.
*   Updated `NOTEBOOKLM_PROMPTS.md` with the new architecture context.
