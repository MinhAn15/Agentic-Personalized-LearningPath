---
description: Iterative loop for refining Agent scientific basis using NotebookLM feedback
---

This workflow defines a "Dialectic Refinement Loop" (Iterative Scientific Validation) to ensure Agents achieve high alignment with their academic foundations.

## Phase 1: Thesis Assessment (Diagnosis)
1.  **Execute Base Prompt**
    -   Use `docs/NOTEBOOKLM_PROMPTS.md` for the specific Agent.
    -   Run in NotebookLM with the source papers uploaded.
2.  **Report to AI Assistant**
    -   In this chat, run the command:
        `@[/scientific-refinement-loop] Feedback for Agent [X]`
    -   **Paste the entire text** from NotebookLM immediately after the command.
    -   *This triggers the AI to switch to "Scientific Analyst" mode.*

## Phase 2: Synthesis Strategy (AI Analysis)
3.  **AI Analysis**
    -   I (the AI) will analyze the critique.
    -   I will categorize issues into:
        -   `[CRITICAL]`: Math/Logic mismatch.
        -   `[MISSING]`: Feature absent in code.
        -   `[VARIANCE]`: Intentional simplification.
4.  **Proposal Generation**
    -   I will propose specific code changes or generate a **Follow-up Prompt** for you to ask NotebookLM if the path is unclear (e.g., "Ask NotebookLM if 'Leiden' is a valid substitute for 'Louvain'").

## Phase 3: Implementation (Action)
5.  **Apply Changes**
    -   Once we agree on the fix, I will edit the code (`backend/agents/`).
    -   I will update `docs/SCIENTIFIC_BASIS.md` and `docs/[AGENT]_WHITEBOX.md`.

## Phase 4: Confirmation (Closure)
6.  **Final Verification**
    -   I will give you a *new* Context Summary reflecting the changes.
    -   You paste this into NotebookLM to confirm "Strong Alignment".
