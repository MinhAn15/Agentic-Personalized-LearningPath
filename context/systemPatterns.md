# System Patterns & Architectural Decisions

## 1. Multi-Agent Orchestration
We use a **Decentralized Event-Driven Architecture**.
- **Message Bus**: Agents communicate primarily via events (`PATH_PLANNED`, `EVALUATION_COMPLETED`).
- **State Management**:
  - `Redis`: Hot state (session history, RL params).
  - `PostgreSQL`: Durable state (user profiles).
  - `Neo4j`: Knowledge state (relationships).

## 2. The Feedback Loop Pattern
The system is built on a continuous feedback loop:
`Profiler -> Planner -> Tutor -> Evaluator -> (Planner/KAG) -> Tutor`
- **Correction**: The loop corrects itself via Agent 5's decision (`REMEDIATE`/`ALTERNATE`).
- **Optimization**: The loop optimizes itself via Agent 3's LinUCB updates.

## 3. Knowledge Grounding Pattern
To prevent hallucinations, we use a **3-Layer Grounding Stack**:
1.  **Bottom (Trust Source)**: Course KG (curated).
2.  **Middle (Personal Context)**: Personal KG (history).
3.  **Top (Examples)**: Vector RAG (unstructured).
*Logic*: If Conflict -> Trust KG.

## 4. Zettelkasten Knowledge Pattern
- Learning is not just consuming; it's creating nodes.
- **Atomic Nodes**: Successful mastery events.
- **Misconception Nodes**: Failed mastery events with correction metadata.
- **Result**: A personalized graph for every learner.
