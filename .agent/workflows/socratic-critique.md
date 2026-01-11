---
description: Socratic Critique Loop for validating Agent implementation against thesis criteria.
---
# Socratic Critique Loop

This workflow implements a **Closed-Loop Feedback System** for critically validating each Agent against:
- Scientific basis (SOTA papers)
- Practical applicability (real-world use)
- Thesis criteria (academic rigor)

## Loop Structure

```
┌─────────────────────────────────────────────────────────┐
│                    CRITIQUE LOOP                        │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ 1. READ  │───►│ 2. PROBE │───►│ 3. FIX   │──┐       │
│  │ (Review) │    │ (Question)│    │ (Refine) │  │       │
│  └──────────┘    └──────────┘    └──────────┘  │       │
│       ▲                                         │       │
│       └─────────────────────────────────────────┘       │
│                    (Until PASS)                         │
└─────────────────────────────────────────────────────────┘
```

---

## Usage

Run this workflow for each agent:
```
/socratic-critique Agent 1
/socratic-critique Agent 2
...
```

---

## Phase 1: READ (Load Context)

// turbo

1. Load the Agent's Whitebox Analysis
   `view_file docs/AGENT_{N}_WHITEBOX.md`

2. Load the Scientific Basis (relevant section)
   `view_file docs/SCIENTIFIC_BASIS.md`

3. Load the Agent's core implementation
   `view_file backend/agents/{agent_name}_agent.py`

---

## Phase 2: PROBE (Socratic Questions)

Ask these critical questions for each agent. **Answer honestly as the thesis author.**

### A. Scientific Validity
1. **Paper Alignment**: Does the implementation actually match the cited paper, or is it a simplified interpretation?
2. **Key Mechanism**: What is the ONE core mechanism that makes this SOTA? Is it implemented correctly?
3. **Ablation**: If we remove this mechanism, would performance degrade? How?

### B. Practical Applicability
4. **Edge Cases**: What happens when input is malformed, empty, or adversarial?
5. **Scalability**: Would this work with 1000 users? 10,000 concepts? What breaks first?
6. **Latency**: Is the LLM call count acceptable for real-time interaction?

### C. Thesis Criteria
7. **Contribution Claim**: What specific contribution does this agent make to the thesis?
8. **Differentiation**: How is this different from a simple LLM wrapper?
9. **Evaluation**: How would you MEASURE if this agent is working correctly?

---

## Phase 3: FIX (Address Issues)

For each issue identified in Phase 2:

| Issue Type | Action |
|------------|--------|
| **Missing Feature** | Implement or document as limitation |
| **Incorrect Logic** | Fix code + update tests |
| **Documentation Gap** | Update WHITEBOX.md |
| **Over-claim** | Revise thesis claims |

---

## Phase 4: RE-PROBE (Verify Fix)

After fixes:
1. Re-read the modified files
2. Re-ask the same Socratic questions
3. Document the resolution in `docs/critique/{agent}_critique.md`

**Exit Condition**: All 9 questions have satisfactory answers.

---

## Critique Template

For each agent, create: `docs/critique/agent_{n}_critique.md`

```markdown
# Agent N Critique Log

## Session 1 (Date)

### Questions & Findings
| # | Question | Finding | Severity | Resolution |
|---|----------|---------|----------|------------|
| A1 | Paper Alignment | ... | High/Med/Low | Fixed/Deferred/N/A |
| A2 | Key Mechanism | ... | | |
| ... | ... | ... | | |

### Code Changes Made
- [ ] File: ... Line: ... Change: ...

### Documentation Updates
- [ ] WHITEBOX.md section X updated

### Status: PASS / NEEDS ITERATION
```

---

## Quick Reference: Agent Files

| Agent | Whitebox | Implementation | SOTA Paper |
|-------|----------|----------------|------------|
| 1 | `AGENT_1_WHITEBOX.md` | `knowledge_extraction_agent.py` | LightRAG (Guo 2024) |
| 2 | `AGENT_2_WHITEBOX.md` | `profiler_agent.py` | LKT (Lee 2024) |
| 3 | `AGENT_3_WHITEBOX.md` | `path_planner_agent.py` | ToT (Yao 2023) |
| 4 | `AGENT_4_WHITEBOX.md` | `tutor_agent.py` | CoT (Wei 2022) |
| 5 | `AGENT_5_WHITEBOX.md` | `evaluator_agent.py` | JudgeLM (Zhu 2023) |
| 6 | `AGENT_6_WHITEBOX.md` | `kag_agent.py` | MemGPT (Packer 2023) |
