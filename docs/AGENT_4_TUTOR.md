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
SocraticState:  # Adaptive Cognitive Loop
    PROBING     # State 0: Open-ended question
    SCAFFOLDING # State 1: Hint level 1 (conceptual)
    GUIDING     # State 2: Hint level 2 (structural)
    EXPLAINING  # State 3: Direct explanation
    CONCLUSION  # State 4: Synthesize answer + insight

    # Adaptive States
    REFUTATION  # Address Misconception (Cognitive Dissonance)
    ELABORATION # Expand on near-correct answer
    TEACH_BACK  # Reversed Socratic (Protégé Effect)

UserIntent:
    HELP_SEEKING # Stuck, error -> Bias towards SCAFFOLDING
    SENSE_MAKING # Curious, why? -> Bias towards PROBING
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
Layer 1: RAG (Local LlamaIndex Vector)
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

## State Transitions (Adaptive)

```
- Help Seeking + Low Turns → SCAFFOLDING (Reduce frustration)
- Sense Making + Low Turns → PROBING (Deepen inquiry)
- High mastery + Low turns → TEACH_BACK (Reversed Socratic)
- Misconception → REFUTATION
- Near correct → ELABORATION
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
- `DialogueState` & `UserIntent` - Conversation, state, and intent tracking
- LlamaIndex - Local vector store for RAG
