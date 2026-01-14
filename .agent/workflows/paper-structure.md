---
description: Q1 Paper Structure for Agentic Personalized Learning Path
---

# Q1 Paper Writing Workflow

This workflow provides a comprehensive template for writing a Q1-level research paper based on the **Agentic Personalized Learning Path** system. Use this as a guide when working with AI assistants to generate paper content.

---

## 📋 Paper Metadata

**Target Venues (Q1 Journals/Conferences):**
- Computers & Education (Elsevier, IF: 12.0)
- IEEE Transactions on Learning Technologies (IF: 4.5)
- User Modeling and User-Adapted Interaction (Springer, IF: 4.6)
- ACL/EMNLP/NAACL (NLP Conferences - Top-tier)
- AIED Conference (AI in Education)

**Paper Type:** Full Research Paper (8-12 pages)

**Keywords:**
- Personalized Learning
- Large Language Models
- Multi-Agent Systems
- Knowledge Graphs
- Adaptive Education Technology

---

## 📑 PAPER STRUCTURE

### 1. TITLE (Concise, Impact-focused)

**Format:** `[Method]: [Problem] via [Key Innovation]`

**Examples:**
- "AgenticTutor: Personalized Learning Path Generation via Multi-Agent LLM Orchestration"
- "Beyond Prompt Engineering: A Six-Agent Cognitive Architecture for Adaptive Education"

---

### 2. ABSTRACT (250 words max)

**Structure (IMRAD):**
```
[CONTEXT] 1-2 sentences on the problem domain.
[GAP] 1 sentence on what existing solutions lack.
[APPROACH] 2-3 sentences on your method.
[RESULTS] 2-3 sentences on key findings with numbers.
[CONCLUSION] 1 sentence on significance.
```

**Template:**
```
Personalized learning remains challenging due to [GAP: cold-start, static curricula, lack of metacognition]. 
Existing LLM tutors are limited to single-turn Q&A without [missing capability].

We present [SYSTEM NAME], a multi-agent architecture comprising six specialized LLM agents 
that implement cognitive mechanisms from [PAPERS]: LightRAG for knowledge indexing (Agent 1), 
Semantic LKT for mastery prediction (Agent 2), Tree of Thoughts for curriculum planning (Agent 3), 
Chain of Thought for tutoring (Agent 4), JudgeLM for assessment (Agent 5), and MemGPT for 
long-term memory (Agent 6).

Experiments on [DATASET/SCENARIO] show that [SYSTEM] achieves [METRIC 1: e.g., 23% faster 
time-to-mastery], [METRIC 2: e.g., ρ=0.87 grading correlation], and [METRIC 3: e.g., 89% 
path completion rate] compared to [BASELINE].

Our work demonstrates that cognitive-inspired multi-agent LLM systems can deliver 
personalized education at scale without domain-specific fine-tuning.
```

---

### 3. INTRODUCTION (1.5-2 pages)

