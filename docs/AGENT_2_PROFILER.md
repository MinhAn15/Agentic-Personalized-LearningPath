# Agent 2: Profiler Agent

## Overview

**File:** `backend/agents/profiler_agent.py`  
**Lines:** 846 | **Methods:** 19

Builds and maintains 17-dimensional Learner Profile with real-time event updates.

## Key Features

1. **Goal Parsing & Intent Extraction** - Topic, Purpose, Constraint, Level
2. **Diagnostic Assessment** - 3-5 concept probes for initial mastery
3. **Profile Vectorization** - Embedding for similarity search
4. **Real-time Event Updates** - Optimistic locking for concurrency

## Diagnostic States

```python
DiagnosticState:
    NOT_STARTED, IN_PROGRESS, COMPLETED
```

## Main Methods

| Method                         | Purpose                                        |
| ------------------------------ | ---------------------------------------------- |
| `execute()`                    | Create/update learner profile                  |
| `_parse_goal_with_intent()`    | Extract Topic, Purpose, Constraint, Level      |
| `_run_diagnostic_assessment()` | Generate & assess 3-5 diagnostic questions     |
| `_vectorize_profile()`         | Create embedding [KnowledgeState, Style, Goal] |
| `_on_evaluation_completed()`   | Update mastery when Evaluator finishes         |
| `_on_pace_check()`             | Update learning_velocity                       |
| `_on_artifact_created()`       | Track generated notes                          |
| `_estimate_bloom_level()`      | 3-signal Bloom estimation                      |

## 17-Dimensional Profile

```
1. learner_id          10. completed_concepts
2. name                11. error_patterns
3. goal                12. time_budget
4. current_level       13. hours_used
5. preferred_style     14. preferred_content_types
6. session_count       15. avg_mastery_level
7. learning_velocity   16. profile_version (locking)
8. attention_span      17. last_updated
9. concept_mastery_map
```

## Event Subscriptions

| Event                  | Handler                    | Updates           |
| ---------------------- | -------------------------- | ----------------- |
| `EVALUATION_COMPLETED` | `_on_evaluation_completed` | dim 9,10,11,15    |
| `PACE_CHECK`           | `_on_pace_check`           | dim 7             |
| `ARTIFACT_CREATED`     | `_on_artifact_created`     | artifact tracking |

## Dependencies

- `LearnerProfile` model - 17 dimensions
- `VersionConflictError` - Optimistic locking
- Neo4j Personal KG - ErrorEpisode, ArtifactEpisode nodes
