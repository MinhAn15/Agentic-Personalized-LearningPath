# PROJECT CRITIQUE INPUT PACKAGE

## 1. ARCHITECTURE & TECHNICAL STACK

### Folder Structure
```
/
├── backend/
│   ├── agents/          # Agent Logic (1-6)
│   ├── api/             # FastAPI Routes
│   ├── core/            # Shared Logic (State, Events, Enforcers)
│   ├── database/        # DB Factories (Neo4j, Postgres, Redis)
│   ├── models/          # Pydantic Schemas
│   └── main.py          # Entry Point
├── frontend/            # Next.js Application
├── data/                # Synthetic Datasets
├── docs/                # Thesis & Whitebox Documentation
├── scripts/             # Experiment Runners
└── docker-compose.yml   # Infrastructure
```

### Technical Stack
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: Next.js (TypeScript, Tailwind CSS)
- **Database**:
    - **Neo4j**: Knowledge Graph & Vector Search
    - **PostgreSQL**: Relational Data & JSONB
    - **Redis**: State Caching & Distributed Locks
- **AI/LLM**:
    - **LlamaIndex**: RAG & Embeddings
    - **Google Gemini**: Main LLM (via `google-generativeai`)
    - **OpenAI**: Compatible fallback

## 2. THESIS SPECIFICATIONS

### Table 3.10: 5-Path Decision Logic (from Agent 5)
Logic deciding the next step based on JudgeLM Score and Error Type:

| Decision | Condition | Adjustment |
| :--- | :--- | :--- |
| **MASTERED** | Score >= 0.9 | -0.05 if Diff>=4 |
| **PROCEED** | Score >= 0.8 | -0.05 if Diff>=4 |
| **ALTERNATE** | Score >= 0.6 | -0.05 if Diff>=4 |
| **REMEDIATE** | < 0.6 AND Error=CONCEPTUAL | N/A |
| **RETRY** | < 0.6 AND Error!=CONCEPTUAL | N/A |

### Harvard 7 Principles Integration
- **Location**: `backend/core/harvard_enforcer.py` and `backend/agents/tutor_agent.py`.
- **Mechanism**: A dedicated `Harvard7Enforcer` class post-processes Tutor generation to ensure compliance (e.g., ensuring "Active Learning" by forcing a question in the output).

### Bloom's Taxonomy Mapping
- **Levels Used**: 6 Levels (Remember, Understand, Apply, Analyze, Evaluate, Create).
- **Implementation**: Normalized to [0, 1] range in Profiler Agent for Vectorization.

### Ablation Study Plan
- **Comparison**: Agentic System vs. Unimodal RAG (Baseline).
- **Variables**:
    - **Without CoT**: Test Tutor performance without reasoning traces.
    - **Without Global Theme**: Test Knowledge Extraction quality without Domain Injection.
    - **Without 3-Way Entity Resolution**: Test Graph quality.

## 3. CURRENT IMPLEMENTATION STATUS

- [x] **Agent 1 (Knowledge Extraction)**: Implemented (`backend/agents/knowledge_extraction_agent.py`) - Features LightRAG & MultiDocFusion.
- [x] **Agent 2 (Profiler)**: Implemented (`backend/agents/profiler_agent.py`) - Features LKT & 10-Dim Vector.
- [x] **Agent 3 (Path Planner)**: Implemented (`backend/agents/path_planner_agent.py`) - Features ToT & LinUCB.
- [x] **Agent 4 (Tutor)**: Implemented (`backend/agents/tutor_agent.py`) - Features Socratic State & Harvard 7.
- [x] **Agent 5 (Evaluator)**: Implemented (`backend/agents/evaluator_agent.py`) - Features JudgeLM & 5-Path Logic.
- [x] **Agent 6 (KAG)**: Implemented (`backend/agents/kag_agent.py`) - Features MemGPT & Zettelkasten.
- [x] **Frontend (Student UI)**: Initial Next.js setup present (`frontend/`).
- [x] **Dual-KG Synchronization**: Implemented via `CentralStateManager` & Dual-Write logic in Profiler.

## 4. DATA & EVALUATION

- **Dataset**: Synthetic Dataset covering 12 topics (CS, Physics, History).
- **Baseline System**: Unimodal RAG Agent (Vector Search + LLM).
- **Metrics**:
    - **Pedagogical**: Personalization Score, Correctness (JudgeLM).
    - **Performance**: Latency (Time to First Token).
    - **Efficiency**: Steps to Mastery.

## 5. SOURCE CODE SNIPPETS

### backend/main.py
```python
from fastapi import FastAPI
# ... (imports)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DBs & Agents
    # ...
    # Initialize agents (KE, Profiler, PathPlanner, Tutor, Evaluator, KAG)
    # Set agents in routes
```

### backend/agents/tutor_agent.py (Harvard 7 & Socratic)
```python
class TutorAgent(BaseAgent):
    def __init__(self, ...):
        # ...
        self.harvard_enforcer = Harvard7Enforcer()
        # ...

    async def execute(self, ...):
        # ...
        # Phase 3: Socratic State
        socratic_state = self._determine_socratic_state(intent, state)
        # Phase 6: Harvard 7 Enforcement
        response = self.enforce_harvard_principles(...)
```

### requirements.txt
```text
llama-index-core>=0.10.0
google-generativeai>=0.4.0
neo4j>=5.18.0
asyncpg>=0.29.0
redis>=5.0.0
# ...
```

## 6. CRITICAL QUESTIONS (DRAFT ANSWERS)

1.  **Deadline**: [USER TO FILL] (e.g., "End of Feb 2026")
2.  **Real Data**: Currently using Synthetic Data (12 topics). Plan to pilot with [NUMBER] students.
3.  **Priority**: **Novelty & Paper Acceptance (Q1)** is the top priority, followed by Code Quality.
4.  **Test Scale**: 100 episodes (50 Treatment vs 50 Control) as per Methodology.
5.  **Mentors**: Currently self-reviewing with AI assistance.

## 7. CURRENT STRUGGLE
**[USER TO FILL]**: (e.g., "Proving that the 'Novelty' of combining these specific papers is sufficient for a Q1 journal vs just being a system integration paper.")
