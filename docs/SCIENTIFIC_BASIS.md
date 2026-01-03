# Scientific Basis & Best Practices

This document records the theoretical foundations, research papers, and industry best practices that drive the architecture of the Multi-Agent System.

## Agent 1: Knowledge Extraction Agent
**Role**: Automated Knowledge Graph Construction from unstructured text.

### 1. GraphRAG (Local Search Only)
*   **Source**: *Edge, D., et al. (2024). "From Local to Global: A Graph RAG Approach to Query-Focused Summarization." Microsoft Research.*
*   **Application**: Agent 1 implements **Local Search Context** (Neighbors & Paths), enabling precise reasoning for specific concepts (e.g., "What are prerequisites for Join?").
*   **Limitation**: Does NOT currently implement **Global Summarization** (Leiden Community Detection). High-level abstraction queries use standard RAG.
*   **Mechanism**: `_extract_concepts_and_relations` parses text into structured triples `(Subject, Predicate, Object)`.

### 2. Approximate String Matching (Fuzzy Search)
*   **Source**: *Navarro, G. (2001). "A guided tour to approximate string matching." ACM Computing Surveys.*
*   **Application**: To prevent duplication when handling noisy extracted concepts (e.g., "SQL Join" vs "SQL Joins"), Agent 1 uses **Lucene-based Fuzzy Search** (Levenshtein Edit Distance).
*   **Implementation**: `db.index.fulltext.queryNodes` with `~` fuzziness operator.

### 3. Ontology-Driven Extraction
*   **Source**: *Gruber, T. R. (1993). "A translation approach to portable ontology specifications."*
*   **Application**: Uses a strict Schema (`CourseConcept`, `REQUIRES`, `EXPLAINS`) rather than free-form tagging. This ensures the extracted knowledge is "computable" by the Path Planner.
*   **Best Practice**: Hard-typed schema enforcement ensures consistency across different learning materials.

## Agent 2: Learner Profiler
**Role**: Managing Learner State, Preferences, and Long-Term History.

### 1. Hexagonal Architecture (Ports & Adapters)
*   **Source**: *Cockburn, A. (2005). "Hexagonal Architecture."*
*   **Application**: Separates the core *Learner Domain Logic* (Mastery updates, Style inference) from external adaptors (API, Database).
*   **Mechanism**: The `LearnerProfile` is a pure entity isolated from the `Redis` persistence layer, allowing interchangeable storage backends.

### 2. Bayesian Knowledge Tracing (BKT)

*   **Source**: *Corbett, A. T., & Anderson, J. R. (1994). "Knowledge tracing: Modeling the acquisition of procedural knowledge."*
*   **Application**: Models knowledge as a hidden state, updated via Bayesian inference with observations (correct/incorrect responses).
*   **Mechanism**: Uses BKT parameters:
    *   `P(Learn) = 0.1` (Probability of learning after one attempt)
    *   `P(Guess) = 0.25` (Probability of correct answer without knowledge)
    *   `P(Slip) = 0.10` (Probability of incorrect answer despite knowledge)
