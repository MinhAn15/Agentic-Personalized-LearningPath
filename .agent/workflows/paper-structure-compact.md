---
description: Concise Q1 Paper Structure (~2500 words)
---

# Q1 Paper Guide

**System:** Agentic Personalized Learning Path  
**Target:** Computers & Education, IEEE TLT, AIED  
**Keywords:** LLM, Multi-Agent, Knowledge Graph, Personalized Learning

---

## STRUCTURE

### 1. TITLE
`[Method]: [Problem] via [Innovation]`  
Ex: "AgenticTutor: Personalized Learning via Six-Agent LLM Orchestration"

### 2. ABSTRACT (250w)
```
[CONTEXT] Personalized learning challenging due to cold-start, static curricula.
[GAP] LLM tutors lack memory, planning, metacognition.
[APPROACH] 6-agent architecture: LightRAG, LKT, ToT, CoT, JudgeLM, MemGPT.
[RESULTS] 23% faster mastery, ρ=0.87 grading, 72% completion.
[CONCLUSION] Multi-agent LLMs enable personalized education at scale.
```

### 3. INTRO (1.5p)
1. Hook: Bloom's 2-Sigma
2. Problem: EdTech limitations
3. Gap: No multi-agent education system
4. Contributions: 6-agent arch, hybrid KG, empirical eval

### 4. RELATED WORK (1p)
| Topic | Papers | Gap |
|-------|--------|-----|
| LLM Tutoring | Khan, Duolingo | No memory |
| Knowledge Tracing | BKT, DKT, LKT | Cold-start |
| Multi-Agent | AutoGPT | Not for edu |
| RAG | LightRAG | Single-graph |

### 5. METHODOLOGY (3p) ⭐

**Architecture:**
```
A1(LightRAG)→A2(LKT)→A3(ToT)
     ↑                    ↓
A6(MemGPT)←A5(JudgeLM)←A4(CoT)
            ↓
       Neo4j KG
```

**Agent Formulas:**
| # | Paper | Formula |
|---|-------|---------|
| 1 | LightRAG | Sim=0.6·cos+0.3·Jprereq+0.1·Jtags, τ=0.8 |
| 2 | LKT | P(m|h,c)=LLM(h⊕c) |
| 3 | ToT | beam: b=3, d=3 |
| 4 | CoT | Hint=Slice(Vote(CoT1..3),k) |
| 5 | JudgeLM | 0.6·Corr+0.2·Comp+0.2·Clar |
| 6 | MemGPT | Archive if Q/M>0.7 |

**Schema:**
```cypher
(:Concept {id,embed,bloom}), (:Profile {vec10d})
[:PREREQ], [:MASTERED], [:NEXT]
```

**Flow:**
```
DOC→A1→KG_UPDATED→A2→PROFILE→A3→PATH→A4→TUTOR→A5→EVAL→A6→ARTIFACT
```

### 6. SETUP (1p)
**RQs:** Multi vs single? Ablation? Latency?  
**Baselines:** GPT-4, RAG, KT  
**Metrics:** T2M(-20%), Compl(≥70%), ρ(≥0.85), Lat(≤3s)

### 7. RESULTS (1.5p)
| System | T2M | Compl | ρ | Lat |
|--------|-----|-------|---|-----|
| GPT-4 | 45m | 42% | .65 | 0.8s |
| RAG | 38m | 55% | .72 | 1.2s |
| **Ours** | **28m** | **72%** | **.87** | 2.1s |

**Ablation:** w/o ToT +25%, w/o LKT +14%

### 8. DISCUSSION (0.5p)
Why: Cognitive specialization  
Tradeoff: Latency vs quality  
Limits: No user study, domain-specific

### 9. CONCLUSION (0.5p)
6-agent arch (LightRAG,LKT,ToT,CoT,JudgeLM,MemGPT)  
23% faster, 72% compl, 0.87 ρ

### 10. REFS
Bloom'84, Guo'24, Lee'24, Yao'23, Wei'22, Zhu'23, Packer'23

---

## FILES
| Agent | Code | Doc |
|-------|------|-----|
| 1 | knowledge_extraction_agent.py | AGENT_1_WHITEBOX.md |
| 2 | profiler_agent.py | AGENT_2_WHITEBOX.md |
| 3 | path_planner_agent.py | AGENT_3_WHITEBOX.md |
| 4 | tutor_agent.py | AGENT_4_WHITEBOX.md |
| 5 | evaluator_agent.py | AGENT_5_WHITEBOX.md |
| 6 | kag_agent.py | AGENT_6_WHITEBOX.md |
| All | constants.py | SCIENTIFIC_BASIS.md |

## FIGURES
1. Arch diagram
2. Learning curve
3. Latency bar
4. Results table
5. Ablation table

## PROMPT
```
CONTEXT: 6-agent LLM for edu (LightRAG,LKT,ToT,CoT,JudgeLM,MemGPT)
TASK: Write [SECTION] for Q1 journal
REFS: [WHITEBOX.md] [SCIENTIFIC_BASIS.md]
FORMAT: LaTeX, formal, cite papers
```

## CHECK
- [ ] Title <15w
- [ ] Abstract <250w +numbers
- [ ] Vector figs
- [ ] 30+ refs
- [ ] Anonymized
- [ ] 8-12 pages
