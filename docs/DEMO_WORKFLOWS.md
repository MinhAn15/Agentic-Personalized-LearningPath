# SOTA Agents: Demo Workflows & Presentation Guide

**Target Audience**: Thesis Supervisor / Scientific Review Board
**Goal**: Demonstrate that the system is not just a "Wrapper" but implements specific, verifiable **Algorithmic Mechanisms** (2024-2025 Research).

---

## 🔬 Scientific Narrative
"Many AI Tutors are just simple Prompt Engineering. This system implements **Agentic Cognitive Architectures** inspired by human cognition:"
1.  **Hippocampal Indexing** (LightRAG) -> Agent 1
2.  **Semantic Memory** (LKT) -> Agent 2
3.  **System 2 Planning** (Tree of Thoughts) -> Agent 3
4.  **Metacognition** (Chain of Thought) -> Agent 4
5.  **Critical Thinking** (JudgeLM) -> Agent 5
6.  **Working Memory** (MemGPT) -> Agent 6

---

## 🤖 Agent 1: Knowledge Extraction (The "Hippocampus")
**Scientific Basis**: *LightRAG (Guo 2024)* - Dual-Graph Indexing.
**Demo Goal**: Show retrieval of non-obvious connections via "Thematic Edges".

### 1. Visual Flow
```mermaid
graph LR
    Doc["Document: 'Calculus.pdf'"] --> Chunker["Chunker: 512 Tokens"]
    Chunker --> Extractor
    subgraph "LightRAG Process (Offline)"
        Extractor -->|Extract| Node["Concept: Calculus"]
        Extractor -->|Extract| Edge["Relation: Enables -> Physics"]
        Edge -->|Enrich| Key["Keywords: 'Rate of Change', 'Motion'"]
    end
    Key --> Neo4j["Neo4j Graph (Knowledge Base)"]
    Node --> Neo4j
```

### 2. Live Demo Script
**Command**: `python scripts/test_agent_1.py`
**Look For**:
*   `[GRAPH]`: Creating relationship with `keywords` property.
*   `[RETRIEVAL]`: "Found via Theme" logs.

---

## 🧠 Agent 2: Profiler (The "Semantic Mapped")
**Scientific Basis**: *Semantic LKT (Lee 2024)* - Zero-Shot Knowledge Tracing.
**Demo Goal**: Show "Cold Start" prediction without historical data.

### 1. Visual Flow
```mermaid
graph TD
    Hist["History: None"] --> LLM
    Q["Question: 'What is a derivative?'"] --> LLM
    
    subgraph "Semantic LKT"
        LLM -->|Analyze Semantics| Concept["Concept: Limits/Slope"]
        Concept -->|Estimate Difficulty| Diff["Hard: 0.7"]
        Diff -->|Output| Score["Predicted Mastery: 0.3"]
    end
```

### 2. Live Demo Script
**Command**: `python scripts/test_agent_2_lkt.py`
**Look For**:
*   `[LKT]`: "Cold Start Detected".
*   `[PREDICTION]`: "Semantic Probability: 0.XX".

---

## 🧭 Agent 3: Path Planner (The "Strategist")
**Scientific Basis**: *Tree of Thoughts (Yao 2023)* - Lookahead Search.
**Demo Goal**: Show the agent rejecting a "greedy" easy path in favor of a "strategic" hard path.

### 1. Visual Flow
```mermaid
graph TD
    Start((Current State)) --> B1[Path A: Easy]
    Start --> B2[Path B: Hard]
    
    subgraph "Lookahead (Depth=2)"
        B1 --> C1[Future: Dead End]
        B2 --> C2[Future: High Mastery]
    end
    
    C1 -- Score: 0.2 --> Prune[X]
    C2 -- Score: 0.9 --> Select[✓]
```

### 2. Live Demo Script
**Command**: `python scripts/test_agent_3_tot.py`
**Look For**:
*   `[ToT]`: "Expanding 3 thoughts...".
*   `[EVAL]`: "Path A Score: 0.2", "Path B Score: 0.9".
*   `[DECISION]`: "Selected Path B".

---

## 🧑‍🏫 Agent 4: Tutor (The "Metacognitive Teacher")
**Scientific Basis**: *Chain of Thought (Wei 2022)* - Thinking before Speaking.
**Demo Goal**: Show the "Hidden Thought Trace" where the agent plans the hint before showing it.

### 1. Visual Flow
```mermaid
sequenceDiagram
    Student->>Tutor: "I'm stuck."
    Note right of Tutor: Hidden CoT Phase
    Tutor->>Tutor: 1. Diagnosis: Missing definition
    Tutor->>Tutor: 2. Strategy: Scaffolding
    Tutor->>Tutor: 3. Draft: "Remember the slope..."
    Tutor->>Student: "Let's review the definition of slope."
```

### 2. Live Demo Script
**Command**: `python scripts/test_agent_4_cot.py`
**Look For**:
*   `[CoT TRACE]`: (Internal Monologue).
*   `[RESPONSE]`: (Final Output only).

---

## ⚖️ Agent 5: Evaluator (The "AI Judge")
**Scientific Basis**: *JudgeLM (Zhu 2023)* - Reference-Based Evaluation.
**Demo Goal**: Show "Rubric Alignment" and "Position Bias Mitigation".

### 1. Visual Flow
```mermaid
graph TD
    Ans[Student Answer] --> Judge
    Ref[Golden Answer] --> Judge
    
    subgraph "G-Eval"
        Judge --> Trace[Justification Trace]
        Trace --> Criteria{Criteria Check}
        Criteria -->|Correctness| S1[Score]
        Criteria -->|Clarity| S2[Score]
    end
    
    S1 & S2 --> Final[Final Score: 8.5]
```

### 2. Live Demo Script
**Command**: `python scripts/test_agent_5_judgelm.py`
**Look For**:
*   `"justification_trace": "Student missed keyword..."`.
*   `"score": 0.8`.

---

## 💾 Agent 6: KAG (The "Operating System")
**Scientific Basis**: *MemGPT (Packer 2023)* - Tiered Memory & Interrupts.
**Demo Goal**: Show the "Heartbeat Loop" autonomy.

### 1. Visual Flow
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Monitoring: User Input
    
    state "OS Kernel" as OS {
        Monitoring --> PressureCheck: Token Limit?
        PressureCheck --> AutoArchive: Yes (>70%)
        PressureCheck --> Think: No
        
        Think --> ToolExec: Function Call
        ToolExec --> Think: Heartbeat (Loop)
        Think --> Yield: Final Answer
    }
    
    Yield --> Idle
```

### 2. Live Demo Script
**Command**: `python scripts/test_agent_6_memgpt.py`
**Look For**:
*   `💓 Heartbeat triggered`.
*   `💾 Auto-Archiving...`.
