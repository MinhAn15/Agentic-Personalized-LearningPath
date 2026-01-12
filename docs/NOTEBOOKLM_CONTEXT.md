# NotebookLM Context: Agentic Personalized Learning Path

> **Purpose**: This document provides comprehensive context for NotebookLM to understand the thesis project.
> **Usage**: Upload this file FIRST before any Whitebox documents.

---

## 1. Project Overview

### 1.1 What Is This Project?

This is a **Master's Thesis** project that develops a **Multi-Agent AI System** for personalized learning. The system uses 6 specialized AI agents to:
1. **Extract knowledge** from course materials
2. **Profile learners** and track their understanding
3. **Plan optimal learning paths** through content
4. **Teach** using Socratic dialogue
5. **Evaluate** learner responses
6. **Manage long-term memory** for the system

### 1.2 Academic Context

| Attribute | Value |
|-----------|-------|
| **Degree** | Master's Thesis |
| **Field** | Computer Science / AI |
| **Focus** | Agentic AI + Personalized Learning |
| **Year** | 2026 |
| **Language** | Vietnamese thesis, English technical terms |

### 1.3 Core Philosophy

```
Traditional LMS                    This System
─────────────────                  ────────────
Linear syllabus          →         Adaptive path (RL-based)
Static content           →         Dynamic scaffolding (LLM)
Binary grading           →         Multi-factor evaluation (JudgeLM)
No memory                →         Tiered memory (MemGPT)
```

---

## 2. The 6-Agent Architecture

### 2.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AGENTIC PERSONALIZED LEARNING                       │
│                                                                         │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐      │
│   │ Agent 1  │────►│ Agent 2  │────►│ Agent 3  │────►│ Agent 4  │      │
│   │ EXTRACT  │     │ PROFILE  │     │   PLAN   │     │   TUTOR  │      │
│   │ (LightRAG)│     │  (LKT)   │     │  (ToT)   │     │  (CoT)   │      │
│   └──────────┘     └──────────┘     └──────────┘     └────┬─────┘      │
│                                                           │             │
│                    ┌──────────┐                     ┌─────▼─────┐       │
│                    │ Agent 6  │◄────────────────────│ Agent 5   │       │
│                    │  MEMORY  │                     │ EVALUATE  │       │
│                    │ (MemGPT) │                     │ (JudgeLM) │       │
│                    └──────────┘                     └───────────┘       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent Summary Table

| # | Agent Name | Role | SOTA Paper | Key Innovation |
|---|------------|------|------------|----------------|
| 1 | Knowledge Extraction | Convert documents → Knowledge Graph | LightRAG (Guo 2024) | Edge-Attribute Thematic Indexing |
| 2 | Profiler | Create & update learner profile | LKT (Lee 2024) | Semantic Mastery Prediction via LLM |
| 3 | Path Planner | Generate optimal curriculum | ToT (Yao 2023) | Beam Search with State Evaluation |
| 4 | Tutor | Interactive teaching | CoT (Wei 2022) | Hidden CoT + Slicing Logic |
| 5 | Evaluator | Grade responses + route | JudgeLM (Zhu 2023) | Reference-as-Prior Scoring |
| 6 | KAG (Memory) | Long-term system memory | MemGPT (Packer 2023) | Tiered Memory + Heartbeat Loop |

---

## 3. Technology Stack

### 3.1 Core Technologies

| Layer | Technology | Purpose |
|-------|------------|---------|
| **LLM** | Google Gemini | All agents use this for reasoning |
| **Embeddings** | Gemini Embedding | Semantic similarity (768-dim) |
| **Graph DB** | Neo4j (v5.19) | Course KG + Personal KG + **Vector Index** |
| **Relational DB** | PostgreSQL | User data, sessions |
| **Cache** | Redis | State, locks, hot data |
| **Backend** | Python + FastAPI | API layer |

### 3.2 Key Libraries

- `llama-index`: LLM orchestration, RAG
- `asyncio`: Concurrent processing
- `numpy`: Vector operations (10-dim profile)

---

## 4. Scientific Basis (SOTA Papers)

Each agent implements a specific State-of-the-Art paper. The thesis contribution is the **adaptation** and **integration** of these papers into a cohesive learning system.

### 4.1 Agent 1: LightRAG (Guo et al., 2024)

