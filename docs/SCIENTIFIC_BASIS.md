# Scientific Basis & Best Practices: SOTA Agentic AI (2024-2025)

This document defines the **Target Architecture** based on the latest research in Large Language Models and Autonomous Agents.

---

## Agent 1: Knowledge Extraction Agent
**Role**: Automated Knowledge Graph Construction & Retrieval.

### 1. LightRAG: Dual-Graph Retrieval
*   **Source**: *Guo, Z., et al. (Oct 2024). "LightRAG: Simple and Fast Retrieval-Augmented Generation."*
*   **Concept**: Combining **Graph-based Indexing** with **Vector Retrieval**.
*   **Target Mechanism**:
    *   **Entity Graph**: For precise structural queries (Command/Query Separation).
    *   **Edge-Attribute Keywords**: Relationships are tagged with *thematic keywords* (e.g., "Impact", "Causality") to support high-level traversal.
    *   **Content Keywords**: High-level topics extracted at the chunk level, indexed in the `DocumentRegistry` for broad semantic search (LightRAG "High-Level" retrieval).
    *   *Upgrade from*: Standard GraphRAG (Edge 2024).

### 2. HippoRAG: Neurobiological Memory
*   **Source**: *Gutiérrez, B., et al. (2024). "HippoRAG: Neurobiologically Inspired Long-Term Memory for LLMs."*
*   **Concept**: Mimicking the Hippocampal indexing theory.
*   **Target Mechanism**: Using a lightweight Knowledge Graph to "index" into heavier vector storage, enabling multi-hop reasoning without massive context windows.

---

## Agent 2: Learner Profiler
**Role**: Tracking Knowledge State & Preferences.

### 1. Deep Knowledge Tracing (DKT) & LLM Tracing
*   **Source**: *Piech, C., et al. (2015). "Deep Knowledge Tracing"* & *Liu, et al. (2024) "Tracing Knowledge State with LLMs".*
*   **Concept**: Knowledge is a latent state best estimated by combining Population Statistics (Prior) with Individual Semantic History (Likelihood), bridging DKT and LLM reasoning.
*   **Target Mechanism**: **Hybrid DKT-LLM Anchoring**
    *   **Prior (The Anchor)**: `CommunityAverage = 1.0 - (Difficulty * 0.15)`. This replaces the fixed bias parameter of DKT, providing a grounded starting point (dealing with Cold Start).
    *   **Adjustment (The Intelligence)**: The LLM analyzes the student's *qualitative history* (errors, misconceptions) to adjust the Prior.
    *   **Formula**: $P(Mastery) = LLM_{adjust}(Prior, History_{semantic})$. This avoids "Hallucinated Competence" by forcing the LLM to justify deviations from the norm.

---

## Agent 3: Path Planner
**Role**: Dynamic Curriculum & Reasoning.

### 1. Tree of Thoughts (ToT)
*   **Source**: *Yao, S., et al. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models."*
*   **Concept**: Treating curriculum generation as a search problem over a tree of "Reasoning Steps" (Thoughts) rather than a greedy selection.
*   **Mechanism (Implemented)**:
    *   **Algorithm**: Beam Search ($b=3$, $d=3$).
    *   **Thought Generator**: `_explore_learning_paths` generates top-3 candidate concepts.
    *   **State Evaluator**: `_evaluate_path_viability` uses LLM to simulate future learner states (Projected Mastery) and scores paths from 0.0 to 1.0.
    *   **Selection**: The system selects the path with the highest cumulative educational value, reducing "Myopia" (short-sighted teaching).

### 2. Spaced Repetition (Ebbinghaus)
*   **Source**: *Ebbinghaus, H. (1885). "Memory: A Contribution to Experimental Psychology."*
*   **Concept**: Forgetting Curve ($R = e^{-t/S}$).
*   **Mechanism**:
    *   Used in **Review Mode** to surface mastered concepts before they decay below threshold.

---

## Agent 4: Tutor Agent
**Role**: Interactive Pedagogy.

### 1. Chain-of-Thought (CoT) & Self-Consistency
*   **Source**: *Wei et al. (2022) "Chain-of-Thought Prompting"* & *Wang et al. (2022) "Self-Consistency Improves Chain of Thought Reasoning".*
*   **Concept**: Making the model "think aloud" and validating logic via consensus.
*   **Target Mechanism**:
    *   **Hidden CoT**: Agent generates 3 internal reasoning traces.
    *   **Self-Consistency**: It compares the traces. If they diverge, it falls back to Probing (low confidence). If they converge, it extracts the first missing step as a Scaffold.
    *   **Leakage Guard**: Explicit filtering of "Final Answer" tokens to prevent premature revelation.

---

## Agent 5: Evaluator Agent
**Role**: Assessment & Grading.

### 1. JudgeLM / LLM-as-a-Judge
*   **Source**: *Zhu, L., et al. (2023). "JudgeLM: Fine-tuning Large Language Models as Scalable Judges."*
*   **Concept**: Using a specialized (or prompted) LLM to grade open-ended responses with high correlation to human experts.
*   **Target Mechanism**:
    *   **G-Eval Steps**:
        1.  Define Criteria (Reasoning, Accuracy, Clarity).
        2.  Generate Scoring Trace.
        3.  Output Weighted Score.
    *   *Upgrade from*: Simple Rubric / IRT.

---

## Agent 6: KAG Agent
**Role**: System Learning & Long-Term Memory.

### 1. MemGPT: Tiered Memory Architecture
*   **Source**: *Packer, C., et al. (2023). "MemGPT: Towards LLMs as Operating Systems."*
*   **Concept**: Managing "Working Context" (Main/RAM) vs "Archival Storage" (Disk/VectorDB).
*   **Target Mechanism**:
    *   **Target Mechanism**:
    *   **Working Memory (RAM)**: `WorkingMemory` class tracks active context.
    *   **Memory Pressure Monitor**: Triggers `_auto_archive` (paging to disk) when > 70% capacity (OS Interrupt equivalent).
    *   **Heartbeat Loop**: `execute` runs recursively if `request_heartbeat=True`, enabling multi-step autonomy (Search -> Read -> Refine).

### 2. Generative Agents
*   **Source**: *Park, J., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior."*
*   **Concept**: Reflection trees where agents synthesis high-level insights from low-level events.
*   **Target Mechanism**: Daily "Reflection" jobs where Agent 6 synthesizes global learning patterns from individual logs.
