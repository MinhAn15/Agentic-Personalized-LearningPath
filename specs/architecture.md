# System Architecture

## Overview
The system is composed of 6 specialized AI Agents collaborating to deliver a personalized learning path.

## Agent Roles

| Agent | Name | Role | Inputs | Outputs |
|-------|------|------|--------|---------|
| **1** | **Knowledge Extraction** | Librarian | Documents | Course KG (Neo4j) |
| **2** | **Profiler** | Psychologist | User Survey | Profile Vector (PG/Redis) |
| **3** | **Path Planner** | Navigator | Profile, Progress | Next Concept (Event) |
| **4** | **Tutor** | Teacher | Concept, Question | Socratic Response |
| **5** | **Evaluator** | Examiner | Answer | Score, Decision |
| **6** | **KAG** | Scribe | Session Data | Personal KG Notes |

## Data Flow
1. **User** -> Agent 2 (Profile created).
2. Agent 2 -> Agent 3 (Initial Plan).
3. Agent 3 -> Agent 4 (Teach Concept A).
4. **User** <-> Agent 4 (Socratic Loop).
5. **User** -> Agent 5 (Submit Answer).
6. Agent 5 -> Agent 6 (Create Note).
7. Agent 5 -> Agent 3 (Update Plan based on Decision).

## Storage Architecture
- **Neo4j**: 
  - `(:CourseConcept)`: Static curriculum.
  - `(:Learner)-[:HAS_MASTERY]->(:CourseConcept)`: Dynamic state.
  - `(:NoteNode)`: Zettelkasten artifacts.
- **PostgreSQL**:
  - User credentials, Logs, Raw Analytics.
- **Redis**:
  - Session Context (Chat history).
  - LinUCB Model parameters (`A`, `b` matrices).
