# Skill: Tree of Thoughts (ToT) Path Planner Strategy

## 1. Context & Objective
Upgrade the current **LinUCB Path Planner** (Greedy/Myopic) to a **Tree of Thoughts (ToT)** architecture to enable strategic lookahead.
*   **Current Limit:** LinUCB optimizes for *immediate* mastery, failing to identify "scaffolding" paths (teaching a hard concept now to unlock easier concepts later).
*   **Target:** Implement "System 2" reasoning (slow, deliberate search) to plan curriculum paths by simulating future learner states.
*   **Source Authority:** *Tree of Thoughts: Deliberate Problem Solving with LLM* [Yao et al., NeurIPS 2023].

## 2. Architecture Specification

The system must implement the four pillars of ToT defined in the paper: **Decomposition, Generator, Evaluator, and Search Algorithm**.

### 2.1. Thought Decomposition
*   **Definition:** Instead of generating token-by-token, the atomic unit of reasoning is a **"Curriculum Step"** (Thought).
*   **Structure:** A "Thought" $z$ is defined as `{Next_Concept_ID, Pedagogical_Strategy, Expected_Difficulty}`.

### 2.2. Search Algorithm: Breadth-First Search (BFS)
*Rationale:* BFS (Algorithm 1 in Source) allows us to explore the top $b$ most promising curriculum paths in parallel.
*   **Parameters:**
    *   $b$ (Beam Width): **3** (Keep top 3 most promising paths).
    *   $T$ (Depth): **3** (Look ahead 3 teaching steps).
*   **Logic Flow:**
    ```python
    # Pseudo-code based on ToT Algorithm 1
    current_frontier = [initial_student_state]
    for step in range(lookahead_depth):
        candidates = []
        for state in current_frontier:
            # 1. Generator: Propose next concepts
            next_thoughts = generate_thoughts(state, k=3)
            for thought in next_thoughts:
                # 2. Evaluator: Simulate future outcome
                value = evaluate_state(state + thought)
                candidates.append((state + thought, value))
        
        # 3. Selection: Beam Search (Keep top b)
        current_frontier = select_top_b(candidates, b=3)
    
    return best_path_in_frontier
    ```

## 3. Prompt Engineering (Strictly Adapted from Source)

The implementation requires two distinct LLM calls per step: **Generation** and **Valuation**.

### 3.1. Thought Generator (Propose Prompt)
*Reference: Game of 24 "Propose Prompt" (Source)*
*   **Role:** Generate potential next steps without judging them yet.
*   **Adaptation:** Unlike standard CoT which outputs one path, this must output $k$ distinct options.

```text
Input:
Student Profile: {History, Current_Mastery_Vector}
Current Goal: {Target_Concept}

Instruction:
Propose 3 distinct next concepts to teach that could serve as valid next steps.
- Option 1 should be a "Review" step (consolidate foundation).
- Option 2 should be a "Scaffolding" step (intermediate difficulty).
- Option 3 should be a "Challenge" step (direct approach to target).

Output format (JSON):
[
  {"concept": "Concept_A", "strategy": "review", "reason": "..."},
  {"concept": "Concept_B", "strategy": "scaffold", "reason": "..."},
  {"concept": "Concept_C", "strategy": "challenge", "reason": "..."}
]
```

### 3.2. State Evaluator (Value Prompt)
*Reference: Game of 24 "Value Prompt" (Source)*
*   **Role:** Perform "Lookahead Simulation". Predict the learner's future state if this path is chosen.
*   **Strategy:** **(a) Value each state independently** (Source). The LLM acts as a heuristic function $V(s)$.

```text
Input:
Proposed Path: {Current_State} -> {Next_Concept}
Student Profile: {Mastery_Vector}

Instruction:
Evaluate this teaching step. Perform a mental simulation of the student learning this concept.
Consider:
1. Prerequisites: Does the student have the required background?
2. Scaffolding Value: Will learning this make future concepts easier?
3. Frustration Risk: Is the gap too wide?

Assign a "Strategic Value" score (1-10) considering LONG-TERM benefit, not just immediate success.
- 1: Impossible/Harmful (Student will quit).
- 5: Neutral/Safe (Standard progression).
- 10: High Leverage (Unlocks multiple future nodes).

Output format:
{"simulation_reasoning": "If we teach X, the student might struggle initially but will master Y 2x faster...", "value_score": 8}
```

## 4. Implementation Checklist for AI Agent

1.  [ ] **State Manager:** Define a class `ToTNode` that stores the chain of thoughts (path history) and the cumulative value score.
2.  [ ] **Switch Mechanism:**
    *   If `User_Query` implies simple retrieval $\rightarrow$ Use Standard RAG (System 1).
    *   If `User_Query` is "Create a Study Plan" or "I'm stuck, guide me" $\rightarrow$ Trigger **ToT Pipeline** (System 2).
3.  [ ] **Parallel Execution:** Since ToT requires $b \times k$ calls per step, implement `async/await` for the Generation and Evaluation steps to reduce latency (Source notes cost/latency is higher, so optimization is key).
4.  [ ] **Safety Pruning:** Implement a hard rule: If `value_score < 3` (Source), prune the branch immediately (DFS/Pruning logic) to save tokens.

## 5. Whitebox Analysis & Constraints

*   **Why BFS?** The paper demonstrates that for tasks with a clear "depth limit" (like `Game of 24` or a 3-step curriculum), BFS performs better than DFS because it retains diversity at each step (Source).
*   **Myopia vs. Lookahead:** The standard Bandit (LinUCB) only sees the reward at $t+1$. This ToT implementation explicitly prompts the LLM to verify "possibility of reaching 24" (analogous to "reaching Mastery") in the future steps (Source), effectively solving the myopia problem.
*   **Cost Warning:** ToT uses approx 5-10x more tokens than standard CoT (Source). Ensure this is only triggered for high-stakes planning decisions.
