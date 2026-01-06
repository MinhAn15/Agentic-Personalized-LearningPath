# Scientific Validation Journal - Agent 5 (Evaluator Agent)

## 1. Audit Summary
**Date**: 2026-01-04
**Auditor**: NotebookLM (Google Gemini) + Antigravity
**Focus Paper**: 
1. Zhu et al. (2023) - JudgeLM: Fine-tuning Large Language Models as Scalable Judges
2. Liu et al. (2023) - G-Eval: NLG Evaluation using GPT-4

## 2. Findings (Audit Phase)
| ID | Topic | Finding | Status |
|----|-------|---------|--------|
| A5-01 | Position Bias | LLM prefers the first option. **Fix**: Use "Reference as Prior" (Ref = Asst 1 = 10/10). | **Fixed** |
| A5-02 | Reliability | Single-pass scoring is noisy. **Fix**: "Justification Trace" (CoT) before scoring improves consistency (~92%). | **Fixed** |
| A5-03 | Knowledge Bias | Without reference, LLM hallucinates. **Fix**: "Reference-Based" evaluation is mandatory. | **Fixed** |

## 3. Refinement Strategy (Plan)
We will upgrade `_score_response` to implement **JudgeLM** style scoring:

1.  **Reference-as-Prior Prompt**:
    *   "Assistant 1" = Golden Reference (Score 10).
    *   "Assistant 2" = Learner Response.
    *   Task: "Assistant 1 is the standard. Score Assistant 2 based on similarity/quality relative to Assistant 1."

2.  **Chain-of-Thought Rubric**:
    *   Force the Agent to output: `analysis` -> `adjustments` -> `final_score`.
    *   Dimensions: Correctness, Clarity, Completeness.

3.  **Code Changes**:
    *   `evaluator_agent.py`: Replace Bloom scoring with `_score_with_judgelm`.

## 4. Verification
*   **Script**: `scripts/verify_judgelm.py`
*   **Metric**: Check if subtle errors (e.g., "Partial correct") receive granular scores (e.g., 0.5-0.7) backed by reasoning.

## 5. Refinement (2026-01-06): JudgeLM Implementation
**Trigger**: Scientific Audit revealed "Position Bias" and need for strict "Reference-as-Prior".
**Action**:
1.  **Strict Prompt**: Implemented Figure 5 Prompt from JudgeLM paper.
    *   Reference = "Assistant 1" (Score 10).
    *   Learner = "Assistant 2".
2.  **Logic**: `_score_response` now outputs `10.0 {score}` notation.
3.  **Rubric**: Injected weights for Correctness (0.6), Completeness (0.2), Clarity (0.2).
**Verification**:
*   `test_agent_5_judgelm.py`: Passed. Confirmed correct parsing and JSON fallback.
