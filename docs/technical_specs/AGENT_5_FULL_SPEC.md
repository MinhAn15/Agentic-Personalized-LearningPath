# Agent 5: Evaluator - Full Technical Specification

**Version:** 2.1 | **Author:** Thesis Defense Documentation | **Date:** 2026-01-14

---

## 1. HIGH-LEVEL DESIGN (HLD)

### 1.1 Architectural Pattern

| Aspect | Value |
|--------|-------|
| **Pattern** | Pedagogical Judge with Multi-Factor Rubric |
| **Paradigm** | JudgeLM Reference-as-Prior Scoring |
| **Key Feature** | 5-Path Decision Engine + Weighted Mastery Update |

**Justification:**
- **JudgeLM (Zhu 2023)**: Reference-as-Prior scoring where "Golden Answer" anchors evaluation
- **5-Path Decision**: MASTERED, PROCEED, ALTERNATE, REMEDIATE, RETRY based on score + error type
- **Hybrid BKT-LLM**: Combines traditional Knowledge Tracing with LLM-based mastery prediction

### 1.2 Data Flow

```mermaid
graph LR
    subgraph Input
        A[Learner Response<br/>+ Expected Answer]
    end
    
    subgraph Phase1["Phase 1: Context"]
        B[Load Concept Metadata<br/>+ Learner Profile]
    end
    
    subgraph Phase2["Phase 2: JudgeLM"]
        C[Reference-as-Prior<br/>Scoring (0-1)]
    end
    
    subgraph Phase3["Phase 3: Error Class"]
        D[CONCEPTUAL<br/>PROCEDURAL<br/>INCOMPLETE<br/>CARELESS]
    end
    
    subgraph Phase4["Phase 4: Misconception"]
        E[Match to Known<br/>Misconceptions in KG]
    end
    
    subgraph Phase5["Phase 5: Feedback"]
        F[Personalized<br/>Feedback Gen]
    end
    
    subgraph Phase6["Phase 6: Decision"]
        G[5-Path Decision<br/>Engine]
    end
    
    subgraph Phase7["Phase 7: Mastery"]
        H[Weighted Moving<br/>Average Update]
    end
    
    subgraph Phase8["Phase 8: Output"]
        I[EVALUATION_COMPLETED<br/>Event]
    end
    
    A --> B --> C --> D --> E --> F --> G --> H --> I
```

### 1.3 Integration Points

| System | Protocol | Purpose | Connection Pool |
|--------|----------|---------|-----------------|
| **Neo4j** | Bolt | Concept KG + Personal KG | 50 connections |
| **Redis** | TCP | Concept metadata cache (TTL: 1h) | 10 connections |
| **Gemini API** | REST | JudgeLM scoring, Feedback generation | Rate-limited |
| **Event Bus** | Internal | EVALUATION_COMPLETED event to Agent 3 | N/A |

### 1.4 JudgeLM Adaptation (Thesis Deviation)

> ⚠️ **Transparency Note**: This implementation adapts JudgeLM, not full replication.

| JudgeLM Original (Zhu 2023) | Thesis Implementation | Justification |
|-----------------------------|----------------------|---------------|
| Fine-tuned 7B model | **Zero-shot Gemini** | No training data |
| Generic comparison | **Educational rubric (3 criteria)** | Domain-specific |
| Single score | **Score + Error Classification + Feedback** | Richer output |

**Fine-tuned educational JudgeLM is documented as Future Work.**

---

## 2. TECHNICAL DECOMPOSITION

### 2.1 Sub-Modules

| Method | Responsibility | Lines | Coupling |
|--------|---------------|-------|----------|
| `execute()` | Main orchestration (8 phases) | 147-390 | High |
| `_score_response()` | JudgeLM scoring | 392-487 | High (Core) |
| `_classify_error()` | Error type classification | 489-530 | Medium |
| `_detect_misconception()` | Match to known misconceptions | 532-569 | Medium |
| `_generate_feedback()` | Personalized feedback | 571-613 | Low |
| `_make_path_decision()` | 5-Path Decision Engine | 631-691 | High (Core) |
| `_update_learner_mastery()` | Weighted Moving Average | 693-766 | Medium |
| `_predict_mastery_lkt()` | LKT-based mastery prediction | 784-826 | Medium |

### 2.2 SOLID Rationale

