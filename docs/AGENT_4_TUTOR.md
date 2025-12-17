# Agent 4: Tutor Agent

## Overview

**File:** `backend/agents/tutor_agent.py`  
**Lines:** 675 | **Methods:** 21

Teaches using Harvard 7 Principles and Reverse Socratic Method with 3-layer grounding.

## Key Features

1. **Reverse Socratic State Machine** - 5-state progression
2. **3-Layer Grounding** - RAG + Course KG + Personal KG
3. **Harvard 7 Principles Enforcement** - Via Harvard7Enforcer
4. **Dialogue State Management** - Multi-turn conversation tracking

## Socratic States

```python
SocraticState:  # 5-state progression
    PROBING     # State 0: Open-ended question
    SCAFFOLDING # State 1: Hint level 1 (conceptual)
    GUIDING     # State 2: Hint level 2 (structural)
    EXPLAINING  # State 3: Direct explanation
    CONCLUSION  # State 4: Synthesize answer + insight
```

## Main Methods

| Method                          | Purpose                                   |
| ------------------------------- | ----------------------------------------- |
| `execute()`                     | Main tutoring interaction                 |
| `_determine_socratic_state()`   | Select state based on mastery/turns       |
| `_three_layer_grounding()`      | Retrieve from RAG, Course KG, Personal KG |
| `_generate_socratic_response()` | Build response for current state          |
| `_build_socratic_prompt()`      | State-specific prompt construction        |
| `_on_path_planned()`            | Handle PATH_PLANNED event                 |
| `_handoff_to_evaluator()`       | Trigger TUTOR_ASSESSMENT_READY            |
| `enforce_harvard_principles()`  | Apply 7 principles to response            |

## 3-Layer Grounding

```
Layer 1: RAG (Chroma Vector Store)
    → Document chunks semantically similar to query

Layer 2: Course KG (Neo4j)
    → Concept definitions, examples, common_errors
    → Prerequisites and related concepts

Layer 3: Personal KG (Neo4j)
    → Learner's mastery history
    → Past misconceptions and error patterns
    → Previous notes about concept
```

## State Transitions

```
High mastery + Low turns → PROBING (challenge)
Increasing hints → SCAFFOLDING → GUIDING → EXPLAINING
After explanation → CONCLUSION
```

## Event Flow

```
PATH_PLANNED (from Agent 3) → Start tutoring session
    → Multiple turns with Socratic progression
    → TUTOR_ASSESSMENT_READY (to Agent 5)
```

## Dependencies

- `GroundingManager` - 3-layer retrieval
- `Harvard7Enforcer` - Apply teaching principles
- `DialogueState` - Conversation tracking
- Chroma - Vector store for RAG
