# Agent 6: KAG Agent (Knowledge Artifact Generator)

## Overview

**File:** `backend/agents/kag_agent.py`  
**Lines:** 783 | **Methods:** 20

Generates Zettelkasten artifacts, synchronizes Dual-KG, and analyzes system-wide patterns.

## Key Features

1. **Zettelkasten Artifact Generation** - 4 artifact types
2. **Dual-KG Synchronization** - 3 layers (Course, Personal, Progress)
3. **System Learning** - Aggregate patterns for curriculum improvement
4. **PKM Query Support** - 4 query types for personal knowledge management

## Artifact Types

```python
ArtifactType:
    ATOMIC_NOTE       # Single learning insight (score ≥ 0.75)
    MISCONCEPTION_NOTE # Document error (score < 0.5, conceptual)
    SUMMARY_NOTE      # Session synthesis (3+ concepts)
    CONCEPT_MAP       # Visual relationship graph
```

## Zettelkasten 4 Principles

```
1. Atomicity      - One note = One key insight
2. Own Words      - LLM paraphrases with learner context
3. Contextualization - personal_example + common_mistake
4. Linking        - LINKSTO relationships in KG
```

## Main Methods

| Method                        | Purpose                                  |
| ----------------------------- | ---------------------------------------- |
| `execute()`                   | Router for generate/sync/analyze actions |
| `_generate_artifact()`        | Create Zettelkasten note                 |
| `_extract_atomic_note()`      | LLM-based note extraction                |
| `_find_related_notes()`       | Semantic similarity search               |
| `_create_note_node()`         | Neo4j NoteNode creation                  |
| `_create_note_links()`        | LINKSTO relationships                    |
| `_sync_dual_kg()`             | Synchronize 3 KG layers                  |
| `_analyze_system()`           | Aggregate learner patterns               |
| `_generate_recommendations()` | Curriculum improvements                  |
| `_on_evaluation_completed()`  | Auto-generate artifact on eval           |

## Dual-KG Layers

```
Layer 1: Course KG (Read-Only)
    → 217 concept nodes (definitions, examples, errors)
    → Reference + source of truth

Layer 2: Personal Notes KG (Read-Write)
    → NoteNode (Zettelkasten artifacts)
    → REFERENCES → CourseConcept
    → LINKSTO → other Notes

Layer 3: Progress KG (System-Managed)
    → SessionNodes, MasteryNodes, ErrorPatternNodes
    → Analytics + re-planning triggers
```

## 4 PKM Query Types

```python
KGSynchronizer.query_temporal()   # Notes from last N days
KGSynchronizer.query_retrieval()  # All notes about concept X
KGSynchronizer.query_synthesis()  # Most connected concepts
KGSynchronizer.query_review()     # Notes for struggling concepts
```

## Event Flow

```
EVALUATION_COMPLETED (from Agent 5)
    → Generate Zettelkasten note
    → Sync to Personal KG (Layer 2)
    → Create LINKSTO relationships
    → Update MasteryNode (Layer 3)
    → ARTIFACT_CREATED (to Agent 2)
```

## System Analysis Output

```python
{
    'statistics': {...},           # Per-concept stats
    'patterns': {
        'difficult_concepts': [],  # avg_mastery < 0.4
        'easy_concepts': [],       # avg_mastery > 0.8
        'insights': []             # Summary messages
    },
    'recommendations': [],         # Curriculum improvements
    'predictions': []              # Next cohort interventions
}
```

## Dependencies

- `AtomicNoteGenerator` - LLM-based note creation
- `KGSynchronizer` - Dual-KG operations
- `ArtifactState` - Track created artifacts
- `AtomicNote`, `MisconceptionNote` - Note models
