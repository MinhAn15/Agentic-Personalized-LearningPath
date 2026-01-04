# Scientific Basis & Best Practices: SOTA Agentic AI (2024-2025)

This document defines the **Target Architecture** based on the latest research in Large Language Models and Autonomous Agents.

---

## Agent 1: Knowledge Extraction Agent
**Role**: Automated Knowledge Graph Construction & Retrieval.

### 1. LightRAG: Dual-Graph Retrieval (Integrated Architecture)
*   **Source**: *Guo, Z., et al. (Oct 2024). "LightRAG"* & *Gutiérrez, B., et al. (2024). "HippoRAG".*
*   **Concept**: Combining **Graph-based Indexing** with **Vector Retrieval** to mimic Neurobiological Memory (Hippocampal Indexing).
*   **Target Mechanism**:
    *   **Entity Graph**: For precise structural queries (Command/Query Separation).
    *   **Edge-Attribute Keywords**: Relationships are tagged with *thematic keywords* (e.g., "Impact", "Causality") to support high-level traversal.
    *   **Content Keywords**: High-level topics extracted at the chunk level, indexed in the `DocumentRegistry` to serve as the "Hippocampal Index" into the heavier Vector Storage.
    *   *Note*: This implementation unifies LightRAG's dual-graph approach with HippoRAG's associative indexing theory.

---

## Agent 2: Learner Profiler
**Role**: Tracking Knowledge State & Preferences.

### 1. Semantic Knowledge Tracing (LKT/DKT Hybrid)
*   **Source**: *Lee, et al. (2024). "Language Model Can Do Knowledge Tracing"* & *Piech, C., et al. (2015). "Deep Knowledge Tracing".*
*   **Concept**: Deep Knowledge Tracing (DKT) uses LSTM to capture long-term dependencies. LKT replaces the LSTM with a Pre-trained Language Model (PLM) to solve "Cold Start" via semantic understanding.
*   **Target Mechanism**:
    *   **Input**: Concatenated textual history (`[CLS] Concept1 \n Question1 [CORRECT] ...`).
    *   **Logic**: Using the LLM to predict the probability of correctness for the next step based on the full semantic context, not just ID sequences.
    *   **Cold Start**: Leveraging the LLM's pre-trained knowledge to predict mastery even with zero history, purely from the semantic difficulty of the question.

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