| Principle | Implementation |
|-----------|----------------|
| **S**ingle Responsibility | `_score_response()` only scores, `_classify_error()` only classifies |
| **O**pen/Closed | `ErrorType` and `PathDecision` enums extensible |
| **L**iskov Substitution | Inherits from `BaseAgent` interface |
| **I**nterface Segregation | Separate event handler for TUTOR_ASSESSMENT_READY |
| **D**ependency Inversion | LLM, Neo4j, Event Bus injected via constructor |

### 2.3 Dependency Map

| Dependency | Version | Purpose |
|------------|---------|---------|
| `neo4j` | 5.x | Concept KG + Personal KG queries |
| `redis` | 4.x | Concept metadata cache |
| `google-generativeai` | 0.4.x | JudgeLM scoring, Feedback |
| `llama-index` | 0.10.x | LLM wrapper |

---

## 3. LOW-LEVEL DESIGN (LLD) & WHITEBOX

### 3.1 Internal State Management

| Aspect | Implementation |
|--------|----------------|
| **Concept Cache** | Redis `concept:{concept_id}` (TTL: 1 hour) |
| **Mastery Update** | Weighted Moving Average to Personal KG |
| **Alert Threshold** | `THRESHOLD_ALERT = 0.4` (Critical Failure) |
| **Scoring Weights** | Correctness (0.6), Completeness (0.2), Clarity (0.2) |

### 3.2 Algorithm (Pseudocode)

```python
async def execute(self, learner_id: str, concept_id: str, 
                  learner_response: str, expected_answer: str, **kwargs):
    # Phase 1: Context Gathering
    concept = await self._get_concept_metadata(concept_id)  # Cached
    learner = await self._get_learner_profile(learner_id)
    
    # Phase 2: JudgeLM Scoring (Reference-as-Prior)
    score, cot_reasoning = await self._score_response(
        learner_response, expected_answer, concept.explanation,
        target_bloom_level=concept.bloom_level
    )
    # Prompt: "Assistant 1 (Golden) vs Assistant 2 (Student)"
    # Rubric: Correctness 60%, Completeness 20%, Clarity 20%
    
    # Phase 3: Error Classification (if score < 0.8)
    if score < 0.8:
        error_type = await self._classify_error(
            learner_response, expected_answer, concept
        )
    else:
        error_type = ErrorType.CORRECT
    
    # Phase 4: Misconception Detection
    misconception = await self._detect_misconception(
        learner_response, concept, error_type
    )
    
    # Phase 5: Feedback Generation
    feedback = await self._generate_feedback(
        learner_response, expected_answer, error_type, 
        misconception, concept.explanation
    )
    
    # Phase 6: 5-Path Decision Engine
    decision = self._make_path_decision(
        score, learner.current_mastery, error_type, concept.difficulty
    )
    
    # Phase 7: Mastery Update (Weighted Moving Average)
    new_mastery = await self._update_learner_mastery(
        learner_id, concept_id, score, 
        current_mastery=learner.current_mastery,
        concept_difficulty=concept.difficulty,
        error_type=error_type
    )
    # New = (Current * 0.4) + (Score * 0.6)
    
    # Phase 8: Alert + Event Emit
    if score < THRESHOLD_ALERT:
        await self._alert_instructor(learner_id, concept_id, score)
    
    await self.event_bus.emit("EVALUATION_COMPLETED", {
        "learner_id": learner_id,
        "concept_id": concept_id,
        "score": score,
        "decision": decision.value,
        "new_mastery": new_mastery
    })
    
    return EvaluationResult(
        score=score,
        error_type=error_type,
        decision=decision,
        feedback=feedback,
        new_mastery=new_mastery
    )
```

### 3.3 Data Schemas

**Input Schema:**
```json
{
  "learner_id": "uuid",
  "concept_id": "string",
  "learner_response": "string (student's answer)",
  "expected_answer": "string (golden answer)",
  "correct_answer_explanation": "string (why it's correct)"
}
```

**Output Schema:**
```json
{
  "score": 0.75,
  "error_type": "INCOMPLETE",
  "decision": "ALTERNATE",
  "feedback": "Good start! Consider also mentioning...",
  "new_mastery": 0.68,
  "cot_reasoning": "Student understood X but missed Y..."
}
```

**5-Path Decision Mapping:**
```json
{
  "MASTERED": "score >= 0.9 (adjusted by difficulty)",
  "PROCEED": "score >= 0.8",
  "ALTERNATE": "score >= 0.6",
  "REMEDIATE": "score < 0.6 AND error_type == CONCEPTUAL",
  "RETRY": "score < 0.6 AND error_type != CONCEPTUAL"
}
```

### 3.4 Guardrails & Validation

