# Agent 2: Profiler Agent - Whitebox Analysis

## 1. Context & Objectives
The **Profiler Agent** is the "State Manager" of the personalized learning system. Unlike traditional LMSs that store static user data, Agent 2 maintains a dynamic, multidimensional **Learner Profile** that evolves in real-time.
**Objective**: To construct a 10-dimensional feature vector $\mathbf{x}_t$ representing the learner's state, used by the Path Planner (Agent 3) for LinUCB bandit optimization.

## 2. Theoretical Framework

### 2.1 The Learner Model (10-Dimensional Vector)
We model the learner state $\mathcal{S}$ as a vector $\mathbf{x} \in \mathbb{R}^{10}$, comprising:
1.  **Knowledge State ($x_0$)**: Average mastery across key concepts ($0 \le x_0 \le 1$).
2.  **Learning Style ($x_{1-4}$)**: One-hot encoding of VARK (Visual, Aural, Read/Write, Kinesthetic).
3.  **Skill Level ($x_5$)**: Normalized difficulty handling (Beginner=0.2, Intermediate=0.5, Advanced=0.8).
4.  **Time Constraints ($x_6$)**: Normalized available time per session.
5.  **Cognitive Load ($x_7$)**: Bloom's Taxonomy level (1=Remember to 6=Create), normalized to $[0,1]$.
6.  **Velocity ($x_8$)**: Learning rate (concepts/hour).
7.  **Scope ($x_9$)**: Relative size of the target goal.

### 2.2 Cold Start Problem & Graph RAG
To initialize $\mathbf{x}_0$ without prior data, we employ a **Diagnostic Assessment** using **Graph RAG**:
1.  **Retrieval**: Given a goal (e.g., "Learn SQL"), we query the Knowledge Graph for "Topographic Anchors"—concepts with high centrality (PageRank).
2.  **Generation**: The LLM generates 5 diagnostic questions based on these anchors.
3.  **Estimation**: User responses are scored to estimate initial mastery and skill level.

## 3. Algorithm Details

### 3.1 Profile Vectorization (`_vectorize_profile`)
Transforms the JSON profile into the vector $\mathbf{x}$ for the Contextual Bandit:
$$
\mathbf{x} = [ \mu_{mastery}, \mathbb{I}_{vis}, \mathbb{I}_{aud}, \mathbb{I}_{read}, \mathbb{I}_{kin}, \eta_{skill}, \tau_{time}, \beta_{bloom}, \nu_{vel}, \sigma_{scope} ]
$$
Where $\mathbb{I}$ is the indicator function for learning style.

### 3.2 Dynamic Interest Decay
To reflect the forgetting curve and shifting interests, we apply an exponential decay to interest tags upon every major interaction:
$$
I_{tag}(t+1) = I_{tag}(t) \times \lambda
$$
Where $\lambda = 0.95$ (decay factor). Tags falling below threshold $\epsilon = 0.1$ are pruned.

### 3.3 Scalable Event Handling (Distributed Lock)
Since the agent is stateful and reactive (Event-Driven), we implement specific handlers for concurrency control:
*   **Race Condition**: Multiple agents (Evaluator, Timer) may update the profile simultaneously.
*   **Solution**: **Redis Distributed Lock** (RedLock algorithm).
*   **Mechanism**:
    ```python
    lock = redis.lock(f"lock:learner:{id}")
    if lock.acquire():
        state = read()
        state = update(state)
        write(state)
        lock.release()
    ```
This ensures Atomic State Updates in a distributed environment (Kubernetes).

## 4. Implementation Logic

### 4.1 Persistence Layer (Dual-Write)
1.  **PostgreSQL**: Canonical source of truth (ACID compliance).
2.  **Neo4j**: Personal Knowledge Graph ("Shadow Graph").
    *   **Nodes**: `:Learner`, `:MasteryNode` (link to Course Concepts), `:ErrorEpisode`.
    *   **Edges**: `[:HAS_MASTERY]`, `[:HAS_ERROR]`.
3.  **Redis**: Hot State Cache (TTL 1 hour) for low-latency read by Agent 3.

### 4.2 Bloom's Taxonomy Estimation
Bloom's level is dynamically estimated from quiz results:
$$
Bloom = 0.6 \cdot Score + 0.25 \cdot Difficulty + 0.15 \cdot QType_{boost}
$$
Where $QType_{boost}$ favors synthesis/application questions over factual recall.

## 5. Conclusion
Agent 2 provides the "Context" ($\mathbf{x}_t$) required for the Agentic RL loop. By combining Graph RAG for initialization and Event-Driven updates for evolution, it solves the Cold Start problem while maintaining high responsiveness.
