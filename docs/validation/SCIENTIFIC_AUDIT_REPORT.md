# Deep Scientific Audit Report
**Date**: 2026-01-03
**Status**: 🔴 CRITICAL GAPS IDENTIFIED
**Auditor**: Antigravity (AI Agent)

## 1. Executive Summary
The Deep Scientific Audit compared the codebase (`backend/agents/*.py`) against the claimed scientific basis (`docs/SCIENTIFIC_BASIS.md`).
While the **Core Architectures** (Hexagonal, Event-Driven, Graph-Based) are solid, **5 out of 6 Agents** have mathematical or logical deviations from their cited research papers.

**Key Definition**: A "Gap" means the code implements a *simplified proxy* (e.g., Weighted Average) instead of the *actual algorithm* (e.g., Bayesian Inference) claimed in the documentation.

| Agent | Status | Critical Gap |
| :--- | :--- | :--- |
| **1. Knowledge Extraction** | 🟡 Partial | Missing **Global Summarization** (Leiden Algorithms) for high-level queries. |
| **2. Profiler** | 🔴 Critical | **False Claim**: Documented "Bayesian Knowledge Tracing" but code uses "Weighted Moving Average". |
| **3. Path Planner** | 🟡 Partial | **Logic Error**: Spaced Repetition prioritizes *Remediation* (Low Mastery) instead of *Review* (Time Decay). |
| **4. Tutor** | 🟢 Verified | **Solid**: Socratic State Machine and Scaffolding are correctly implemented. |
| **5. Evaluator** | 🔴 Critical | **Rubric Failure**: Scores based on *Keyword Match* (Correctness) rather than *Bloom's Depth* (Understanding). |
| **6. KAG** | 🟡 Partial | **Missing Feature**: Generates Text only (Violates Dual-Code Theory/Constructivism requirement for Visuals). |

---

## 2. Detailed Findings & Remediation Plan

### Agent 1: Knowledge Extraction (GraphRAG)
*   **Scientific Basis**: Edge et al. (2024) - GraphRAG.
*   **Finding**: The agent successfully builds a graph (Local Search) but lacks the "Community Detection" layer (Global Search).
*   **Impact**: The system is excellent at specific fact retrieval (A->B) but poor at "Summarize the entire course" tasks.
*   **Recommendation**:
    *   [ ] Integration of `Leiden` algorithm for community detection (Future Phase).
    *   [ ] For now: Update docs to clarify this is "Local GraphRAG".

### Agent 2: Profiler (Bayesian Knowledge Tracing)
*   **Scientific Basis**: Corbett & Anderson (1994) - BKT.
*   **Finding**: Code uses `New = 0.3*Old + 0.7*Score`. This is a Weighted Moving Average. It ignores $P(Guess)$ and $P(Slip)$ parameters essential to BKT.
*   **Impact**: A student guessing correctly is treated the same as a student knowing the answer, inflating mastery.
*   **Recommendation**:
    *   [ ] **Refactor**: Implement true BKT (HMM-based) or a simplified Bayesian update rule.
    *   [ ] **Action**: Query NotebookLM for a pythonic BKT implementation snippet.

### Agent 3: Path Planner (Spaced Repetition)
*   **Scientific Basis**: Ebbinghaus (1885) - Forgetting Curve.
*   **Finding**: Logic `Priority = 1.0 - Mastery` selects concepts the student *doesn't know*. Spaced Repetition should select concepts the student *does know* but is about to forget ($R = e^{-t/S}$).
*   **Impact**: The system never reviews mastered material, leading to decay.
*   **Recommendation**:
    *   [ ] **Refactor**: Implement SuperMemo-2 (SM-2) or a simpler Exponential Decay formula.
    *   [ ] **Action**: Query NotebookLM for the SM-2 algorithm.

### Agent 4: Tutor (Socratic Method)
*   **Scientific Basis**: Collins (1982) - Inquiry Teaching.
*   **Finding**: **VERIFIED**. The State Machine (`PROBING` -> `SCAFFOLDING` -> `GUIDING`) effectively implements the theory.
*   **Recommendation**: None.

### Agent 5: Evaluator (Bloom's Taxonomy)
*   **Scientific Basis**: Bloom (1956).
*   **Finding**: The LLM Rubric prompt asks for `score` based on `expected_answer`. It does not ask "Does this demonstrate Application/Analysis?".
*   **Impact**: High scores are given for Memorization (Recall) even if the learning objective was Analysis.
*   **Recommendation**:
    *   [ ] **Prompt Engineering**: Update `_score_response` to accept a `target_bloom_level` and penalize "Recall-only" answers for higher-level questions.

### Agent 6: KAG (Dual-Code Theory)
*   **Scientific Basis**: Paivio (1971) - Dual Coding.
*   **Finding**: Agent generates text summaries (Zettelkasten). No implementation of Visual Generation (Mermaid/Image).
*   **Impact**: Reduced retention for visual learners. Misses the "Constructivist" goal of building Concept Maps.
*   **Recommendation**:
    *   [ ] **Feature Add**: Add `_generate_mermaid_diagram()` method to KAG Agent.

---

## 3. Immediate Next Steps
1.  **Stop Audit Phase**: The audit is complete.
2.  **Start Refinement Phase**: We need to fix the code to match the science.
3.  **Prioritization**:
    *   **High (Fix Logic)**: Agent 2 (BKT) and Agent 3 (Spaced Repetition).
    *   **Medium (Fix Prompt)**: Agent 5 (Bloom's).
    *   **Low (New Feature)**: Agent 6 (Visuals) and Agent 1 (Leiden).
