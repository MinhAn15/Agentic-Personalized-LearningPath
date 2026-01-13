---
description: 3-Way Verification (Code ↔ Whitebox ↔ Theory) for any Agent
---

# Verify Sync Workflow

Ensures WHITEBOX documentation is synchronized with:
1. **Codebase** (actual implementation)
2. **Theory** (SCIENTIFIC_BASIS.md)
3. **Constants** (exact values match)

## Usage

```
/verify-sync Agent 1
/verify-sync Agent 2
...
```

---

## Phase 1: LOAD (3 Sources)

// turbo

For Agent N, load:

1. **Whitebox Documentation**
   ```
   view_file docs/AGENT_{N}_WHITEBOX.md
   ```

2. **Scientific Basis**
   ```
   view_file docs/SCIENTIFIC_BASIS.md
   ```
   → Focus on relevant section for Agent N

3. **Implementation Code**
   ```
   view_file backend/agents/{agent_name}_agent.py
   ```

---

## Phase 2: VERIFY CONSTANTS

Check that ALL constants match between Whitebox and Code:

| Agent | Critical Constants to Check |
|-------|----------------------------|
| 1 | `MERGE_THRESHOLD`, `TOP_K_CANDIDATES`, `W_SEMANTIC/STRUCTURAL/CONTEXTUAL` |
| 2 | `REDIS_PROFILE_TTL`, `PROFILE_VECTOR_DIM`, `λ` (interest decay) |
| 3 | `GATE_FULL_PASS_SCORE`, `MASTERY_PROCEED_THRESHOLD`, `beam_width`, `depth` |
| 4 | `W_DOC`, `W_KG`, `W_PERSONAL`, `CONFLICT_THRESHOLD`, `TUTOR_COT_TRACES` |
| 5 | `DIFFICULTY_ADJUSTMENT`, `MASTERY_BOOST`, `P_LEARN/GUESS/SLIP` |
| 6 | `max_tokens`, `max_steps`, `MASTERY_THRESHOLD`, `DIFFICULT_THRESHOLD` |

### Verification Format

```markdown
| Constant | Whitebox Value | Code Value | Status |
|----------|----------------|------------|--------|
| MERGE_THRESHOLD | 0.85 | 0.85 | ✅ MATCH |
| TOP_K_CANDIDATES | 20 | 20 | ✅ MATCH |
```

---

## Phase 3: VERIFY MECHANISM (Theory ↔ Code)

For each Agent, verify the SOTA mechanism is correctly implemented:

### Agent 1 (LightRAG - Guo 2024)
- [ ] Edge Keywords extracted and stored
- [ ] Dual-Graph adaptation documented in Section 2.6
- [ ] Entity Resolution uses cosine similarity

### Agent 2 (LKT - Lee 2024)
- [ ] `_predict_mastery_lkt()` uses LLM with history format
- [ ] Fallback to heuristics if LLM fails
- [ ] History formatted as `[CLS] CONCEPT_NAME`

### Agent 3 (ToT - Yao 2023)
- [ ] Beam Search with configurable b and d
- [ ] Thought Generator with multiple strategies
- [ ] State Evaluator for viability scoring

### Agent 4 (CoT - Wei 2022)
- [ ] Multiple reasoning traces generated
- [ ] Self-consistency voting
- [ ] Trace sliced into student-safe hints

### Agent 5 (JudgeLM - Zhu 2023)
- [ ] Reference-as-Prior format ("Assistant 1" vs "Assistant 2")
- [ ] Score notation `10.0 {score}`
- [ ] Weighted rubric (Correctness/Completeness/Clarity)

### Agent 6 (MemGPT - Packer 2023)
- [ ] WorkingMemory class with System/Core/FIFO
- [ ] Memory pressure threshold (>70%)
- [ ] Auto-archive with summarization

---

## Phase 4: VERIFY PIPELINE FLOW

Check that the processing phases in Whitebox match actual code flow:

```python
# For each method call in execute():
# 1. Find it in code
# 2. Verify it matches Whitebox description
# 3. Check input/output types
```

---

## Phase 5: GENERATE REPORT

Create verification report in:
```
docs/verify/{agent_n}_sync_report.md
```

### Report Template

```markdown
# Agent N Sync Verification Report

**Date:** {date}
**Status:** ✅ SYNCED / ⚠️ DRIFT DETECTED

## Constants Verification
| Constant | Whitebox | Code | Status |
|----------|----------|------|--------|
| ... | ... | ... | ✅/❌ |

## Mechanism Verification
| Mechanism | Paper | Implementation | Status |
|-----------|-------|----------------|--------|
| ... | ... | ... | ✅/⚠️/❌ |

## Pipeline Verification
| Phase | Whitebox | Code Method | Status |
|-------|----------|-------------|--------|
| ... | ... | ... | ✅/❌ |

## Issues Found
- [ ] Issue 1: ...
- [ ] Issue 2: ...

## Actions Required
1. ...
2. ...
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
