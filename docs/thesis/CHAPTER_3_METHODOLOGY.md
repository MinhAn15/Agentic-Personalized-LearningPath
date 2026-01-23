# Chapter 3: Methodology

## 3.1 Research Design
This research employs a **quantitative experimental design** (A/B testing) to evaluate the efficacy of a Multi-Agent System (MAS) in delivering personalized learning paths compared to a traditional Retrieval-Augmented Generation (RAG) baseline.

The core hypothesis is that an agentic system with cognitive architecture (Reasoning, Profiling, Memory) produces significantly higher quality pedagogical outcomes than a standard RAG system.

### 3.1.1 Variables
*   **Independent Variable**: The System Architecture (Agentic vs. Baseline).
*   **Dependent Variables**:
    *   **Pedagogical Quality**: Relevance, Personalization, Correctness (assessed by LLM-as-a-Judge).
    *   **System Performance**: Latency (Time to First Token, Total Duration).
    *   **Learner Efficiency**: Step count to mastery (simulated).

## 3.2 Experimental Setup

### 3.2.1 Control Group: Baseline Agent
The control group is a **unimodal RAG agent** designed to represent the current industry standard.
*   **Mechanism**:
    1.  **Retrieval**: Vector Search (Top-K=3) using `BAAI/bge-small-en-v1.5` embeddings.
    2.  **Generation**: Direct LLM call (`sonar` / GPT-4o) with retrieved context.
*   **Limitations**: No user profiling, no multi-step reasoning, no persistent memory.

### 3.2.2 Treatment Group: Agentic System
The experimental group is the **Agentic Personalized Learning Path** system detailed in Chapter 4.
*   **Mechanism**:
    1.  **Knowledge Extraction**: Constructing a semantic Knowledge Graph from course materials.
    2.  **Profiling**: Dynamically updating learner state (Knowledge Tracing).
    3.  **Reasoning**: Tree of Thoughts (ToT) for path planning.
    4.  **Tutoring**: Chain of Thought (CoT) for pedagogical guidance.
    5.  **Evaluation**: Self-reflection via JudgeLM.

## 3.3 Data Collection

### 3.3.1 Synthetic Dataset
To ensure reproducibility and domain agnosticism, a synthetic dataset was generated covering **12 diverse topics**, ranging from Computer Science to Humanities:
1.  **Computer Science**: SQL (Basics to Optimization), Python (OOP, Analysis), Machine Learning.
2.  **Physics**: Quantum Physics (Wave-Particle Duality).
3.  **History**: European History (The Renaissance).

Each topic consists of:
*   **Source Material**: Educational markdown/PDF content.
*   **Learner Profiles**: 5 distinct personas (Beginner to Advanced, Visual vs. Textual learners).

### 3.3.2 Execution Protocol
The experiment runs a batch of **100 episodes** (50 Control, 50 Treatment), randomized across learner profiles and topics.
*   **Infrastructure**: `scripts/run_batch.py` orchestrates the execution.
*   **Environment**: Local execution with Perplexity API for LLM inference (preventing local hardware bottlenecks).

## 3.4 Evaluation Framework

### 3.4.1 Automated Metrics
Results are captured in `data/experiments/results/*.json` and consolidated for analysis.

| Metric | Definition | Measurement Tool |
| :--- | :--- | :--- |
| **Response Latency** | Time from request to final answer. | `scripts/run_experiment.py` timers |
| **Knowledge Retrieval** | Relevance of retrieved chunks to the query. | Hit Rate @ K (vector score) |
| **Throughput** | Successful interactions per minute. | Batch Runner Logs |

### 3.4.2 LLM-as-a-Judge (JudgeLM)
Qualitative assessment is performed by a dedicated **Evaluator Agent** using the JudgeLM framework.
*   **Criteria**:
    1.  **Personalization**: Does the answer adapt to the learner's profile? (Score 1-5)
    2.  **Pedagogical Validity**: Is the teaching method sound? (Score 1-5)
    3.  **Correctness**: Is the factual information accurate? (Score 1-5)

## 3.5 Analysis Method
Data is visualized using **Matplotlib/Seaborn** (`scripts/generate_figures.py`) and an **Interactive Dashboard** (`dashboard/index.html`).
*   **Comparative Analysis**: T-tests to determine statistical significance between Control and Treatment groups.
*   **Distribution Analysis**: Box plots for latency and stability.
