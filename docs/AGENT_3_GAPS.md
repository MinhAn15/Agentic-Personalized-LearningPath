# Agent 3: Identified Gaps & Technical Debt

> **Status**: Open
> **Date**: 2026-01-04
> **Priority**: High

## 1. ToT Implementation is Disconnected
- **Status**: 🔴 **CRITICAL**
- **Description**: The method `_get_reachable_concepts` returns `[]`.
- **Impact**: The Beam Search (`_beam_search`) immediately terminates, effectively disabling the ToT Planner.
- **Required Fix**: Implement Graph traversal in `_get_reachable_concepts` OR implement the "Thought Generator" LLM prompt to propose steps.

## 2. Weak Evaluator Prompt
- **Status**: 🔴 **CRITICAL**
- **Description**: `_evaluate_path_viability` uses a generic "Act as a Curriculum Architect" prompt.
- **Impact**: It lacks the "Mental Simulation" required by ToT (predicting future mastery state).
- **Required Fix**: alignment with `skill.md` "State Evaluator" specification (Simulation Reasoning + Value Score).

## 3. Missing Thought Generator
- **Status**: 🟡 **MAJOR**
- **Description**: Current logic selects concepts via Graph Neighbors.
- **Impact**: It misses "Strategic" steps (Review vs Scaffold vs Challenge) which are the core "Thoughts" in the ToT paper.
- **Required Fix**: Implement the "Propose Prompt" (Review/Scaffold/Challenge) in `_explore_learning_paths`.

## 4. Hybrid Conflicting Logic
- **Status**: 🟡 **MAJOR**
- **Description**: The class has both `_generate_adaptive_path` (LinUCB) and `_explore_learning_paths` (ToT).
- **Impact**: It is unclear which valid logic is prioritized. `execute` currently calls `_generate_adaptive_path` (LinUCB).
- **Required Fix**: Refactor `execute` to use ToT (`_explore_learning_paths`) as the primary "System 2" planner, potentially keeping LinUCB as a "System 1" heuristic.
