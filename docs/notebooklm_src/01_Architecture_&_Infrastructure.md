# 01. Architecture & Infrastructure Deep Dive

## 1. High-Level Architecture
The system follows a **Multi-Agent Microservices** architecture, orchestrated via a central API Gateway (FastAPI). It strictly adheres to the **Clean Architecture** principles, separating Domain Logic (Agents) from Infrastructure (Databases).

### System Components
1.  **Orchestrator (Backend API):** FastAPI service that routes user requests to specific agents.
2.  **Agent Mesh:** 6 Specialized Agents (Reader, Profiler, Planner, Tutor, Evaluator, KAG) interacting asynchronously.
3.  **Data Persistence Layer:**
    *   **Neo4j (Knowledge Graph):** Stores topological relationships (Prerequisites, Related-To) between concepts.
    *   **Qdrant/Weaviate (Vector Database):** Stores high-dimensional embeddings of text chunks for semantic retrieval.
    *   **PostgreSQL:** Stores user profiles, chat history, and experiment logs.
    *   **Redis:** Caches hot data (session state, recent thoughts) for low-latency access.

## 2. The Hybrid RAG Engine (Agent 6)
A core innovation is the **Hybrid Retrieval-Augmented Generation** engine.
*   **Vector Search (Reactive):** Finds content visually similar to the query.
*   **Graph Traversal (Proactive):** Finds content logically related to the query (e.g., finding a required concept that was never explicitly mentioned).

## 3. Deployment Infrastructure (Docker Compose)
The entire stack is containerized for reproducibility ("Science-in-a-Box").

### Service Mesh
*   `backend`: The main FastAPI Python application.
*   `neo4j`: Graph Database with APOC plugin enabled for complex traversals.
*   `vector_db`: Standalone service for dense vector storage.
*   `postgres`: Relational data.
*   `redis`: In-memory cache.

### Network Topology
*   All services run on an internal bridge network `agent_mesh`.
*   Only the `backend` (Port 8000) and `frontend` (Port 3000) are exposed to the host.

## 4. API Gateway Design
*   **Protocol:** REST/HTTP for client-server, internal Python method calls for Agent-to-Agent.
*   **Auth:** JWT-based authentication via `Depend(get_current_user)`.
*   **State Management:** Stateless API; Session state is hydrated from Redis per request.
