# Agent 3: Path Planner Agent

## Overview

**File:** `backend/agents/path_planner_agent.py`  
**Lines:** 496 | **Methods:** 14

Generates optimal learning sequences using Multi-Armed Bandit RL with adaptive chaining.

## Key Features

1. **Multi-Armed Bandit with UCB** - Balance exploration/exploitation
2. **3 Chaining Modes** - Forward, Backward, Lateral sequencing
3. **Pacing Recommendations** - Based on time budget usage
4. **Success Probability** - Predict path completion likelihood

## Chaining Modes

```python
ChainingMode:
    FORWARD   # Normal progression (after PROCEED/MASTERED)
    BACKWARD  # Review prerequisites (after REMEDIATE)
    LATERAL   # Try alternative paths (after ALTERNATE)

EvaluationDecision:  # From Agent 5
    PROCEED, MASTERED, REMEDIATE, ALTERNATE, RETRY
```

## Main Methods

| Method                             | Purpose                              |
| ---------------------------------- | ------------------------------------ |
| `execute()`                        | Generate personalized learning path  |
| `_select_chain_mode()`             | Choose mode based on last evaluation |
| `_generate_adaptive_path()`        | Build path using chaining strategy   |
| `_get_chain_candidates()`          | Get concepts based on relationships  |
| `_determine_pacing()`              | Calculate pacing recommendations     |
| `_recommend_resources()`           | Suggest content types per concept    |
| `_calculate_success_probability()` | Predict completion likelihood        |

## RL Engine Integration

```python
RLEngine with BanditStrategy:
    - UCB (Upper Confidence Bound) for concept selection
    - Tracks arm statistics per concept
    - Balances known-good vs unexplored concepts
```

## Success Probability Formula

```
P(success) = 0.4 × avg_mastery
           + 0.4 × time_fit
           - 0.2 × difficulty_penalty
```

## Output Structure

```python
{
    'path': [
        {
            'concept_id': str,
            'title': str,
            'difficulty': int,
            'bloom_level': str,
            'estimated_time': int,
            'recommended_content': str
        }
    ],
    'chain_mode': str,
    'success_probability': float,
    'pacing': str  # COMFORTABLE, MODERATE, TIGHT
}
```

## Dependencies

- `RLEngine` - Multi-Armed Bandit implementation
- `BanditStrategy` - UCB algorithm
- `rl_config.py` - Thresholds and weights
