# Agent 5: Evaluator Agent

## Overview

**File:** `backend/agents/evaluator_agent.py`  
**Lines:** 537 | **Methods:** 12

Assesses learner understanding, classifies errors, tracks mastery, and makes path decisions.

## Key Features

1. **Semantic Scoring** - LLM + embedding similarity + KG grounding
2. **5-Type Error Classification** - Decision tree based on score
3. **Mastery Tracking** - Weighted moving average with Bloom adjustments
4. **5-Path Decision Engine** - Per THESIS Table 3.10

## Error Types

```python
ErrorType:  # 5 classifications
    CORRECT     # Score ≥ 0.95
    CARELESS    # Minor typo, high similarity
    INCOMPLETE  # Partial answer, missing details
    PROCEDURAL  # Wrong method, right concept
    CONCEPTUAL  # Fundamental misunderstanding

PathDecision:  # 5 next actions
    MASTERED    # ≥ 0.9 mastery, no severe misconceptions
    PROCEED     # ≥ 0.8 mastery, no conceptual error
    ALTERNATE   # 0.6-0.79 + conceptual error
    RETRY       # Moderate issues
    REMEDIATE   # < 0.4 or persistent misconceptions
```

## Main Methods

| Method                        | Purpose                            |
| ----------------------------- | ---------------------------------- |
| `execute()`                   | Main evaluation pipeline           |
| `_score_response()`           | 0-1 scoring with LLM               |
| `_classify_error()`           | Determine error type               |
| `_detect_misconception()`     | Identify specific misunderstanding |
| `_generate_feedback()`        | Personalized feedback text         |
| `_make_path_decision()`       | Decide next action                 |
| `_update_learner_mastery()`   | Update mastery level               |
| `_on_assessment_ready()`      | Handle TUTOR_ASSESSMENT_READY      |
| `generate_feedback_for_kag()` | Feedback for artifact generation   |

## Core Modules

```python
SemanticScorer:
    Score = 0.4×semantic_sim + 0.5×llm_score + 0.1×grounding_boost

ErrorClassifier:
    Decision tree: score → similarity check → KG ontology match

MasteryTracker:
    mastery_new = (1-λ) × mastery_old + λ × score  (λ = 0.3)
    Bloom boost: +0.05 if score ≥ 0.9
    Bloom penalty: -0.05 if struggling with higher-order

DecisionEngine:
    Implements THESIS Table 3.10 logic

InstructorNotificationService:
    Triggers alert if score < 0.4 (Critical Failure)
```

## Event Flow

```
TUTOR_ASSESSMENT_READY (from Agent 4)
    → Score response
    → Classify error
    → Detect misconceptions
    → Classify error
    → Detect misconceptions
    → Update mastery
    → Check for critical failure (Alert Instructor)
    → Make path decision
    → EVALUATION_COMPLETED (to Agent 6, Agent 2, Agent 3)
```

## Dependencies

- `SemanticScorer` - Multi-signal scoring
- `ErrorClassifier` - Decision tree + ontology
- `MasteryTracker` - Weighted average + Bloom
- `DecisionEngine` - 5-path logic
- `InstructorNotificationService` - Alerting system
- `EvaluationResult` - Complete result dataclass
