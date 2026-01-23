# Agent 4 (Tutor) Critique Log

## Session 1 (2026-01-21)

### Context
- **Discrepancy Found**: Doc `AGENT_4_WHITEBOX.md` references `_determine_socratic_state()` method, but it does not exist in `tutor_agent.py`.
- **Options Considered**:
  - **Option A**: Update doc to reflect actual implementation (inline in `execute()`).
  - **Option B**: Refactor code to extract `_determine_socratic_state()` method.

---

### Socratic Questions & Findings

| # | Question | Finding | Severity | Resolution |
|---|----------|---------|----------|------------|
| A1 | Paper Alignment (Wei 2022 CoT) | Implementation is correct: 3 CoT traces, Self-Consistency, Leakage Guard | Low | N/A |
| A2 | Key Mechanism | State machine logic exists but embedded in `execute()`, not named method | Medium | Requires decision |
| A3 | Ablation Impact | Removing CoT would significantly degrade pedagogy quality | Low | N/A |
| C7 | Thesis Contribution | Claims "Method Ontology" + "Dynamic CoT" | High | **Named method supports claim** |
| C8 | Differentiation | Not a simple LLM wrapper due to State Machine + Harvard 7 + 3-Layer Grounding | High | **Clear structure aids defense** |
| C9 | Evaluation Metrics | Defined in Whitebox Section 5 (Engagement, Leakage, Consensus) | Low | N/A |

---

### Critical Analysis: Option A vs Option B

| Criterion | Option A (Update Doc) | Option B (Refactor Code) |
|:----------|:----------------------|:-------------------------|
| **Effort** | Low (10 min) | Low (30 min) |
| **Code Quality** | No improvement | Improved separation of concerns |
| **Thesis Defensibility** | Weaker (doc says X, code does X differently) | Stronger (doc says X, code has X) |
| **Test Impact** | None | None (tests use `DialogueState`, not `execute()` internals) |
| **Maintainability** | Status quo | Better (smaller `execute()`, testable helper) |

---

### Final Verdict: **OPTION B (Refactor Code)**

**Rationale (MIS Strategic Alignment):**

1. **Scientific Rigor**: The thesis claims a "Method Ontology" (Chandrasekaran 1999). A named method `_determine_socratic_state()` directly maps to this claim, making it traceable and defensible.

2. **Code-Documentation Alignment**: For academic work, the codebase IS the artifact. If a reviewer searches for `_determine_socratic_state`, they should find it. This is critical for reproducibility.

3. **Low Risk, High Reward**: The refactoring is trivial (extracting ~20 lines), tests won't break, and the payoff is cleaner architecture + thesis alignment.

4. **Comment in Code Already Hints at This**: Line 30 says *"UPGRADE: SocraticState removed in favor of Dynamic CoT"*. This suggests the original design HAD a separate state handler. We should restore it under the documented name.

---

### Recommended Action

1. Extract state determination logic from `execute()` (lines 144-181) into:
   ```python
   def _determine_socratic_state(self, state: DialogueState, question: str) -> DialoguePhase:
       """
       Determine the current Socratic state based on Method Ontology.
       Source: Chandrasekaran et al. (1999)
       Returns the appropriate DialoguePhase for response generation.
       """
       # ... extracted logic
   ```

2. Update `AGENT_4_WHITEBOX.md` Section 2.1 if method logic changes.

3. Run: `pytest backend/tests/test_tutor_agent.py -v` to verify no regression.

---

### Status: **DECISION MADE - Proceed with Option B**
