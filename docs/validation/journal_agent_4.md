# Scientific Validation Journal - Agent 4 (Tutor Agent)

## 1. Audit Summary
**Date**: 2026-01-04
**Auditor**: NotebookLM (Google Gemini) + Antigravity
**Focus Paper**: 
1. Wei et al. (2022) - Chain-of-Thought Prompting
2. Wang et al. (2022) - Self-Consistency

## 2. Findings
| ID | Topic | Finding | Status |
|----|-------|---------|--------|
| A4-01 | Rigid FSM | Socratic State Machine is too rigid and doesn't "think" before speaking. | **Fixed** |
| A4-02 | Leakage | Standard CoT leaks the answer. | **Fixed** |
| A4-03 | Hallucination | Single-pass generation can hallucinate incorrect hints. | **Fixed** |

## 3. Implementation Details (Refinement)
We replaced the `SocraticState` Enum and strict FSM with a Dynamic CoT loop:

1.  **Hidden CoT**: `_generate_cot_traces(n=3)`
    *   Generates 3 internal thoughts about the student's error.
    *   *Self-Consistency Check*: `_check_consensus()` ensures the agent is confident in its diagnosis.

2.  **Leakage Guard**: `_extract_scaffold()`
    *   Parses the internal thought.
    *   Removes "Therefore", "The answer is", etc.
    *   Returns only the reasoning steps + a probing question.

3.  **Code Changes**:
    *   `tutor_agent.py`: Removed 200+ lines of Socratic Logic. Added CoT methods.
    *   `constants.py`: Added `TUTOR_COT_TRACES`, `TUTOR_LEAKAGE_KEYWORDS`.

## 4. Verification
*   **Script**: `scripts/verify_tutor_cot.py`
*   **Result**: 
    *   ✅ Leakage Guard active (Answer Hidden).
    *   ✅ Scaffolding format verified.
    *   ✅ Legacy Socratic methods removed (No NameError).

## 5. Refinement (2026-01-04): Hybrid CoT + Method Ontology
**Trigger**: Scientific Audit revealed "Method Ontology" (Chandrasekaran 1999) is needed for structured scaffolding.
**Action**:
1.  **Restored `DialogueState`**: Re-integrated the State Machine to track phases (Intro -> Scaffolding -> Handoff).
2.  **Slicing Logic**: Implemented `_slice_cot_trace` to serve the CoT plan one step at a time.
3.  **SOTA Prompts**: Injected GSM8K/CSQA Exemplars into `_generate_cot_traces`.
**Verification**:
*   `test_agent_4_cot.py`: Confirmed phase transitions and sequential hint serving.
