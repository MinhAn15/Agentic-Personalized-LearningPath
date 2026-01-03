# Scientific Validation Journal: Agent 3 (Path Planner)

## 1. Audit Summary
*   **Agent**: Path Planner
*   **Source Code**: `backend/agents/path_planner_agent.py`
*   **Scientific Basis**: `docs/SCIENTIFIC_BASIS.md`
*   **Primary Source**: Yao et al. (2023) "Tree of Thoughts".
*   **Previous**: LinUCB (Li 2010) - Found to be "Myopic" (System 1).
*   **New Target**: Tree of Thoughts (ToT) - Deliberate Problem Solving (System 2).
*   **Status**: 🔵 **REFINEMENT PLANNED** (Code upgrade in progress).

## 2. NotebookLM Feedback (2026-01-03)
**Prompt**: Validate transition from LinUCB to ToT for Curriculum Sequencing.

### Critique of LinUCB (Myopia)
*   **Verdict**: **Confirmed**. LinUCB optimizes for *immediate* mastery gain (Greedy), failing to see that teaching a hard prerequisite (A) now makes future concepts (B, C, D) accessible.
*   **Analogy**: LinUCB is like a chess player taking a pawn (Greedy) vs ToT sacrificing a pawn to checkmate (Lookahead).

### Design Decisions (NotebookLM Recommendations)
1.  **Search Strategy**: **Beam Search** ($b=3$).
    *   *Why*: DFS is risky (might find deep but suboptimal path). BFS checks multiple starting points. Beam Search strikes balance between breadth and memory.
2.  **Evaluator Mechanism**: **"Value Each State Independently"**.
    *   *Mechanism*: Ask LLM to rate the "Educational Feasibility" of a path (e.g., A -> B -> C) on a scale.
    *   *Constraint*: Prompt must require *reasoning* before the score to prevent calibration error.
3.  **Cost Acceptance**: ToT is computationally expensive. We accept higher latency for higher quality curriculum planning.

## 3. Implementation Plan
*   **Algorithm**: Beam Search ($Depth=3, Width=3$).
*   **Functions**:
    1.  `_generate_thoughts`: Suggest 3 next concepts.
    2.  `_evaluate_states`: Score them (0.0-1.0) using LLM.
    3.  `_select_best_beam`: Expand top-k.

## 4. Verification Checkpoints
*   [ ] Does `_evaluate_states` output reliable scores?
*   [ ] Does the planner select a "High Investment" path (Hard -> Easy) over a "low hanging fruit" path?
