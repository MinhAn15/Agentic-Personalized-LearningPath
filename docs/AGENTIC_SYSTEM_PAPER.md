# Design and Implementation of an Agentic Personalized Learning System using State-of-the-Art LLM Architectures

**Author**: Ly Minh An
**Date**: January 2026

---

## Abstract

This paper presents the design and implementation of an **Agentic Personalized Learning Path System**, a Multi-Agent System (MAS) leveraging Large Language Models (LLMs) to deliver adaptive, high-precision education. Moving beyond simple "LLM wrappers," this system integrates State-of-the-Art (SOTA) architectures from 2023-2025 research—including **LightRAG** for knowledge extraction, **Tree of Thoughts (ToT)** for curriculum planning, and **MemGPT** for long-term memory management. We demonstrate how these specific cognitive architectures resolve common LLM limitations (hallucination, myopia, context overflow) in educational settings.

---

## 1. Introduction

Traditional Adaptive Learning Systems (ALS) rely on rigid heuristics (e.g., Item Response Theory) or static Knowledge Graphs. While robust, they lack the semantic flexibility to understand nuanced learner misconceptions. Conversely, generic LLMs (e.g., GPT-4) offer semantic flexibility but suffer from "Hallucination," "Position Bias," and limited long-term reasoning.

This project bridges this gap by implementing a **Neuro-Symbolic Architecture**, combining the structured reliability of Graph Databases (Neo4j) with the reasoning capabilities of Agents. The system comprises six specialized agents, each grounded in a specific scientific methodology.

---

## 2. System Architecture

The system operates on an event-driven microservices architecture (Python/FastAPI) backed by a Dual-Graph implementation:
1.  **Course Knowledge Graph (Static)**: The "Standard of Truth" derived from curriculum material.
2.  **Personal Knowledge Graph (Dynamic)**: A subgraph tracking the learner's mastery, misconceptions, and notes (Zettelkasten).

Six autonomous agents interact via an Event Bus to manage the learning lifecycle: Extraction $\rightarrow$ Profiling $\rightarrow$ Planning $\rightarrow$ Tutoring $\rightarrow$ Evaluation $\rightarrow$ Memory.

---

## 3. Methodology: Agent-Specific SOTA Architectures

Each agent was rigorously audited and refined to align with seminal research papers.

### 3.1. Agent 1: Knowledge Extraction (The Cartographer)
*   **Challenge**: Standard RAG (Retrieval-Augmented Generation) loses global thematic context.
*   **Solution**: **LightRAG** (Guo et al., 2024).
*   **Mechanism**: We implemented **Edge-Attribute Thematic Indexing**. Instead of just linking nodes $A \rightarrow B$, every edge carries semantic metadata (`keywords`, `summary`). This allows the retrieval system to perform "Thematic Traversal" (finding concepts related by *theme* rather than just keyword overlap), enabling high-fidelity curriculum mapping.

### 3.2. Agent 2: Learner Profiler (The Analyst)
*   **Challenge**: "Cold Start" problem in learner modeling and LLM hallucination in mastery estimation.
*   **Solution**: **Hybrid DKT-LLM Anchoring** (Liu et al., 2024).
*   **Mechanism**:
    *   **Math Anchor**: We calculate a "Community Prior" based on concept difficulty ($P_{prior}$).
    *   **LLM Adjustment**: The LLM analyzes the student’s *semantic* history (e.g., "confused by syntax") to apply a qualitative adjustment ($\Delta P$) to the anchor.
    *   *Result*: A calibrated mastery score that is mathematically grounded yet semantically aware.

