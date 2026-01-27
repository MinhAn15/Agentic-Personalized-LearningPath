# 02. Agent Logic Deep Dive

## 1. Agent 1: The Semantic Reader (Ingestion)
*   **Role:** Processing raw educational content (documents, URLs) into machine-understandable formats.
*   **Key Logic:**
    1.  **Semantic Chunking:** Uses a recursive algorithm to split text by "Topic Shifts" (embedding distance) rather than character counts.
    2.  **Triple Extraction:** Extract `(Head, Relation, Tail)` triples for the Knowledge Graph.
    3.  **Vectorization:** Embeds chunks using `models/embedding-001` ($d=768$).

## 2. Agent 2: The Profiler (State Manager)
*   **Role:** Tracking the learner's evolving state (Mastery, Mood, Preferences).
*   **Algorithm:** `Semantic LKT` (Language Knowledge Tracing).
    *   Input: History of `(Question, Answer, Correctness)`.
    *   Output: $P(m|H_t)$ for each concept.
*   **Latent Vitals:** Tracks Frustration and Boredom using simple sentiment analysis metrics on user chat logs.

## 3. Agent 3: The Path Planner (Strategic Brain)
*   **Role:** Determining *what* to teach next.
*   **Method:** **Tree of Thoughts (ToT)**.
    *   Generates $k=3$ candidate paths.
    *   Simulates student reaction ("Mental Simulation").
    *   Selects path with max Reward Function $r_t$.
*   **States:** `PLANNING` -> `EXECUTING` -> `REPLANIING`.

## 4. Agent 4: The Socratic Tutor (Interface)
*   **Role:** Delivering the content through conversation.
*   **Style:** **Maieutic Method** (Asking questions to stimulate critical thinking) rather than didactics.
*   **Scaffolding:** Dynamically adjusts hint levels based on the Profiler's "Frustration" signal.

## 5. Agent 5: The Evaluator (Judge)
*   **Role:** Assessing student answers.
*   **Logic:**
    *   Compares User Answer vs. Ground Truth.
    *   Assigns a boolean `correct` and a float `quality_score`.
    *   Triggers **Remedial Loops** if correctness < Threshold.
    *   **Security:** Checks for Prompt Injection attempts before passing input to other agents.

## 6. Agent 6: Knowledge Augmented Generator (KAG)
*   **Role:** The "Librarian" providing context to the Tutor.
*   **Mechanism:** **Hybrid Retrieval**.
    *   Step 1: **Vector Search** (Top-5 chunks).
    *   Step 2: **Graph Traversal** (2-hop neighborhood of current concept).
    *   Step 3: **Context Fusion** (Reranking and deduplication).
