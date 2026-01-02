# Deep Scientific Audit Plan 🔬

**Objective**: Ensure 100% alignment between `docs/SCIENTIFIC_BASIS.md`, the actual Source Code, and `docs/*_WHITEBOX.md`.
**Philosophy**: "Rigorous Verification" - We do not assume alignment; we prove it.

---

## 📅 Phase 1: The Audit Loop (Per Agent)
We will proceed Agent by Agent. For each Agent, we execute this 4-step cycle:

### Step 1: Claim Extraction (The Theory)
*   **Action**: I will extract specific claims from `SCIENTIFIC_BASIS.md`.
*   *Example*: "Agent 3 uses LinUCB with Woodbury Matrix Identity."

### Step 2: Code Inspection (The Reality)
*   **Action**: I will read the specific Python file (e.g., `path_planner_agent.py`).
*   **Check**:
    1.  Is the algorithm *actually* implemented, or is it just a placeholder/heuristic?
    2.  Are the parameters consistent with the paper (e.g., $\alpha$ in BKT)?
    3.  **Gap Logging**: Any discrepancy is logged in `task.md`.

### Step 3: Peer Review (The Validation)
*   **Action**: You (User) use **NotebookLM** with my `NOTEBOOKLM_PROMPTS`.
*   **Input**: You feed the paper + my code summary.
*   **Output**: NotebookLM confirms if the math is sound or "naive".

### Step 4: Synchronization (The Fix)
*   **Action**: Based on Code Inspection + NotebookLM Feedback:
    1.  **Refactor Code**: Fix math errors or "naive" implementations.
    2.  **Update Whitebox**: Ensure the architecture diagram matches reality.
    3.  **Refine Scientific Basis**: Update the text to be honest (e.g., change "Concept Drift" to "Static Preferences" if we haven't implemented Drift yet).

---

## 📋 Execution Schedule

| Order | Agent | Key Theory to Verify | Target File |
| :--- | :--- | :--- | :--- |
| **1** | **Knowledge Extraction** | GraphRAG, Fuzzy Search (Levenshtein), Ontology | `knowledge_extraction_agent.py` |
| **2** | **Profiler** | Bayesian Knowledge Tracing (BKT), Hexagonal Arch | `profiler_agent.py` |
| **3** | **Path Planner** | Contextual Bandits (LinUCB), ZPD, Spaced Repetition | `path_planner_agent.py` |
| **4** | **Tutor** | Socratic Method State Machine, Scaffolding | `tutor_agent.py` |
| **5** | **Evaluator** | Bloom's Taxonomy Rubric, IRT Difficulty Adj. | `evaluator_agent.py` |
| **6** | **KAG (System)** | Dual-Loop Learning, Network Centrality | `kag_agent.py` |

---

## 📂 Output Artifacts
At the end of this process, we will have:
1.  **Verified Codebase**: Comments in code linking directly to papers.
2.  **Living Documentation**: `SCIENTIFIC_BASIS.md` will be the "Truth Source".
3.  **Validation Journal**: A log of what we changed based on research e.g. `docs/validation/journal_agent_1.md`.
