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
*   **Concept**: Curriculum generation as a **Search Problem** over a tree of reasoning steps ($z$: "Curriculum Step"), enabling strategic lookahead (System 2) vs greedy selection (System 1).
*   **Target Mechanism**:
    *   **Thought Decomposition**: A thought is `{Next_Concept_ID, Strategy, Difficulty}`.
    *   **Search**: BFS with Beam Width $b=3$ and Lookahead $T=3$.
    *   **Thought Generator**: Proposes $k=3$ distinct next steps (Review, Scaffolding, Challenge).
    *   **State Evaluator**: LLM simulates future mastery states and assigns a "Strategic Value" (1-10) for pruning.

### 2. Spaced Repetition (Ebbinghaus)
*   **Source**: *Ebbinghaus, H. (1885). "Memory: A Contribution to Experimental Psychology."*
*   **Concept**: Forgetting Curve ($R = e^{-t/S}$).
*   **Mechanism**:
    *   Used in **Review Mode** to surface mastered concepts before they decay below threshold.

---

## Agent 4: Tutor Agent
**Role**: Interactive Pedagogy.

### 1. Dynamic Chain-of-Thought (CoT) & Method Ontology
*   **Source**: *Wei et al. (2022) "Chain-of-Thought Prompting"* & *Chandrasekaran et al. (1999) "Ontologies for Task Method Structures".*
*   **Concept**: Combining **Reasoning Traces** (CoT) with a structured **Task Methodology** (Ontology) to guide the scaffolding process.
*   **Target Mechanism**:
    *   **Hybrid Architecture**: Retains a high-level `DialogueState` (Method Ontology: Intro -> Scaffolding -> Handoff) for flow control.
    *   **Hidden CoT**: Agent generates 3 internal reasoning traces during the `SCAFFOLDING` phase.
    *   **Self-Consistency**: Verifies majority consensus before serving a hint.
    *   **Leakage Guard**: Explicit filtering of "Final Answer" and Slicing Logic to reveal one step at a time.

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
    *   **Working Memory (RAM)**: `WorkingMemory` class segmented into **System Persona**, **Core Memory** (Pinned), and **FIFO Queue**.
    *   **Memory Pressure Monitor**: `is_pressure_high()` trigger (>70%) causing `_auto_archive` (Evict 50% -> Summarize -> Key Insight Node).
    *   **Heartbeat Loop**: `execute` runs a recursive `while` loop, enabling autonomous function chaining (`core_memory_append` -> `archival_memory_search`).
    *   **Tools**: `core_memory_append`, `core_memory_replace`, `archival_memory_insert`, `archival_memory_search` (Hybrid Retrieval).

### 2. Generative Agents
*   **Source**: *Park, J., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior."*
*   **Concept**: Reflection trees where agents synthesis high-level insights from low-level events.
*   **Target Mechanism**: Daily "Reflection" jobs where Agent 6 synthesizes global learning patterns from individual logs.
