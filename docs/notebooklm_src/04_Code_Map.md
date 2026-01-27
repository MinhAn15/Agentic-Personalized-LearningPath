# 04. Codebase Map

## Directory Structure

### `/backend`
The core application logic.
*   `agents/`: Contains the 6 Agent Classes.
    *   `knowledge_extraction_agent.py`: Agent 1 (Reader).
    *   `profiler_agent.py`: Agent 2 (Profiler - LKT).
    *   `path_planner_agent.py`: Agent 3 (Planner - ToT).
    *   `tutor_agent.py`: Agent 4 (Tutor).
    *   `evaluator_agent.py`: Agent 5 (Judge).
    *   `kag_agent.py`: Agent 6 (Knowledge Augmented Generator).
*   `database/`: Infrastructure Connections.
    *   `neo4j_ops.py`: Graph queries (Cypher).
    *   `vector_db.py`: Chroma/Qdrant adapters.
*   `main.py`: FastAPI entry point.

### `/scripts`
Utilities for running and testing the system.
*   `verify_*.py`: Individual agent verification scripts.
*   `generate_figures.py`: Generates plots for the thesis.
*   `demo_kag_real.py`: Interactive demo of Agent 6.

### `/frontend`
User Interface (Next.js).
*   `components/`: Reusable UI elements (ChatBox, KnowledgeGraphView).
*   `pages/`: Application routes.

### `/docs`
Documentation.
*   `WHITEBOX_DEEP_DIVE.md`: The primary whitebox analysis document.
*   `notebooklm_src/`: Raw markdown source for AI ingestion.
