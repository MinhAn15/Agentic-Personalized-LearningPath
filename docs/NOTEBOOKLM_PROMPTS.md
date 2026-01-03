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
> - **Architecture Decision**: Instead of maintaining a separate 'Keyword Graph' (which doubles schema complexity), I am implementing **'Edge-Attribute Thematic Indexing'**. 
> - **Mechanism**: Every relationship edge (e.g., A -> B) now carries `keywords` and a `summary` property, allowing the LLM to filter paths by theme (e.g., 'Traverse only edges related to *database optimization*')."

**Prompt**:
> "Evaluate this 'Edge-Attribute' implementation of LightRAG against the original paper.
> 1. Does storing keywords/summaries on *relationships* (edges) achieve the same 'global retrieval' capability as the paper's separate 'Keyword Nodes', or does it limit discovery?
> 2. The paper discusses 'Graph Pruning' to reduce noise. Will filtering edges by their new `keywords` property be an effective pruning strategy for retrieval?
> 3. Are there risks of 'Edge Explosion' (too much text on edges) impacting graph traversal performance?"

---

## Agent 2: Deep Knowledge Tracing (DKT)
**Target Paper**: *Piech et al. (2015) "Deep Knowledge Tracing" or Liu et al. (2024) "LLM Tracing"*

**Context**:
> "I am upgrading my Learner Profiler.
> - **Current**: Hybrid DKT-LLM Anchoring.
> - **Mechanism**:
>     1. **Community Prior**: I calculate a baseline pass rate based on difficulty (e.g., Hard=25%).
>     2. **LLM Adjustment**: I provide the LLM with this Prior AND the student's recent semantic history (errors, misconceptions).
>     3. **Prompt**: 'The baseline is [Prior]. Given the student's history [X], adjust this probability up or down.'"

**Prompt**:
> "Evaluate this 'Hybrid Anchoring' approach against the principles of Deep Knowledge Tracing.
> 1. Does providing a 'Community Prior' effectively solve the 'Cold Start' problem mentioned in the DKT paper (where LSTM hidden states are initialized)?
> 2. By asking the LLM to 'adjust' a baseline rather than predict from scratch, do I sufficiently mitigate the 'Calibration Error' (Hallucination) risk?
> 3. DKT assumes 'slip' and 'guess' are latent. How does my system account for 'Lucky Guesses' if the LLM sees a correct answer?"

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
> "I am upgrading my Tutor Agent.
> - **Current**: Socratic State Machine (Fixed transitions).
> - **Goal**: 'Dynamic Chain-of-Thought'.
> - **Mechanism**:
>     1. When a student errs, the Agent generates a hidden Connect-the-Dots trace (CoT).
>     2. It reveals this trace one step at a time as 'Scaffolding'."

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
>     1. **Main Context (RAM)**: Current Active Goal + Immediate Errors.
>     2. **External Context (Disk)**: Knowledge Graph + Vector Archive.
> - **Mechanism (Implemented)**:
>     1. **WorkingMemory**: Class tracking current token usage vs max context.
>     2. **Interrupt**: `is_pressure_high()` checks if context > 70%. If true, injects "SYSTEM ALERT" and triggers `_auto_archive`.
>     3. **Heartbeat**: The `execute` method runs a `while` loop, allowing the agent to chain multiple actions (Search -> Read) before yielding to user."

**Prompt**:
> "Analyze this MemGPT-inspired architecture.
> 1. The paper defines 'Virtual Context Management'. Is my 'Paging via Function Calling' equivalent to their OS-level interrupt mechanism?
> 2. How does MemGPT decide *when* to yield context (write to disk) to prevent context overflow? I need a correct heuristic.
> 3. What is the role of 'System Events' (Heartbeats) in maintaining agent persistence?"