| Check | Implementation | Fail-Safe |
|-------|---------------|-----------|
| Empty response | `len(learner_response) == 0` | Score 0.0 |
| LLM scoring fail | JSON parse error | Keyword overlap fallback |
| Invalid score | `score < 0 or score > 1` | Clamp to [0, 1] |
| Concept not found | KG query empty | Use default difficulty |
| Alert threshold | `score < 0.4` | Notify instructor |

### 3.5 Error Handling Matrix

| Error | Detection | Recovery | Log Level |
|-------|-----------|----------|-----------|
| JudgeLM timeout | `asyncio.TimeoutError` | Keyword overlap fallback | WARN |
| LLM empty response | `len(response) == 0` | Score 0.0 + log | WARN |
| JSON parse error | `JSONDecodeError` | Regex fallback for `10.0 X` | WARN |
| Event emit fail | Exception caught | Swallow, don't crash | ERROR |
| KG disconnect | `ServiceUnavailable` | Use cached concept | ERROR |

### 3.6 Testing Strategy

| Test Type | Coverage | File |
|-----------|----------|------|
| Unit | `_score_response()`, `_make_path_decision()` | `test_evaluator_agent.py` |
| JudgeLM | Prompt structure, `10.0 X` parsing | `test_agent_5_judgelm.py` |
| Decision | All 5 paths with edge cases | `test_path_decision.py` |
| Integration | Full `execute()` with events | `test_evaluator_integration.py` |

---

## 4. COMPLEXITY ANALYSIS

### 4.1 Time Complexity

| Phase | Complexity | Bottleneck |
|-------|------------|------------|
| Context Gathering | O(1) | Redis cache / Neo4j indexed |
| JudgeLM Scoring | O(1) | 1 LLM call |
| Error Classification | O(1) | Rule-based |
| Feedback Generation | O(1) | 1 LLM call |
| Decision + Mastery | O(1) | Simple computation |

### 4.2 Latency Analysis

| Operation | LLM Calls | Est. Time |
|-----------|-----------|-----------|
| **JudgeLM Scoring** | 1 | ~500ms |
| **Error Classification** | 0 (rule-based) | ~10ms |
| **Feedback Generation** | 1 | ~500ms |
| **Mastery Update** | 0 | ~50ms |
| **Total** | **2** | **~1s** |

### 4.3 Resource Usage

| Resource | Usage | Limit |
|----------|-------|-------|
| Memory | ~15MB per evaluation | Minimal state |
| Tokens | ~1.5K per LLM call | 3K total |
| Redis cache | ~1KB per concept | 1 hour TTL |
| Neo4j connections | 1-2 per request | Pool: 50 |

### 4.4 Scalability Analysis

| Scale | Evaluations/min | Status |
|-------|-----------------|--------|
| Small | < 100 | ✅ Fast |
| Medium | 100-1K | ✅ Acceptable |
| Large | 1K-10K | ⚠️ LLM rate limits |
| Enterprise | > 10K | ❌ Needs batch scoring |

---

## 5. AI ENGINEER ARTIFACTS

### 5.1 Model Configuration

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Model | `gemini-1.5-flash` | Cost/speed for scoring |
| Temperature | **0.2** | Consistent grading |
| Top_P | 0.95 | Focused output |
| Max Tokens | 1024 | Sufficient for rubric |

### 5.2 System Prompts

**JudgeLM Scoring (Reference-as-Prior):**
```
You are a fair and accurate educational grader.

REFERENCE ANSWER (Golden):
{expected_answer}

EXPLANATION:
{explanation}

STUDENT ANSWER:
{learner_response}

GRADING RUBRIC:
1. Correctness (60%): Is the answer factually correct?
2. Completeness (20%): Does it cover all key points?
3. Clarity (20%): Is it well-expressed?

BLOOM LEVEL TARGET: {bloom_level}

OUTPUT FORMAT:
10.0 [SCORE] where SCORE is 0.0 to 1.0
{"correctness": X, "completeness": Y, "clarity": Z, "reasoning": "..."}
```

**Error Classification:**
```
Classify the error type in this student response:

Student Answer: {learner_response}
Expected Answer: {expected_answer}

Error Types:
- CONCEPTUAL: Fundamental misunderstanding
- PROCEDURAL: Wrong method, right idea
- INCOMPLETE: Missing key information
- CARELESS: Minor mistake, understands concept

Return JSON: {"error_type": "...", "explanation": "..."}
```

### 5.3 Prompt Engineering Techniques

