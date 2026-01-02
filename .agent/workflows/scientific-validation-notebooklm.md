---
description: Run scientific validation of Agents using NotebookLM
---

Steps to validate the scientific integrity of the Agent codebase using Google NotebookLM.

1.  **Select Agent & Paper**
    -   Open `docs/SCIENTIFIC_BASIS.md` to identify the Source Paper.
    -   Download the PDF of the paper (e.g., from arXiv or Google Scholar).

2.  **Prepare NotebookLM**
    -   Go to [NotebookLM](https://notebooklm.google.com/).
    -   Create a new Notebook.
    -   Upload the PDF(s).

3.  **Execute Prompt**
    -   Open `docs/NOTEBOOKLM_PROMPTS.md`.
    -   Scroll to the relevant Agent section.
    -   Copy the **Context** (Code implementation summary).
    -   Copy the **Prompt**.
    -   Paste both into the NotebookLM chat box.

4.  **Record Findings**
    -   If NotebookLM identifies a gap (e.g., "Your EMA approximation fails to account for 'Slip' probability"), create a new Issue/Gap in `task.md`.
    -   Example: `[ ] Refine Agent 2 Mastery Calculation based on Corbett (1994) feedback`.

5.  **Iterate**
    -   Update the code based on findings.
    -   Re-run the prompt with the updated Context.
