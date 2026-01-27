# 03. Algorithms & Formulas

## 1. Reward Function ($r_t$)
Used by the Path Planner (Agent 3) to evaluate the optimality of a proposed learning path node.

$$ r_t = \alpha \cdot S_{eval} + \beta \cdot \mathbb{I}_{complete} - \gamma \cdot P_{drop} $$

Where:
*   $S_{eval} \in [0, 1]$: Quality score of the student's answer (from Agent 5).
*   $\mathbb{I}_{complete} \in \{0, 1\}$: Binary indicator of concept mastery (threshold crossed).
*   $P_{drop} \in [0, 1]$: Probability of dropout (predicted Frustration/Boredom).
*   **Weights:** $\alpha=0.6, \beta=0.4, \gamma=1.0$ (High penalty for dropout).

## 2. Tree of Thoughts (ToT) Beam Search
Used to explore the space of possible next pedagogical moves.
*   **Hyperparameters:**
    *   Beam Width ($b$): 3
    *   Max Depth ($d$): 3
*   **Process:**
    1.  Generate $b$ thoughts $y_{t}$.
    2.  Evaluate each thought values $v(y_t)$ using Mental Simulation.
    3.  Prune thoughts where $v(y_t) < \text{threshold}$.
    4.  Repeat for $d$ steps.

## 3. Knowledge Tracing (LKT) Update
Used by Agent 2 to update the probability of mastery $P(m)$.
We use a **Bayesian Update** approximation via LLM or simplified formula:
$$ P(m_{t+1}) = P(L|A) = \frac{P(A|L) \cdot P(L)}{P(A)} $$
Where:
*   $L$: State of "Learned".
*   $A$: Observation of "Correct Answer".

## 4. Hybrid Retrieval Score ($S_{final}$)
Used by Agent 6 to rank context chunks.
$$ S_{final} = w_v \cdot S_{vector} + w_g \cdot S_{graph} $$
Where:
*   $S_{vector}$: Cosine similarity of embeddings.
*   $S_{graph}$: Topological relevance (1.0 for direct neighbor, 0.5 for 2-hop).
*   $w_v = 0.7, w_g = 0.3$ (biased towards semantic match).
