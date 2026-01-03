# NotebookLM Prompts: Scientific Validation

Use these prompts in **Google NotebookLM** (or similar tools) after uploading the relevant Research Paper (PDF). These prompts are designed to bridge the gap between "Theoretical Theory" and "Actual Implementation".

---

## 🔍 How to Use
1.  **Upload the Paper**: Get the PDF linked in `docs/SCIENTIFIC_BASIS.md`.
2.  **Paste the Context**: Copy the "Context" block below (which summarizes our code implementation).
3.  **Run the Prompt**: Ask NotebookLM to critique and validate the alignment.

---

## Agent 1: Knowledge Extraction vs GraphRAG
**Target Paper**: *Edge, D., et al. (2024). "From Local to Global: A Graph RAG Approach..."*

**Context (Paste this into Chat)**:
> "I am building a Knowledge Extraction Agent. Instead of simple chunking, I implemented 'Ontology-Driven extraction'.
> 1. I use a fixed schema (Concepts, Prerequisites) extracted via LLM.
> 2. I identify entities using Fuzzy Search (Levenshtein distance ~0.8).
> 3. I map relationships directionally (e.g., 'Concept A requires Concept B').
> 4. **Limitation**: This is a 'Local RAG' implementation (finding path A->B). It explicitly LACKS the 'Global Summarization' (Leiden Community Detection) layer described in the GraphRAG paper."

**Prompt**:
> "Based on the GraphRAG paper, critique my implementation.
> 1. Does my use of 'Fuzzy Search' for entity resolution align with the paper's approach to community detection?
> 2. The paper discusses 'Hierarchical Summarization'. My current approach only extracting atomic triples. What specific mechanism from the paper should I add to support 'Global Queries' better?
> 3. Is my strict Schema (Ontology) a constraint or an advantage compared to the paper's unstructured graph generation?"

---

## Agent 2: Profiler vs Bayesian Knowledge Tracing
**Target Paper**: *Corbett & Anderson (1994). "Knowledge Tracing..."*

**Context (Paste this into Chat)**:
> "I implemented Bayesian Knowledge Tracing (BKT) for my Learner Profiler.
> - **BKT Parameters** (class-level constants):
>   - `P_LEARN = 0.1` (Probability of learning after one attempt)
>   - `P_GUESS = 0.25` (Probability of guessing correctly without knowledge)
>   - `P_SLIP = 0.10` (Probability of making a mistake despite knowing)
> - **Update Rule** (Bayes' theorem):
>   - If Correct: `P(Know|Correct) = ((1 - P_SLIP) * P(Know)) / P(Correct)`
>   - If Incorrect: `P(Know|Incorrect) = (P_SLIP * P(Know)) / P(Incorrect)`
>   - Then: `P(Know) += (1 - P(Know)) * P_LEARN`"

**Prompt**:
> "Analyze this BKT implementation against the formal Hidden Markov Model.
> 1. Are my parameter values (`P_LEARN=0.1`, `P_GUESS=0.25`, `P_SLIP=0.10`) reasonable defaults based on the research literature?
> 2. I apply learning gain AFTER the Bayesian update. The paper shows `P(L_n) = P(L_{n-1}) + (1 - P(L_{n-1})) * P(T)`. Is my formula mathematically equivalent?
> 3. What experiments or calibration methods from the paper would help me tune these parameters for different subject domains (e.g., math vs programming)?"

---

## Agent 3: Path Planner vs Contextual Bandits (LinUCB)
**Target Paper**: *Li, L., et al. (2010). "A Contextual-Bandit Approach..."*

**Context (Paste this into Chat)**:
> "I implemented the LinUCB Disjoint algorithm for recommending learning materials.
> - Context ($x_{t,a}$): Learner Embedding Vector + Graph Embeddings.
> - Update: I use the Woodbury Matrix Identity to update the Inverse Covariance Matrix ($A^{-1}$) incrementally ($O(d^2)$) instead of re-inverting ($O(d^3)$).
> - Selection: I chose the arm with the highest Upper Confidence Bound."

**Prompt**:
> "Review my LinUCB implementation details.
> 1. Does my use of Woodbury Matrix Identity preserve the mathematical exactness required by the paper's 'Ridge Regression' core?
> 2. The paper warns about 'non-stationary' environments (user preferences change). My implementation currently assumes static feature dimensions. Based on the experiments in the paper, how significant is the 'Cold Start' problem if I don't use hybrid features?
> 3. Evaluate the theoretical justification for using 'Graph Embeddings' as the context vector. Does the paper support using high-dimensional dense vectors?"

---

## Agent 5: Evaluator vs Item Response Theory (IRT)
**Target Paper**: *Lord, F. M. (1980). "Applications of Item Response Theory..."*

**Context (Paste this into Chat)**:
> "I am using a simplified IRT model to grade learners.
> - I calculate 'Concept Difficulty' dynamically.
> - If high-mastery learners (Top 20%) consistently fail a question, I flag the *Question* as 'High Difficulty' or 'Ambiguous'.
> - I weight the final score based on this difficulty: `Score = RawScore * (1 + DifficultyBonus)`."

**Prompt**:
> "Critique this 'Dynamic Difficulty' approach against standard IRT 2-Parameter Logistic (2PL) models.
> 1. IRT uses a Logit function $P(\theta) = \frac{1}{1 + e^{-a(\theta - b)}}$. My linear multiplier is much simpler. What specific 'Item Characteristic Curve' property am I losing?
> 2. Is determining difficulty solely based on 'High-Mastery Failure' a recognized heuristic in the literature, or is it prone to bias?
> 3. How would you map my 'DifficultyBonus' to the paper's 'Discrimination Parameter' ($a$)?"

---

## Agent 6: KAG vs Zettelkasten & Dual-Loop
**Target Paper**: *Argyris (1976) "Double-Loop Learning" + Luhmann's Zettelkasten*

**Context (Paste this into Chat)**:
> "My Agent 6 performs 'System Learning' (Dual-Loop) and implements 'Dual-Code Theory' (Paivio).
> 1. Single Loop: Tutor corrects the student.
> 2. Dual Loop: Agent 6 aggregates failure rates across ALL students to identify system bottlenecks.
> 3. Artifacts: It generates 'Atomic Notes' (Zettelkasten) that contain BOTH:
>    - **Verbal**: Textual insights and personal examples.
>    - **Visual**: A `Mermaid.js` Concept Map (`graph TD`) visualizing relationships between the new concept and prior knowledge."

**Prompt**:
> "Analyze this Dual-Loop architecture.
> 1. Does aggregating 'Struggle Rate' constitute a valid 'Governing Variable' modification as defined by Argyris? Or is it just 'Single Loop' at a larger scale?
> 2. Luhmann's Zettelkasten emphasizes 'serendipitous connection'. My agent uses strict semantic similarity (Vector Search) to link notes. Does the literature suggest this effectively mimics human 'associative thought', or is it too deterministic?
> 3. Suggest a 'Double-Loop' feedback mechanism from the findings of the paper that I am missing."