**Original**: Dual-Graph architecture (Entity Graph + Keyword Graph)
**Adaptation**: Edge-Attribute Keywords (store on relationships, not separate graph)
**Justification**: Single-graph simplicity while maintaining thematic retrieval

### 4.2 Agent 2: LKT (Lee et al., 2024)

**Original**: Language Model for Knowledge Tracing
**Adaptation**: Zero-shot LKT with formatted history `[CLS] Concept \n Question [CORRECT]`
**Innovation**: Cold-start handling via semantic difficulty estimation

### 4.3 Agent 3: ToT (Yao et al., 2023)

**Original**: Tree of Thoughts for deliberate problem solving
**Adaptation**: Curriculum generation as search problem
**Parameters**: Beam Width b=3, Depth d=3

### 4.4 Agent 4: CoT (Wei et al., 2022)

**Original**: Chain-of-Thought prompting
**Adaptation**: Hidden CoT + Slicing for scaffolding
**Guard**: Leakage prevention (no answer reveal)

### 4.5 Agent 5: JudgeLM (Zhu et al., 2023)

**Original**: LLM-as-a-Judge for evaluation
**Adaptation**: Reference-as-Prior with 3-criteria rubric
**Hybrid**: BKT parameters for mastery tracking

### 4.6 Agent 6: MemGPT (Packer et al., 2023)

**Original**: LLMs as Operating Systems
**Adaptation**: WorkingMemory class with System/Core/FIFO
**Mechanism**: Memory pressure > 70% triggers auto-archive

---

## 5. Key Data Structures

### 5.1 Learner Profile Vector (10-dim)

```
x = [μ_mastery, I_visual, I_auditory, I_read, I_kinesthetic, 
     η_skill, τ_time, β_bloom, ν_velocity, σ_scope]
```

| Dim | Name | Description |
|-----|------|-------------|
| 0 | μ_mastery | Average mastery across concepts [0,1] |
| 1-4 | VARK | One-hot learning style |
| 5 | η_skill | Skill level (beginner/intermediate/advanced) |
| 6 | τ_time | Time budget |
| 7 | β_bloom | Current Bloom's level |
| 8 | ν_velocity | Learning pace |
| 9 | σ_scope | Goal scope |

### 5.2 Knowledge Graph Schema

```
(:CourseConcept {concept_id, name, definition, bloom_level, difficulty})
-[:REQUIRES {weight}]->(:CourseConcept)
-[:NEXT {keywords, summary}]->(:CourseConcept)
-[:SIMILAR_TO {similarity}]->(:CourseConcept)
```

### 5.3 WorkingMemory (Agent 6)

```python
class WorkingMemory:
    system_instructions: str  # Immutable persona
    core_memory: Dict         # Pinned facts (user profile)
    fifo_queue: List          # Rolling conversation
```

---

## 6. Evaluation Metrics Summary

Each agent has defined evaluation metrics in their Whitebox Section 5:

| Agent | Key Metric | Target |
|-------|------------|--------|
| 1 | Extraction F1 | ≥ 0.85 |
| 2 | Mastery Prediction MAE | ≤ 0.15 |
| 3 | Path Completion Rate | ≥ 70% |
| 4 | Engagement Rate | ≥ 70% |
| 5 | Human Correlation (ρ) | ≥ 0.85 |
| 6 | Memory Overflow Rate | 0% |

---

## 7. Thesis Contributions

### 7.1 Novel Contributions

1. **Integration**: First system combining 6 SOTA papers into unified learning agent
2. **Adaptation**: Each paper adapted for educational context (not just NLP tasks)
3. **Cold-Start Solution**: LKT + Graph RAG for new learner profiling
4. **Memory Management**: MemGPT for infinite-context tutoring

### 7.2 Limitations (Honest)

1. No large-scale user study (synthetic evaluation)
2. Single LLM backend (Gemini only)
3. No fine-tuning (zero-shot only)

---

## 8. How to Use This Document

When generating content for NotebookLM:

1. **Reference the Agent number** (e.g., "Agent 3" not just "Path Planner")
2. **Include SOTA paper name and year** in all slides
3. **Use metrics from Section 6** for evaluation claims
4. **Be honest about limitations** from Section 7.2
5. **Keep technical terms in English** even in Vietnamese slides
