# NotebookLM Prompts: SOTA Validation (2024-2025)

Use these prompts to validte the transition from Classical Algorithms to **SOTA Agentic AI**.

> [!TIP]
> Upload the target SOTA paper (e.g., Tree of Thoughts PDF) to NotebookLM before running these prompts.

---

## Agent 1: LightRAG / HippoRAG
**Target Paper**: *Guo et al. (2024) "LightRAG" OR Gutiérrez et al. (2024) "HippoRAG"*

**Context**:
> "I am upgrading my Knowledge Extraction Agent.
> - **Current**: Simple GraphRAG (Triples + Fuzzy Search).
> - **Goal**: Implement 'LightRAG' Thematic Indexing.
> - **Architecture Decision**: Instead of maintaining a separate 'Keyword Graph' (which doubles schema complexity), I am implementing **'Edge-Attribute Thematic Indexing'** combined with **'Chunk-Level Content Keywords'**. 
> - **Mechanism**: 
>     1. **Low-Level**: Every relationship edge (e.g., A -> B) carries `keywords` and a `summary` property.
>     2. **High-Level**: Global "Content Keywords" are extracted per document chunk and indexed in `DocumentRegistry` for broad thematic search."

**Prompt**:
> "Evaluate this 'Edge-Attribute' implementation of LightRAG against the original paper.
> 1. Does storing keywords/summaries on *relationships* (edges) achieve the same 'global retrieval' capability as the paper's separate 'Keyword Nodes', or does it limit discovery?
> 2. The paper discusses 'Graph Pruning' to reduce noise. Will filtering edges by their new `keywords` property be an effective pruning strategy for retrieval?
> 3. Are there risks of 'Edge Explosion' (too much text on edges) impacting graph traversal performance?"

---

## Agent 2: semantic Knowledge Tracing (LKT)
**Target Paper**: *Lee et al. (2024) "Language Model Can Do Knowledge Tracing"*

**Context**:
> "I have upgraded my Learner Profiler to **Semantic Knowledge Tracing (LKT)**.
> - **Previous**: Hybrid DKT (Prior + Adjustment).
> - **Current**: **Pure Semantic LKT**.
> - **Mechanism**:
>     1. **Input Format**: I flatten the student's history into a semantic string: `[CLS] ConceptA \n QuestionA [CORRECT] ConceptB...`
>     2. **Prediction**: I append the target concept/question and a `[MASK]` token.
>     3. **Inference**: The LLM predicts the probability of `[CORRECT]` filling the mask based on the full semantic context (not just IDs).
>     4. **Cold Start**: For new students, the model relies purely on the semantic difficulty of the `Question` text."

**Prompt**:
> "Evaluate this LKT implementation against the state-of-the-art:
> 1. Does the 'Input Format' (Question Text + Outcome) provide enough signal for the LLM to capture 'Skill Transfer' (e.g., Algebra helping Physics)?
> 2. The paper discusses 'Instruction Tuning'. Is my zero-shot prompt robust enough, or must I fine-tune on a dataset like ASSISTments?
> 3. How does LKT compare to DKT in terms of 'interpretability'? Can I ask the LLM *why* it predicted 0.8?"

---

## Agent 3: Path Planner (Tree of Thoughts)
**Target Paper**: *Yao et al. (2023) "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"*

**Context**:
> "I have upgraded my Path Planner to use **Tree of Thoughts (ToT)**.
> - **Algorithm**: Beam Search (Width $b=3$, Depth $d=3$).
> - **Search Space**: The Curriculum Knowledge Graph.
> - **State Evaluator**: 
>     1. **Input**: A candidate path (e.g., A -> B -> C).
>     2. **Prompt**: 'Evaluate feasibility on 0.0-1.0 scale. Consider Prerequisite Logic and Cognitive Load.'
>     3. **Output**: Float score used for pruning."

**Validation Prompt**:
> "Evaluate this specific ToT implementation:
> 1. **Beam Width**: Is $b=3$ sufficient for a curriculum graph, or is the risk of missing a global optimum high?
> 2. **Evaluation Prompt**: How can I ensure the LLM's '0.8' core is consistent across different paths? Should I provide 'Few-Shot' examples of good vs bad paths?
> 3. **Pruning**: Should I add a 'Diversity' metric to ensure the 3 beams aren't just minor variations of the same path?"