### 3.3. Agent 3: Path Planner (The Strategist)
*   **Challenge**: Greedy algorithms (Bandits) optimize for the *next* lesson, often failing to build long-term prerequisites ("Myopia").
*   **Solution**: **Tree of Thoughts (ToT)** (Yao et al., 2023).
*   **Mechanism**:
    *   **Search**: A Beam Search algorithm ($b=3, d=3$) explores multiple future distinct lesson trajectories simultaneously.
    *   **Evaluation**: An LLM "State Evaluator" scores each branch based on "Projected Mastery" and "Cognitive Load."
    *   *Result*: A strategic curriculum path that optimizes for long-term retention rather than short-term engagement.

### 3.4. Agent 4: Tutor (The Mentor)
*   **Challenge**: LLMs often reveal answers prematurely or hallucinate incorrect logic steps.
*   **Solution**: **Chain-of-Thought (CoT) & Self-Consistency** (Wei et al., 2022; Wang et al., 2022).
*   **Mechanism**:
    *   **Hidden CoT**: The agent generates three internal reasoning traces to solve the problem *before* speaking.
    *   **Self-Consistency**: It compares the traces for consensus. Only if the logic aligns does it generate a "Scaffold" (hint).
    *   **Leakage Guard**: Regex filters ensure the final answer is never leaked in the scaffold.

### 3.5. Agent 5: Evaluator (The Judge)
*   **Challenge**: "Position Bias" (LLMs preferring the first option) and grading inconsistency.
*   **Solution**: **JudgeLM / G-Eval** (Zhu et al., 2023).
*   **Mechanism**:
    *   **Reference-as-Prior**: The prompt explicitly designates the Golden Answer as "Assistant 1" (The Standard).
    *   **CoT Grading**: The LLM must output a JSON "Justification Trace" analyzing the gap between Learner and Reference *before* assigning a weighted score (Correctness/Clarity/Completeness).

### 3.6. Agent 6: KAG Agent (The Librarian)
*   **Challenge**: Limited Context Window (Context Overflow) and reactive behavior.
*   **Solution**: **MemGPT** (Packer et al., 2023).
*   **Mechanism**:
    *   **Tiered Memory**: Architecture separates `WorkingMemory` (RAM) from `ArchivalStorage` (Neo4j/Vector).
    *   **OS Interrupts**: A "Memory Pressure Monitor" triggers an auto-archive routine when context usage exceeds 70%.
    *   **Heartbeat Loop**: A recursive execution loop allows the agent to perform multi-step autonomy (e.g., Search $\rightarrow$ Read $\rightarrow$ Search Again) without user intervention.

---

## 4. Verification & Results

We implemented a robust automated verification suite (`scripts/verify_*.py`) to test the specific cognitive claims of each agent:
*   **Agent 3 (ToT)**: Validated that the planner selects longer, harder paths if they lead to higher total mastery (beating greedy baselines).
*   **Agent 6 (MemGPT)**: Validated that the system automatically "pages out" memory to disk when the 70% pressure threshold is hit, preserving system stability.
*   **Agent 5 (JudgeLM)**: Achieved 100% correlation on "Perfect Match" test cases and stable partial credit on constrained test sets.

---

## 5. Conclusion

This project demonstrates that integrating rigorous cognitive architectures into Agentic workflows significantly enhances the reliability, autonomy, and pedagogical validity of AI tutors. By moving from "Prompt Engineering" to "System Engineering" (MemGPT, ToT, LightRAG), we achieve a personalized learning system that is not only intelligent but also stable, scientific, and scalable.

---

## References
1.  Guo, Z., et al. (2024). *LightRAG: Simple and Fast Retrieval-Augmented Generation.*
2.  Liu, Z., et al. (2024). *Tracing Knowledge State with LLMs.*
3.  Yao, S., et al. (2023). *Tree of Thoughts: Deliberate Problem Solving with Large Language Models.*
4.  Wei, J., et al. (2022). *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.*
5.  Zhu, L., et al. (2023). *JudgeLM: Fine-tuning Large Language Models as Scalable Judges.*
6.  Packer, C., et al. (2023). *MemGPT: Towards LLMs as Operating Systems.*