*   **Formula**: `P(Know|Correct) = P(Correct|Know) * P(Know) / P(Correct)` (Bayes' theorem)

### 3. Distributed Locking (Concurrency Control)
*   **Source**: *Kleppmann, M. (2017). "Designing Data-Intensive Applications" (Redlock Algorithm).*
*   **Application**: Prevents race conditions when multiple agents (e.g., Tutor and Evaluator) try to update the learner's state simultaneously.
*   **Mechanism**: Uses `Redis.lock` with a TTL (Time-To-Live) to serialize write access to the `LearnerProfile`.

## Agent 3: Path Planner
**Role**: Dynamic Curriculum Sequencing and Adaptive Recommendation.

### 1. Zone of Proximal Development (ZPD)
*   **Source**: *Vygotsky, L. S. (1978). "Mind in society."*
*   **Application**: The agent only recommends concepts where the learner has satisfied prerequisites (Grounding) but has not yet achieved mastery.
*   **Mechanism**: `get_reachable_concepts()` filters the Knowledge Graph for nodes where `(Learner)-[:HAS_MASTERY]->(Prereq)` exists.

### 2. Contextual Bandits (LinUCB)
*   **Source**: *Li, L., et al. (2010). "A Contextual-Bandit Approach to Personalized News Article Recommendation."*
*   **Application**: Balances **Exploration** (trying new content formats) vs **Exploitation** (using formats known to work for this learner).
*   **Mechanism**:
    *   **Context**: Learner embeddings (Knowledge State).
    *   **Arm**: Activity Types (Video, Text, Quiz).
    *   **Reward**: Evaluation Score + Time Efficiency.
    *   **Update**: Woodbury Matrix Identity for efficient online updates.

### 3. Spaced Repetition (Forgetting Curve)
*   **Source**: *Ebbinghaus, H. (1885). "Memory: A Contribution to Experimental Psychology."*
*   **Application**: Schedules reviews for previously mastered concepts to prevent decay.
*   **Mechanism**: Before recommending new content, the agent checks `last_review_date` and inserts a "Review Node" if the decay threshold is met (Exponential Decay function).

## Agent 4: Tutor Agent
**Role**: Interactive Instruction and Socratic Dialogue.

### 1. Socratic Method
*   **Source**: *Plato (approx 400 BC). "Meno" (Demonstration of questioning).*
*   **Application**: Instead of lecturing, the agent asks guided questions to help the learner derive the answer.
*   **Mechanism**: State machine transitions (`QUESTIONING` -> `HINTING` -> `EXPLAINING`) based on learner responses.

### 2. Instructional Scaffolding
*   **Source**: *Wood, D., Bruner, J. S., & Ross, G. (1976). "The role of tutoring in problem solving."*
*   **Application**: Providing temporary support that remains until the learner can perform the task independently.
*   **Mechanism**: Dynamic hint generation; hints become less explicit as the learner demonstrates competence.

### 3. Three-Layer Knowledge Grounding
*   **Source**: *Chandrasekaran, B., et al. (1999). "What are ontologies, and why do we need them?" (Knowledge Engineering).*
*   **Application**: Minimizes hallucinations by grounding answers in specific contexts.
*   **Mechanism**:
    1.  **KG**: Structural Grounding (Concepts & Relations).
    2.  **Vector DB**: Semantic Grounding (Text Chunks).
    3.  **LLM**: Linguistic Grounding (Fluency & Syntax).

## Agent 5: Evaluator Agent
**Role**: Assessing Learner Mastery and Providing Feedback.

### 1. Bloom's Taxonomy (Cognitive Domain)
*   **Source**: *Bloom, B. S. (1956). "Taxonomy of educational objectives."*
*   **Application**: Evaluating *Depth of Knowledge* rather than just keyword matching.
*   **Mechanism**: The LLM Rubric explicitly asks: "Does the answer demonstrate Application/Analysis?" (Score 0.8+) vs "Just Recall?" (Score < 0.6).

### 2. Item Response Theory (IRT) - Concept Difficulty
*   **Source**: *Lord, F. M. (1980). "Applications of item response theory to practical testing problems."*
*   **Application**: Validating if a "difficult" question is actually hard or just poorly worded.
*   **Mechanism**: Agent 6 (KAG) aggregates scores per concept; if high-proficiency learners fail a specific concept, its difficulty parameter is adjusted.

### 3. F1 Score (Precision vs Recall in Grading)
*   **Source**: *Van Rijsbergen, C. J. (1979). "Information Retrieval."*
*   **Application**: Balancing "Key Concepts Mentioned" (Recall) vs "Correct Usage" (Precision).
*   **Mechanism**: The scoring algorithm averages `key_concepts_hit` (Recall) and `lack_of_misconceptions` (Precision).

## Agent 6: KAG Agent
**Role**: Knowledge Aggregation and System Learning.

### 1. Zettelkasten Method (Smart Notes)
*   **Source**: *Luhmann, N. (Social Systems Theory).*
*   **Application**: Turning ephemeral quiz answers into permanent "Atomic Notes" for the learner.
*   **Mechanism**: `AtomicNoteGenerator` extracts a strict structure: `Key Insight` + `Personal Example` + `Connection`.

### 2. Dual-Loop Learning
*   **Source**: *Argyris, C. (1976). "Single-loop and double-loop models in research on decision making."*
*   **Application**: The system doesn't just teach (Single Loop); it analyzes *how well* it is teaching (Dual Loop).
*   **Mechanism**: KAG aggregates "Struggle Rates" across learners to identify bad content (the system "learns to learn").

### 3. Dual-Code Theory (Multimodal Learning)
*   **Source**: *Paivio, A. (1971). "Imagery and verbal processes."*
*   **Application**: Facilitates deep understanding by presenting information in two formats: Verbal (Text Notes) and Non-verbal (Visual Concept Maps).
*   **Mechanism**: The agent generates `Mermaid.js` graphs alongside Zettelkasten notes to visualize relationships between concepts.

### 4. Network Analysis (Graph Centrality)
*   **Source**: *Page, L., et al. (1999). "The PageRank Citation Ranking: Bringing Order to the Web."*
*   **Application**: Identifying "Keystone Concepts" that enable many other concepts.
*   **Mechanism**: While currently simple, the architecture allows calculating `Degree Centrality` to recommend high-impact concepts first.
