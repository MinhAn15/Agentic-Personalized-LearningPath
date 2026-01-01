# Project Brief: Agentic Personalized Learning Path

## 🎯 Goal
Develop a Master's Thesis project that uses a **Multi-Agent System** to create a highly personalized, adaptive learning experience. The system moves beyond traditional linear courses by using Knowledge Graphs and LLMs to adapt content, path, and feedback to the learner's real-time state.

## 🧠 Core Philosophy
- **Dynamic Adaptation**: The syllabus changes based on mastery.
- **Constructivism**: Learners build knowledge (Zettelkasten) rather than just consuming it.
- **Socratic Method**: The Tutor agent asks questions to stimulate critical thinking.
- **Dual-Graph Grounding**: Combining Course Knowledge (Static) with Personal Knowledge (Dynamic) to prevent hallucinations.

## 🏗 High-Level Architecture (The 6 Agents)
1.  **Agent 1 (Knowledge Extraction)**: Ingests documents (PDF/Video) -> Builds Course Graph.
2.  **Agent 2 (Profiler)**: Analyzes user surveys/Cold Start -> Creates Learner Profile Vector.
3.  **Agent 3 (Path Planner)**: Uses LinUCB (RL) -> Selects optimum next Learning Concept.
4.  **Agent 4 (Tutor)**: Socratic Dialogue + 3-Layer Grounding (RAG+KG+Personal) -> Teaches content.
5.  **Agent 5 (Evaluator)**: Assesses responses -> Updates Mastery Scores -> Routes (Proceed/Remediate).
6.  **Agent 6 (KAG)**: Knowledge & Assessment Graph. Converts interaction into Atomic Notes (Zettelkasten) for long-term retention.

## 🛠 Key Technologies
- **Backend**: Python (FastAPI/LangGraph concepts).
- **AI**: LLMs (Gemini/OpenAI), Embeddings.
- **Data**: Neo4j (Graph), PostgreSQL (Relational), Redis (Cache/State), VectorDB.