| Technique | Used? | Example |
|-----------|-------|---------|
| Role-Play Persona | ✅ | "You are a fair and accurate grader" |
| Reference-as-Prior | ✅ | Golden answer provided first |
| Multi-Criteria Rubric | ✅ | Correctness 60%, Completeness 20%, Clarity 20% |
| Score Notation | ✅ | "10.0 [SCORE]" format |
| JSON + Reasoning | ✅ | Structured output with CoT |

### 5.4 Prompt → Theory Mapping

| Prompt Section | Technique | Paper/Source |
|----------------|-----------|--------------|
| Reference-as-Prior | JudgeLM | Zhu et al. (2023) |
| "10.0 [SCORE]" notation | JudgeLM token format | Zhu et al. (2023) |
| Multi-criteria rubric | G-Eval | Liu et al. (2023) |
| Bloom level target | Educational alignment | Bloom's Taxonomy |
| Error taxonomy | Pedagogical classification | Educational research |

---

## 6. EVALUATION METHODOLOGY

### 6.1 Metrics vs Baseline

| Metric | Our Target | Exact Match | Keyword Overlap | Semantic Sim | Expected |
|--------|------------|-------------|-----------------|--------------|----------|
| Human Correlation (ρ) | ≥ 0.85 | ~0.4 | ~0.55 | ~0.7 | **+21%** |
| Scoring Consistency | ≤ 0.05 std | N/A | N/A | ~0.1 | **-50%** |
| Error Classification | ≥ 80% | N/A | N/A | N/A | Unique |
| Misconception Detection | ≥ 75% | N/A | N/A | N/A | Unique |

**Baseline Definition**:
- Exact Match: Binary correct/incorrect
- Keyword Overlap: Count matching keywords
- Semantic Similarity: Embedding cosine similarity

### 6.2 JudgeLM-Specific Metrics

| Metric | Definition | Target (per Zhu 2023) |
|--------|------------|----------------------|
| Position Bias | Score diff when swapping order | ≤ 0.1 |
| Length Bias | Correlation with response length | ρ ≤ 0.2 |
| Reference Anchoring | Impact of golden answer quality | High |

### 6.3 BKT Parameter Validation

| Parameter | Implementation | BKT Literature | Status |
|-----------|----------------|----------------|--------|
| P_LEARN | 0.1 | 0.05-0.15 | ✅ Valid |
| P_GUESS | 0.25 | 0.2-0.3 | ✅ Valid |
| P_SLIP | 0.10 | 0.05-0.15 | ✅ Valid |

### 6.4 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No real human grader study | Cannot verify correlation | Synthetic ground truth |
| Domain-specific rubrics | May not generalize | Configurable weights |
| LLM variance | Different scores each run | Run 3x, use median |

### 6.5 Ablation Study (Future Work)

| Variant | Expected Impact | Status |
|---------|-----------------|--------|
| **Without JudgeLM** | Lower human correlation (~0.6) | 📋 Not yet tested |
| **Without Multi-Criteria** | Less nuanced feedback | 📋 Not yet tested |
| **Without Reference-as-Prior** | Higher position bias | 📋 Not yet tested |

---

## 7. THESIS CONTRIBUTION

This section explicitly states the novel contributions of Agent 5 to differentiate from prior work.

### 7.1 Novel Elements

| Contribution | Novel Element | Prior Work | Evidence |
|--------------|---------------|------------|----------|
| **JudgeLM for Education** | Apply JudgeLM to student grading | JudgeLM for LLM comparison | Section 5.2 prompts |
| **5-Path Decision Engine** | MASTERED/PROCEED/ALTERNATE/REMEDIATE/RETRY | Binary pass/fail | Section 3.2 algorithm |
| **Error Taxonomy** | 4-type classification with misconception linking | Generic error labels | Section 3.3 schema |
| **Hybrid BKT-LLM Mastery** | Weighted average with LKT prediction | Separate BKT or LLM | Section 2.1 methods |

### 7.2 Summary

| Aspect | Description |
|--------|-------------|
| **Role** | "Pedagogical Judge" - scores, classifies errors, decides next step |
| **Scientific Basis** | JudgeLM (Zhu 2023), G-Eval (Liu 2023), BKT, LKT |
| **Key Innovation** | JudgeLM + 5-Path Decision + Error Taxonomy + Hybrid Mastery |
| **Resilience** | Keyword overlap fallback, swallow event errors, cached concepts |
| **Performance** | ~1s per evaluation (2 LLM calls) |
| **Scalability** | Optimized for Medium Scale (1K evaluations/min) |
