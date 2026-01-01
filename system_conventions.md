# System Conventions & Operational Procedures

> **Role**: Coding Assistant for "Agentic Personalized Learning Path" (Thesis Project).
> **Objective**: Build a robust, scalable multi-agent system for personalized education.

## 1. Coding Standards
- **Language**: Python 3.10+
- **Style**: PEP 8 compatible. Use clear variable names (snake_case).
- **Architecture**: Modular Agentic architecture. Each Agent must be decoupled.
- **Async**: Use `asyncio` for all I/O bound operations (Database, LLM calls).
- **Error Handling**: 
  - Use `try-except` blocks for external calls.
  - Log errors using the standard `logging` module.
  - Fail gracefully; do not crash the entire pipeline.

## 2. Tech Stack Rules
- **Neo4j (Graph DB)**:
  - Used for Knowledge Graphs (CourseKG, PersonalKG).
  - Use `MERGE` for idempotent writes.
  - Nodes must have consistent labels (`Learner`, `CourseConcept`, `NoteNode`).
- **PostgreSQL**:
  - Used for structured User Profile data and transactional history.
- **Vector DB** (LlamaIndex/Chroma):
  - Used for RAG.
  - Semantic Search fallback.

## 3. Workflow & Definition of Done
- **Before Coding**: Check `specs/` for requirements.
- **After Coding**: 
  - Update `context/activeContext.md` with new progress.
  - Ensure no "magic numbers" (use constants).
  - Documentation updated if architecture changes.

## 4. Documentation Structure
- `/specs/`: Functional constraints (Truth).
- `/context/`: Memory Bank for Agent state (Context).
- `/docs/`: Human-readable detailed explanations.
