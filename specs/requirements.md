# Functional Requirements Specification

## Agent 1: Knowledge Extraction
- [MUST] Parse PDF/Video/Text inputs.
- [MUST] Extract concepts and relationships (Prerequisite, IsA, RelatedTo).
- [MUST] Construct the "Course Knowledge Graph" in Neo4j.
- [SHOULD] Auto-generate definition and examples for concepts.

## Agent 2: Profiler
- [MUST] Ingest user survey/history.
- [MUST] Create a 10-dim `Profile Vector`.
- [MUST] Handle Cold Start (default vector) vs Warm Start.
- [MUST] Persist Profile to Postgres and Neo4j (`Learner` node).

## Agent 3: Path Planner
- [MUST] Implement LinUCB algorithm for concept selection.
- [MUST] Support 5 Chaining Modes: `FORWARD`, `BACKWARD`, `LATERAL`, `ACCELERATE`, `REVIEW`.
- [MUST] Filter candidates based on Prerequisites in Course KG.
- [MUST] Re-plan dynamically upon `EVALUATION_COMPLETED` events.

## Agent 4: Tutor
- [MUST] Socratic Dialogue Engine (state machine).
- [MUST] Implement 3-Layer Grounding (RAG, CourseKG, PersonalKG).
- [MUST] Detect Conflicts: If RAG contradicts KG, trust KG.
- [MUST] Handle `ask_for_clarification` if confidence < 0.5.

## Agent 5: Evaluator
- [MUST] Score user answers (0.0 - 1.0) using LLM.
- [MUST] Classify Error Types (Conceptual, Procedural, Careless).
- [MUST] Make Path Decisions: `MASTERED`, `PROCEED`, `ALTERNATE`, `REMEDIATE`, `RETRY`.
- [MUST] Emit `EVALUATION_COMPLETED` event.

## Agent 6: KAG (Knowledge & Assessment Graph)
- [MUST] Create `ATOMIC_NOTE` for scores >= 0.8.
- [MUST] Create `MISCONCEPTION_NOTE` for scores < 0.8.
- [MUST] Link Notes to Course Concepts (`ABOUT` edge).
- [MUST] Link Notes to each other (Semantic similarity).
- [SHOULD] Analyze global graph for Bottleneck detection.