---

## Agent 4: Chain-of-Thought (CoT)
**Target Paper**: *Wei et al. (2022) "Chain-of-Thought Prompting"*

**Context**:
> "I have upgraded my Tutor Agent to **Hybrid CoT + Method Ontology**.
> - **Architecture**: Hybrid State Machine (Intro -> Scaffolding -> Handoff).
> - **Innovation**: 'Method Ontology' (Chandrasekaran 1999) guides the phase, while 'Chain-of-Thought' (Wei 2022) generates the content.
> - **Mechanism**:
>     1. **Hidden CoT**: Generates 3 internal reasoning traces during the `SCAFFOLDING` phase.
>     2. **Slicing**: The logic is sliced into a sequence of hints (Method Steps) served one per turn.
>     3. **Leakage Guard**: Strict regex filtering prevents the 'Final Answer' from leaking."

**Prompt**:
> "Review this CoT Scaffolding strategy.
> 1. Does the paper suggest that 'Hidden CoT' improves the alignment of the final output compared to standard prompting?
> 2. How can I ensure the CoT doesn't 'leak' the answer too early?
> 3. Suggest a 'Metacognitive' check I can add to the generation step."

---

## Agent 5: JudgeLM / G-Eval
**Target Paper**: *Zhu et al. (2023) "JudgeLM"*

**Context**:
> "I have upgraded my Evaluator Agent to **JudgeLM (Reference-Based)**.
> - **Technique**: 'Reference-as-Prior' (Zhu 2023).
> - **Mechanism**:
>     1. **Prompt Structure**: Pairwise Comparison.
>        - 'Assistant 1': Golden Answer (Score 10/10).
>        - 'Assistant 2': Learner Response.
>     2. **CoT Requirement**: The LLM must output a `justification_trace` JSON field analyzing gaps *before* outputting the `score`.
>     3. **Scoring**: Weighted average of Correctness (0.6), Completeness (0.2), and Clarity (0.2)."

**Prompt**:
> "Critique this G-Eval implementation.
> 1. The paper discusses 'Position Bias' (LLM preferring the first option). How should I structure the prompt to mitigate this when grading single answers?
> 2. Is generating the 'Justification Trace' essential for score reliability, or just for transparency?
> 3. Does JudgeLM perform better with 'Reference-Based' (Golden Answer provided) or 'Reference-Free' evaluation?"

---

## Agent 6: MemGPT
**Target Paper**: *Packer et al. (2023) "MemGPT"*

**Context**:
> "I am upgrading my KAG Agent (System Memory).
> - **Current**: Zettelkasten Notes in VectorDB.
> - **Goal**: 'Tiered Memory System' (OS-style).
> - **Architecture**:
>     1. **Working Context** (RAM): Segmented into System Instructions (Immutable), Core Memory (Pinned User Profile), and FIFO Queue (Conversation).
>     2. **External Context** (Disk): Personal Knowledge Graph (Neo4j) accessed via Tools.
> - **Mechanism (Implemented)**:
>     1. **Interrupts**: `is_pressure_high()` checks token usage. If >70%, triggers `_auto_archive` (Evict Queue -> Summarize -> Store in KG).
>     2. **Heartbeat Loop**: `execute` uses a recursive loop to process `[FUNCTION]` calls from the LLM until a final answer is yielded.
>     3. **Functions**: The Agent has explicit tools: `core_memory_append` (Write RAM), `archival_memory_search` (Read Disk), etc."

**Prompt**:
> "Analyze this MemGPT-inspired architecture.
> 1. The paper defines 'Virtual Context Management'. Is my 'Paging via Function Calling' equivalent to their OS-level interrupt mechanism?
> 2. How does MemGPT decide *when* to yield context (write to disk) to prevent context overflow? I need a correct heuristic.
> 3. What is the role of 'System Events' (Heartbeats) in maintaining agent persistence?"
