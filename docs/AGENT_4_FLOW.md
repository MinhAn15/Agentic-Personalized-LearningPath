# Agent 4: Tutor Agent Flow

## 1. High-Level Control Flow

The Tutor Agent executes a **Reverse Socratic Method** driven by a state machine and supported by varying layers of data grounding.

```mermaid
graph TD
    subgraph Input
        Q[User Question]
        CTX[Context: Concept, History]
    end

    subgraph Phase1_Context[Phase 1: Context Gathering]
        Q --> KG[Query Course KG]
        CTX --> PKG[Query Personal KG]
        KG --> STATE[Learner State]
        PKG --> STATE
    end

    subgraph Phase2_Intent[Phase 2: Intent & Method Ontology]
        Q --> CLASSIFY[Classify Intent]
        STATE --> NEXT_PHASE{Determine Phase}
        CLASSIFY --> NEXT_PHASE
        NEXT_PHASE -->|Intro| PROBE[Lightweight Probing]
        NEXT_PHASE -->|Scaffolding| COT_LOOP[Hidden CoT Loop]
        NEXT_PHASE -->|Assessment| HANDOFF[Handoff to Evaluator]
    end

    subgraph Phase2a_CoT[Dynamic CoT Loop]
        COT_LOOP --> GEN[Generate 3 Traces]
        GEN --> CONSENSUS{Consensus?}
        CONSENSUS -->|Yes| SLICE[Slice Steps]
        CONSENSUS -->|No| FALLBACK[Ask Clarification]
        SLICE --> SERVE[Serve Next Hint]
    end

    subgraph Phase3_Grounding[Phase 3: 3-Layer Grounding]
        PROBE --> G_START[Start Grounding]
        COT_LOOP --> G_START
        G_START -->|Async| RAG[Layer 1: RAG]
        G_START -->|Async| C_KG[Layer 2: Course KG]
        G_START -->|Async| P_KG[Layer 3: Personal KG]
        
        RAG --> MERGE[Merge Context]
        C_KG --> MERGE
        P_KG --> MERGE
        
        MERGE --> CONFLICT{Conflict?}
        CONFLICT -->|Yes| PENALTY[Reduce Confidence]
        CONFLICT -->|No| CALC[Calc Confidence]
    end

    subgraph Phase4_Response[Phase 4: ResponseGen]
        CALC --> CHECK{Confidence > 0.5?}
        CHECK -->|No| FALLBACK_GEN[Ask Clarification]
        CHECK -->|Yes| LLM[Generate Response]
        LLM --> GUARD[Leakage Guard]
        GUARD --> HARVARD[Enforce Harvard 7 Principles]
    end

    subgraph Phase5_Output[Phase 5: Output]
        HARVARD --> SAVE[Save Session State]
        SAVE --> EVENT[Emit 'tutor_guidance_provided']
        EVENT --> JSON[Return Result]
    end
```

## 2. Key Components

### 2.1 Hybrid Architecture: Method Ontology + CoT
The Agent uses a high-level **Method Ontology** (Chandrasekaran 1999) to manage the pedagogical goal, and **Chain-of-Thought** (Wei 2022) to generate the content.

| Phase | Condition | Mechanism |
| :--- | :--- | :--- |
| **INTRO** | New Concept | Lightweight Probing (Socratic Question). |
| **SCAFFOLDING** | Concept identified | **Hidden CoT**: Generates internal traces, slices them, and serves step-by-step hints. |
| **ASSESSMENT** | Mastery check needed | **Handoff**: Transfers control to Agent 5 (Evaluator) for grading. |

### 2.2 3-Layer Grounding (Async)
Parallel retrieval from three sources to ensure hallucination-free responses.

1.  **RAG (Layer 1)**: `_rag_retrieve` (Vector Store). weight=0.4
2.  **Course KG (Layer 2)**: `_course_kg_retrieve` (Neo4j). weight=0.35
3.  **Personal KG (Layer 3)**: `_personal_kg_retrieve` (Neo4j). weight=0.25

**Conflict Detection**: If RAG content contradicts Course KG (semantic similarity < 0.6), Course KG is trusted, and confidence is penalized.

### 2.3 Harvard Enforcer
Post-processing step that validates the response against principles like:
-   **Active Learning**: Does it ask a question?
-   **Cognitive Load**: Is it short (2-4 sentences)?
-   **Feedback**: Does it acknowledge the user's input?
