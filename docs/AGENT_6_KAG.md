# Agent 6: KAG Agent (Knowledge Graph Aggregator)

## Overview

**File:** `backend/agents/kag_agent.py`  
**Purpose:** Aggregator responsible for Zettelkasten artifact generation, Dual-KG synchronization, and Cross-Learner system analysis.

---

## 🏗️ 1. Zettelkasten Artifact Generation

Transforms learning interactions into atomic knowledge snippets:
- **ATOMIC_NOTE**: Core learning insight (successful understanding).
- **MISCONCEPTION_NOTE**: Documentation of an error for future reference.
- **Logic**: Uses LLM to extract `Key Insight`, `Personal Example`, and `Common Mistakes` from session logs.
- **Storage**: Nodes are created in the **Personal KG** and linked to **CourseConcepts**.

### Node Schema
- `(Learner) -[:CREATED_NOTE]-> (NoteNode)`
- `(NoteNode) -[:ABOUT]-> (CourseConcept)`
- `(NoteNode) -[:LINKS_TO]-> (ExistingNoteNode)` (Semantic/Temporal link)

---

## 🔄 2. Dual-KG Synchronization

Maintains the boundary between shared knowledge and private learner state:
- **Course KG**: Shared, static knowledge (read-only for Agent 6).
- **Personal KG**: Dynamic learner progress (read-write).
- **Sync Events**: Listens for `EVALUATION_COMPLETED` to update the `HAS_MASTERY` relationship level and `ErrorNode` history.

---

## 📊 3. System Learning (Cross-Learner)

Aggregates patterns from the entire student population to improve the course:
| Mechanism | Logic |
| :--- | :--- |
| **Bottleneck Detection** | Identifies concepts with high "Struggle Rates" (> 60%). |
| **Recommendation Engine** | Suggests content changes if prerequisite mastery is low across the cohort. |
| **Prediction** | Predicts intervention points for future learners based on past population failures. |

---

## 🔧 Key Methods

- `_generate_artifact()`: Creates the Zettelkasten note.
- `_sync_dual_kg()`: Updates Neo4j relationships.
- `_analyze_system()`: Batch analysis of all learner graphs.
- `_find_related_notes()`: Cypher-based semantic search for note-linking.
