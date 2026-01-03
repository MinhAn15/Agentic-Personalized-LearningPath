---
description: Standard procedure for applying scientific feedback (NotebookLM/Audit) to the codebase and ensuring full documentation synchronization.
---

# Scientific Refinement & Synchronization Workflow

This workflow ensures that any change in the scientific basis is reflected across the entire system (Code, Docs, Prompts, Logs).

## 1. Input Analysis
*   [ ] Read **NotebookLM Feedback** or **Audit Report**.
*   [ ] Identify the specific mathematical or logical gap (e.g., "Missing Leiden Algorithm", "Wrong BKT Formula").

## 2. Planning
*   [ ] Create/Update `implementation_plan.md`.
    *   Define the new algorithm/logic.
    *   List specific files to modify.

## 3. Code Implementation (**The Refinement**)
*   [ ] Modify `backend/agents/*.py` to implement the new logic.
*   [ ] Add/Update `constants.py` for any new parameters (e.g., `P_LEARN`, `DECAY_RATE`).
*   [ ] **Requirement**: Add comments citing the Scientific Paper and Year in the code (e.g., `# Source: Corbett & Anderson (1994)`).

## 4. Documentation Synchronization (**CRITICAL**)
*   [ ] **Update Theory**: Modify `docs/SCIENTIFIC_BASIS.md` to reflect the *actual* implemented formula.
*   [ ] **Update Context**: Modify `docs/NOTEBOOKLM_PROMPTS.md`. Update the "Context" block for the specific agent to describe the *new* implementation. This ensures future validations use the correct context.
*   [ ] **Update Journal**: Add entry to `docs/validation/journal_agent_X.md` logging the fix and its date.

## 5. Verification & Tracking
*   [ ] Create/Update `walkthrough.md` with snippets of the changes.
*   [ ] Update `task.md`: Mark the specific Refinement task as `[x]`.

## 6. Final Check
*   [ ] Run `@[/spec-check]` (Optional) to ensure no regressions.