**Structure:**
1. **Hook** (1 paragraph): Why personalized learning matters (cite Bloom's 2-Sigma)
2. **Problem** (1-2 paragraphs): Challenges in current EdTech/LLM tutors
3. **Gap** (1 paragraph): What's missing in prior work
4. **Contribution** (1 paragraph): What you bring (numbered list)
5. **Paper Outline** (optional): Brief roadmap

**Key Citations to Include:**
```bibtex
@article{bloom1984sigma,
  title={The 2 sigma problem: The search for methods of group instruction as effective as one-to-one tutoring},
  author={Bloom, Benjamin S},
  journal={Educational Researcher},
  year={1984}
}

@inproceedings{guo2024lightrag,
  title={LightRAG: Simple and Fast Retrieval-Augmented Generation},
  author={Guo, Zhen and others},
  booktitle={arXiv preprint},
  year={2024}
}

@inproceedings{yao2023tree,
  title={Tree of Thoughts: Deliberate Problem Solving with Large Language Models},
  author={Yao, Shunyu and others},
  booktitle={NeurIPS},
  year={2023}
}
```

**Contributions Template:**
```
Our contributions are:
1. A novel six-agent cognitive architecture where each agent implements a distinct SOTA mechanism 
   (LightRAG, LKT, ToT, CoT, JudgeLM, MemGPT).

2. A hybrid knowledge representation combining Course Knowledge Graphs with Personal Learning Graphs 
   stored in Neo4j with vector embeddings.

3. Empirical evaluation demonstrating [specific improvements] over [baselines] on [dataset/scenario].
```

---

### 4. RELATED WORK (1-1.5 pages)

**Subsections:**

#### 4.1 LLM-based Tutoring Systems
- GPT-4 tutors (Khan Academy, Duolingo)
- Limitations: No memory, no curriculum planning

#### 4.2 Knowledge Tracing
- BKT, DKT, SAKT
- **LKT (Lee 2024)**: Semantic understanding for cold-start

#### 4.3 Multi-Agent LLM Systems
- AutoGPT, BabyAGI, MetaGPT
- Gap: None designed for education

#### 4.4 Retrieval-Augmented Generation for Education
- RAG basics
- **LightRAG (Guo 2024)**: Dual-graph retrieval

**Gap Statement:**
> "While individual techniques (LKT, ToT, JudgeLM) have shown promise, no prior work has 
> integrated them into a coherent multi-agent architecture for personalized education."

---

### 5. METHODOLOGY (3-4 pages, CORE SECTION)

#### 5.1 System Overview

**Include Architecture Diagram:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                     AGENTIC TUTOR ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐                         │
│   │ Agent 1 │───▶│ Agent 2 │───▶│ Agent 3 │                         │
│   │ LightRAG│    │   LKT   │    │   ToT   │                         │
│   │Knowledge│    │ Profiler│    │  Path   │                         │
│   └────┬────┘    └────┬────┘    └────┬────┘                         │
│        │              │              │                               │
│        ▼              ▼              ▼                               │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐                         │
│   │ Agent 6 │◀───│ Agent 5 │◀───│ Agent 4 │                         │
│   │ MemGPT  │    │ JudgeLM │    │   CoT   │                         │
│   │  KAG    │    │Evaluator│    │  Tutor  │                         │
│   └────┬────┘    └─────────┘    └─────────┘                         │
│        │                                                             │
│        ▼                                                             │
│   ┌─────────────────────────────────────────┐                        │
│   │          Neo4j Knowledge Graph           │                       │
│   │   Course KG ←→ Personal KG ←→ System KG  │                       │
│   └─────────────────────────────────────────┘                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 5.2 Agent Specifications

For EACH agent, include:

**Template:**
```latex
\subsubsection{Agent N: [Name] ([Paper Reference])}

\textbf{Role:} [1 sentence description]

\textbf{Scientific Basis:} [Paper citation and key insight]

\textbf{Mechanism:}
[Mathematical formulation if applicable]

\textbf{Input:} $X = \{x_1, x_2, ..., x_n\}$ where $x_i$ is ...

\textbf{Output:} $Y = f(X)$ where ...

\textbf{Key Innovation:} [What we adapted/improved from the paper]
```

**Agent Formulas:**

**Agent 1 (LightRAG - Entity Resolution):**
```latex
\text{Sim}_{3way}(e_1, e_2) = w_s \cdot \text{cos}(\mathbf{v}_1, \mathbf{v}_2) 
                            + w_t \cdot J(\text{prereq}_1, \text{prereq}_2)
                            + w_c \cdot J(\text{tags}_1, \text{tags}_2)
```
Where: $w_s = 0.6, w_t = 0.3, w_c = 0.1$, $\tau = 0.8$

**Agent 2 (LKT - Mastery Prediction):**
```latex
P(\text{mastery}|h, c) = \text{LLM}\left( 
    \text{[CLS]} \oplus h \oplus \text{[SEP]} \oplus c 
\right)
```
Where $h$ is interaction history and $c$ is target concept.

**Agent 3 (Tree of Thoughts):**
```latex
\pi^*(s) = \arg\max_{a \in \mathcal{A}} \sum_{s' \in S} P(s'|s,a) \cdot V(s')
```
With beam search: $b=3$, depth $T=3$.

**Agent 4 (Chain of Thought):**
```latex
\text{Hint}_k = \text{Slice}(\text{CoT}_{consensus}, k)
```
Where $\text{CoT}_{consensus} = \text{MajorityVote}(\{\text{CoT}_1, \text{CoT}_2, \text{CoT}_3\})$

**Agent 5 (JudgeLM - G-Eval):**
```latex
\text{Score} = 0.6 \cdot \text{Correctness} + 0.2 \cdot \text{Completeness} + 0.2 \cdot \text{Clarity}
```

**Agent 6 (MemGPT - Memory Pressure):**
```latex
\text{if } \frac{|\text{Queue}|}{M_{max}} > 0.7 \text{ then AutoArchive}()
```

#### 5.3 Knowledge Graph Schema

```cypher
// Neo4j Node Types
(:CourseConcept {id, name, description, embedding, bloom_level, difficulty})
(:LearnerProfile {id, vector_10d, learning_style, mastery_map})
(:MasteryNode {learner_id, concept_id, score, timestamp})
(:ZettelNote {id, key_insight, concept_map_mermaid, tags[]})

// Relationship Types
[:PREREQUISITE_OF], [:RELATED_TO], [:PART_OF], [:MASTERED], [:NEXT]
```

#### 5.4 Inter-Agent Communication

**Event Bus Pattern:**
```
DOCUMENT_UPLOADED → Agent 1 → COURSEKG_UPDATED
LEARNER_JOINED → Agent 2 → PROFILE_CREATED
PROFILE_CREATED → Agent 3 → PATH_PLANNED
PATH_PLANNED → Agent 4 → TUTORING_STARTED
TUTOR_ASSESSMENT_READY → Agent 5 → EVALUATION_COMPLETED
EVALUATION_COMPLETED → Agent 6 → ARTIFACT_CREATED
```

---

### 6. EXPERIMENTAL SETUP (1 page)

#### 6.1 Research Questions

```
RQ1: Does the multi-agent architecture improve learning outcomes compared to single-agent baselines?
RQ2: How does each agent contribute to the overall system performance (ablation)?
RQ3: What is the latency overhead of multi-agent coordination?
```

#### 6.2 Baselines

| System | Description |
|--------|-------------|
| GPT-4 Direct | Single LLM with system prompt |
| RAG Tutor | GPT-4 + Vector retrieval |
| KT Baseline | DKT for mastery + Rule-based hints |
| Ablation Variants | Remove each agent one at a time |

#### 6.3 Datasets/Scenarios

| Dataset | Domain | Size | Source |
|---------|--------|------|--------|
| ASSISTments 2009 | Math | 100K interactions | Public |
| Coursera SQL | Databases | Manual curation | Created |
| Synthetic Learners | Various | 50 simulated profiles | Generated |

#### 6.4 Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Time to Mastery | Avg. time to reach 80% mastery | -20% vs baseline |
| Path Completion Rate | % paths fully completed | ≥ 70% |
| Grading Correlation | Spearman's ρ with human grades | ≥ 0.85 |
| Latency per Turn | P95 response time | ≤ 3 seconds |

---

### 7. RESULTS (1.5-2 pages)

#### 7.1 Main Results Table

```latex
\begin{table}[h]
\centering
\caption{Main Results on [Dataset]. Best in \textbf{bold}.}
\begin{tabular}{lcccc}
\toprule
\textbf{System} & \textbf{T2M ↓} & \textbf{Compl. ↑} & \textbf{ρ ↑} & \textbf{Lat. ↓} \\
\midrule
GPT-4 Direct    & 45 min & 42\% & 0.65 & 0.8s \\
RAG Tutor       & 38 min & 55\% & 0.72 & 1.2s \\
KT Baseline     & 35 min & 58\% & 0.78 & 0.5s \\
\textbf{Ours}   & \textbf{28 min} & \textbf{72\%} & \textbf{0.87} & 2.1s \\
\bottomrule
\end{tabular}
\end{table}
```

#### 7.2 Ablation Study

```
| Configuration | T2M (min) | Δ from Full |
|---------------|-----------|-------------|
| Full System   | 28        | —           |
| w/o Agent 3 (ToT) | 35    | +25%        |
| w/o Agent 2 (LKT) | 32    | +14%        |
| w/o Agent 6 (MemGPT) | 30 | +7%         |
```

#### 7.3 Visualizations to Include

1. **Learning Curve Chart**: Mastery over time (Ours vs Baselines)
2. **Agent Latency Breakdown**: Stacked bar chart per agent
3. **Confusion Matrix**: Error types classified by Agent 5
4. **Knowledge Graph Visualization**: Sample subgraph from Neo4j

---

### 8. DISCUSSION (0.5-1 page)

#### 8.1 Analysis of Results
- Why multi-agent outperforms single-agent
- Which agent contributes most (ablation insights)
- Latency tradeoff discussion

#### 8.2 Limitations
```
1. No large-scale user study with real students.
2. Domain-specific examples may not generalize.
3. LLM API costs at scale.
4. Synthetic learner simulation simplifies real behavior.
```

#### 8.3 Future Work
```
1. Deploy with actual students and measure learning gain.
2. Fine-tune JudgeLM on domain-specific rubrics.
3. Add speech interface for accessibility.
4. Integrate with LMS (Moodle, Canvas).
```

---

### 9. CONCLUSION (0.5 page)

**Template:**
```
We presented [SYSTEM NAME], a multi-agent LLM architecture for personalized education 
that integrates six cognitive mechanisms: [list agents and their papers].

Our experiments demonstrate [key result 1], [key result 2], and [key result 3].

This work shows that [main takeaway], paving the way for [future direction].

Code and data are available at: [REPOSITORY URL]
```

---

### 10. REFERENCES (Standard Q1 Format)

**Use BibTeX with ACM/IEEE style. Minimum 30-40 references for Q1.**

**Must-cite papers from the codebase:**
```bibtex
@article{guo2024lightrag,
  title={LightRAG: Simple and Fast Retrieval-Augmented Generation},
  author={Guo, Zhen and others},
  year={2024}
}

@inproceedings{lee2024lkt,
  title={Language Model Can Do Knowledge Tracing},
  author={Lee, et al.},
  year={2024}
}

@inproceedings{yao2023tot,
  title={Tree of Thoughts: Deliberate Problem Solving with LLMs},
  author={Yao, Shunyu and others},
  booktitle={NeurIPS},
  year={2023}
}

@inproceedings{wei2022cot,
  title={Chain-of-Thought Prompting Elicits Reasoning in LLMs},
  author={Wei, Jason and others},
  booktitle={NeurIPS},
  year={2022}
}

@inproceedings{zhu2023judgelm,
  title={JudgeLM: Fine-tuned LLMs are Scalable Judges},
  author={Zhu, Lianghui and others},
  year={2023}
}

@inproceedings{packer2023memgpt,
  title={MemGPT: Towards LLMs as Operating Systems},
  author={Packer, Charles and others},
  year={2023}
}

@article{bloom1984sigma,
  title={The 2 Sigma Problem},
  author={Bloom, Benjamin S},
  journal={Educational Researcher},
  year={1984}
}
```

---

## 📊 CHARTS & FIGURES TO GENERATE

| Figure # | Type | Description | Tool |
|----------|------|-------------|------|
| 1 | Architecture | 6-agent system overview | Mermaid/Draw.io |
| 2 | Flowchart | Processing pipeline per agent | Mermaid |
| 3 | Line Chart | Mastery curve over time | Matplotlib |
| 4 | Bar Chart | Latency breakdown by agent | Matplotlib |
| 5 | Table | Main results comparison | LaTeX |
| 6 | Table | Ablation study | LaTeX |
| 7 | Knowledge Graph | Sample Neo4j subgraph | Neo4j Browser |
| 8 | Heatmap | Confusion matrix (error types) | Seaborn |

---

## 🔧 CODE REFERENCES FOR EACH SECTION

| Section | Files to Reference |
|---------|-------------------|
| Agent 1 | `knowledge_extraction_agent.py`, `entity_resolver.py`, `AGENT_1_WHITEBOX.md` |
| Agent 2 | `profiler_agent.py`, `AGENT_2_WHITEBOX.md` |
| Agent 3 | `path_planner_agent.py`, `constants.py`, `AGENT_3_WHITEBOX.md` |
| Agent 4 | `tutor_agent.py`, `AGENT_4_WHITEBOX.md` |
| Agent 5 | `evaluator_agent.py`, `AGENT_5_WHITEBOX.md` |
| Agent 6 | `kag_agent.py`, `AGENT_6_WHITEBOX.md` |
| Constants | `backend/core/constants.py` |
| Scientific Basis | `docs/SCIENTIFIC_BASIS.md` |
| Sync Reports | `docs/verify/agent_*_sync_report.md` |

---

## ✅ Q1 SUBMISSION CHECKLIST

- [ ] Title follows venue guidelines (< 15 words)
- [ ] Abstract < 250 words with quantitative results
- [ ] All figures are vector graphics (PDF/SVG)
- [ ] All tables have proper captions
- [ ] References use consistent BibTeX style
- [ ] Supplementary materials prepared (code, data)
- [ ] Anonymized for double-blind review
- [ ] Ethical considerations addressed
- [ ] Reproducibility statement included
- [ ] Page limit respected (8-12 pages)

---

## 📝 PROMPT FOR AI PAPER WRITING

When using an AI to write sections, provide this context:

```
CONTEXT:
- System: Multi-agent LLM architecture for personalized education
- 6 Agents: LightRAG, LKT, ToT, CoT, JudgeLM, MemGPT
- Storage: Neo4j Knowledge Graph with embeddings
- Target: Q1 journal in EdTech/AI

TASK:
Write the [SECTION NAME] section following academic conventions.
Include proper LaTeX formatting for equations.
Cite relevant papers from the bibliography.
Use formal scientific language.

REFERENCES:
[Paste relevant WHITEBOX.md content here]
[Paste relevant SCIENTIFIC_BASIS.md sections here]
```
