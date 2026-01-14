# Agent 3: Path Planner - Full Technical Specification

**Version:** 2.1 | **Author:** Thesis Defense Documentation | **Date:** 2026-01-14

---

## 1. HIGH-LEVEL DESIGN (HLD)

### 1.1 Architectural Pattern

| Aspect | Value |
|--------|-------|
| **Pattern** | Hybrid Decision Engine (ToT + LinUCB) |
| **Paradigm** | Deliberate Reasoning (System 2) + Adaptive RL |
| **Key Feature** | Strategic Lookahead + Real-time Re-planning |

**Justification:**
- **Tree of Thoughts (Yao 2023)**: Deep reasoning for initial curriculum planning with beam search
- **LinUCB (Li 2010)**: Contextual bandit for fast, incremental re-planning
- **Adaptive Chaining**: 5 modes (FORWARD, BACKWARD, ACCELERATE, LATERAL, REVIEW)

### 1.2 Data Flow

```mermaid
graph LR
    subgraph Input
        A[Learner Profile<br/>+ Goal + Last Result]
    end
    
    subgraph Phase1["Phase 1: Context Loading"]
        B[Load Profile Vector<br/>from Agent 2]
    end
    
    subgraph Phase2["Phase 2: Smart Filter"]
        C[Personal Subgraph<br/>Expansion O(1)]
    end
    
    subgraph Phase3["Phase 3: Mastery Gate"]
        D{Probabilistic<br/>Gate Check}
    end
    
    subgraph Phase4["Phase 4: Algorithm Selection"]
        E{First time?}
        F[ToT Beam Search<br/>b=3, d=3]
        G[LinUCB Selection]
    end
    
    subgraph Phase5["Phase 5: Adaptive Chain"]
        H[Select Mode<br/>FORWARD/BACKWARD/...]
    end
    
    subgraph Phase6["Phase 6: Output"]
        I[Learning Path JSON]
    end
    
    A --> B --> C --> D --> E
    E -->|Yes| F --> H
    E -->|No| G --> H
    H --> I
```

### 1.3 Integration Points

| System | Protocol | Purpose | Connection Pool |
|--------|----------|---------|-----------------|
| **Neo4j** | Bolt | Knowledge Graph traversal | 50 connections |
| **Redis** | TCP | LinUCB state persistence | 10 connections |
| **Gemini API** | REST | ToT reasoning (Thought Generator, State Evaluator) | Rate-limited |
| **Agent 2** | Internal | Learner Profile (10-dim vector) | N/A |

### 1.4 ToT Adaptation (Thesis Deviation)

> ⚠️ **Transparency Note**: This implementation adapts ToT, not full replication.

| ToT Original (Yao 2023) | Thesis Implementation | Justification |
|-------------------------|----------------------|---------------|
| BFS/DFS game tree | **Beam Search (b=3, d=3)** | Bounded complexity |
| Generic tasks (Game of 24) | **Curriculum planning domain** | Education-specific |
| Single-shot | **Hybrid with LinUCB fallback** | Real-time requirement |

**Full ToT with deeper search is documented as Future Work.**

---

## 2. TECHNICAL DECOMPOSITION

### 2.1 Sub-Modules

| Method | Responsibility | Lines | Coupling |
|--------|---------------|-------|----------|
| `execute()` | Main orchestration | 443-626 | High |
| `_beam_search()` | ToT beam search (b=3, d=3) | 170-223 | High (Core) |
| `_thought_generator()` | Propose 3 next concepts | 270-306 | Medium |
| `_evaluate_path_viability()` | State evaluator (mental simulation) | 225-268 | Medium |
| `_select_chain_mode()` | Adaptive chaining logic | 699-723 | Low |
| `_generate_adaptive_path()` | Path generation per mode | 725-899 | High |
| `_on_evaluation_feedback()` | LinUCB reward update | 324-440 | Medium |

### 2.2 SOLID Rationale

| Principle | Implementation |
|-----------|----------------|
| **S**ingle Responsibility | `_thought_generator()` only proposes, `_evaluate_path_viability()` only evaluates |
| **O**pen/Closed | `ChainingMode` enum extensible |
| **L**iskov Substitution | Inherits from `BaseAgent` interface |
| **I**nterface Segregation | Separate methods for ToT vs LinUCB |
| **D**ependency Inversion | LLM, Neo4j, Redis injected via constructor |

### 2.3 Dependency Map

| Dependency | Version | Purpose |
|------------|---------|---------|
| `neo4j` | 5.x | Graph traversal, concept lookup |
| `redis` | 4.x | LinUCB state (A, b matrices) |
| `google-generativeai` | 0.4.x | ToT reasoning |
| `numpy` | 1.24.x | Matrix operations for LinUCB |

---

## 3. LOW-LEVEL DESIGN (LLD) & WHITEBOX

### 3.1 Internal State Management

| Aspect | Implementation |
|--------|----------------|
| **LinUCB State** | Redis `linucb:{concept_id}` with `A` (10x10), `b` (10x1) |
| **State TTL** | 7 days |
| **Concurrency** | Redis lock `lock:concept:{concept_id}` for atomic updates |
| **MAB Stats** | In-memory cache synced with Redis |

### 3.2 Algorithm (Pseudocode)

```python
async def execute(self, learner_id: str, goal: str, last_result: str, **kwargs):
    # Phase 1: Context Loading
    profile = await self._load_profile(learner_id)  # 10-dim vector from Agent 2
    concepts = await self._query_neo4j(learner_id)  # Personal subgraph
    
    # Phase 2: Smart Filtering (O(1) via subgraph expansion)
    candidates = self._expand_from_mastery_nodes(profile.mastered_concepts)
    
    # Phase 3: Probabilistic Mastery Gate
    gate_prob = min(1.0, profile.current_score / GATE_FULL_PASS_SCORE)
    if random.random() > gate_prob:
        chain_mode = ChainingMode.BACKWARD  # Force remediation
    else:
        chain_mode = self._select_chain_mode(last_result)
    
    # Phase 4: Algorithm Selection (ToT vs LinUCB)
    if profile.is_first_planning:
        # ToT: Beam Search with b=3, d=3
        path_ids = await self._beam_search(learner_id, candidates)
        # 18 LLM calls: 9 generator + 9 evaluator
    else:
        # LinUCB: Fast contextual bandit selection
        next_concept = self.rl_engine.select(
            profile.context_vector, candidates, strategy=BanditStrategy.UCB
        )
        path_ids = [next_concept]  # 0 LLM calls
    
    # Phase 5: Apply Adaptive Chaining
    path = self._generate_adaptive_path(profile, concepts, chain_mode)
    
    # Phase 6: Output Generation
    return LearningPath(
        concepts=path,
        chaining_mode=chain_mode,
        success_probability=self._calculate_success_prob(path, profile)
    )
```

### 3.3 Data Schemas

**Input Schema:**
```json
{
  "learner_id": "uuid",
  "goal": "string (e.g., 'Master SQL Joins')",
  "last_result": "PROCEED | MASTERED | REMEDIATE | ALTERNATE | RETRY | null"
}
```

**Output Schema:**
```json
{
  "path": [
    {"concept_code": "sql.inner_join", "estimated_time": 30, "difficulty": 3},
    {"concept_code": "sql.left_join", "estimated_time": 25, "difficulty": 3}
  ],
  "chaining_mode": "FORWARD",
  "success_probability": 0.85,
  "reasoning": "Based on mastery of SELECT, recommending JOIN progression"
}
```

**LinUCB State Schema (Redis):**
```json
{
  "A": "10x10 matrix (JSON array)",
  "b": "10x1 vector (JSON array)",
  "count": 42,
  "last_updated": "2026-01-14T12:00:00Z"
}
```

### 3.4 Guardrails & Validation

| Check | Implementation | Fail-Safe |
|-------|---------------|-----------|
| Prerequisite violation | Graph constraint check | Block concept |
| Empty candidates | `len(candidates) == 0` | Return REVIEW mode |
| LinUCB matrix invalid | `np.linalg.LinAlgError` | Reset to identity |
| ToT timeout | `asyncio.timeout(30)` | Fallback to LinUCB |
| Probabilistic gate | `random() > gate_prob` | Force BACKWARD |

### 3.5 Error Handling Matrix

| Error | Detection | Recovery | Log Level |
|-------|-----------|----------|-----------|
| ToT timeout | `asyncio.TimeoutError` | Fallback to LinUCB | WARN |
| LinUCB state corrupt | Invalid JSON | Reset to identity matrix | ERROR |
| No valid candidates | Empty after filter | Switch to REVIEW mode | INFO |
| Redis lock timeout | 5s timeout | Retry 3x with backoff | ERROR |
| Graph query fail | `ServiceUnavailable` | Use cached path | ERROR |

### 3.6 Testing Strategy

| Test Type | Coverage | File |
|-----------|----------|------|
| Unit | `_beam_search()`, `_thought_generator()` | `test_path_planner.py` |
| Integration | Full `execute()` with mocked Neo4j | `test_path_planner_integration.py` |
| Deterministic | Probabilistic Gate with seeded random | `test_agent_3.py` |

---

## 4. COMPLEXITY ANALYSIS

### 4.1 Time Complexity

| Phase | Complexity | Bottleneck |
|-------|------------|------------|
| Context Load | O(1) | Redis lookup |
| Smart Filter | O(1) | Personal subgraph expansion |
| ToT Beam Search | O(b × d) | b=3 beams, d=3 depth |
| LinUCB Selection | O(k) | k = candidates |
| Adaptive Chain | O(1) | Mode selection |

### 4.2 Latency Analysis

| Scenario | LLM Calls | Est. Time |
|----------|-----------|-----------|
| **First time (ToT Full)** | 18 | ~9 seconds |
| **First time (ToT Shallow d=2)** | 12 | ~6 seconds |
| **Re-plan (LinUCB)** | 0 | ~100ms |
| **Cached path** | 0 | ~50ms |

**LLM Call Breakdown (ToT):**
| Component | Calls per Beam | Total (b=3, d=3) |
|-----------|----------------|------------------|
| Thought Generator | 1 per node | 9 calls |
| State Evaluator | 1 per candidate | 9 calls |
| **Total** | | **18 calls** |

### 4.3 Resource Usage

| Resource | Usage | Limit |
|----------|-------|-------|
| Memory | ~30MB (LinUCB matrices) | Per learner |
| Tokens | ~1K per LLM call | 18K for full ToT |
| Redis storage | ~1KB per concept | LinUCB state |
| Neo4j connections | 1 per request | Pool: 50 |

### 4.4 Scalability Analysis

| Scale | # Concepts | ToT Latency | LinUCB Latency | Status |
|-------|------------|-------------|----------------|--------|
| Small | < 100 | 9s | 100ms | ✅ Fast |
| Medium | 100-1K | 9s | 150ms | ✅ Acceptable |
| Large | 1K-10K | 9s | 200ms | ⚠️ LinUCB memory |
| Enterprise | > 10K | 9s | 300ms | ❌ Needs sharding |

**Note:** ToT latency is constant regardless of concept count (beam search bounded).

---

## 5. AI ENGINEER ARTIFACTS

### 5.1 Model Configuration

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Model | `gemini-1.5-flash` | Cost/speed for ToT |
| Temperature | **0.7** | Creative for thought generation |
| Top_P | 0.95 | Diverse candidates |
| Max Tokens | 2048 | Path reasoning |

### 5.2 System Prompts

**Thought Generator (ToT):**
```
You are a curriculum designer for personalized learning.
Current concept: {current_concept}
Target goal: {target_concept}
Learner mastery: {mastery_state}

Generate 3 DISTINCT next learning concepts. Each should be:
1. Reachable from current concept
2. Progressing toward target
3. Matched to learner's skill level

Return JSON: {"thoughts": [{"concept_id": "...", "strategy": "REVIEW|SCAFFOLD|CHALLENGE", "rationale": "..."}]}
```

**State Evaluator (ToT):**
```
Evaluate this learning path for a student:
Path: {path_sequence}
Learner profile: {profile_vector}

Predict:
1. Success probability (0.0-1.0)
2. Time to completion (minutes)
3. Cognitive load (1-5)

Use "mental simulation" - imagine the learner progressing through each step.

Return JSON: {"viability": 0.X, "estimated_time": N, "cognitive_load": M, "reasoning": "..."}
```

### 5.3 Prompt Engineering Techniques

| Technique | Used? | Example |
|-----------|-------|---------|
| Role-Play Persona | ✅ | "You are a curriculum designer" |
| Mental Simulation | ✅ | "imagine the learner progressing" |
| Output Format Constraint | ✅ | "Return JSON: {...}" |
| Strategy Taxonomy | ✅ | "REVIEW, SCAFFOLD, CHALLENGE" |
| Chain-of-Thought | ✅ | Multi-step path reasoning |

### 5.4 Prompt → Theory Mapping

| Prompt Section | Technique | Paper/Source |
|----------------|-----------|--------------|
| "3 DISTINCT next concepts" | Thought Decomposition | ToT (Yao 2023) |
| "mental simulation" | State Evaluation | ToT (Yao 2023) |
| "viability" score | Pruning Heuristic | ToT (Yao 2023) |
| LinUCB selection | Contextual Bandit | Li et al. (2010) |
| REVIEW, SCAFFOLD, CHALLENGE | Pedagogical scaffolding | Vygotsky ZPD |

---

## 6. EVALUATION METHODOLOGY

### 6.1 Metrics vs Baseline

| Metric | Our Target | Random Path | Greedy Path | Rule-based | Expected Improvement |
|--------|------------|-------------|-------------|------------|----------------------|
| Completion Rate | ≥ 70% | ~40% | ~55% | ~60% | **+75%** vs random |
| Time to Mastery | -20% | Baseline | -5% | -10% | **-20%** vs baseline |
| Prerequisite Violations | 0 | Many | Some | 0 | Hard constraint |
| Backtrack Rate | ≤ 30% | ~50% | ~40% | ~35% | **-40%** vs random |

**Baseline Definition**:
- Random: Select next concept randomly
- Greedy: Always highest mastery neighbor
- Rule-based: Fixed prerequisite ordering

### 6.2 ToT-Specific Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| Beam Diversity | Unique concepts across beams | ≥ 2 |
| Pruning Effectiveness | Low-value paths correctly pruned | ≥ 80% |
| Strategic Value Accuracy | Correlation predicted vs actual | ρ ≥ 0.6 |

### 6.3 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| ToT expensive | ~9s latency | LinUCB hybrid mode |
| No user study | Cannot validate engagement | Synthetic simulation |
| LLM variance | Different paths per run | Run 3x, report variance |

### 6.4 Ablation Study (Future Work)

| Variant | Expected Impact | Status |
|---------|-----------------|--------|
| **Without ToT** | Higher backtrack rate | 📋 Not yet tested |
| **Without LinUCB** | Higher latency for re-planning | 📋 Not yet tested |
| **Without Mastery Gate** | More lucky-guess problems | 📋 Not yet tested |

---

## 7. THESIS CONTRIBUTION

This section explicitly states the novel contributions of Agent 3 to differentiate from prior work.

### 7.1 Novel Elements

| Contribution | Novel Element | Prior Work | Evidence |
|--------------|---------------|------------|----------|
| **ToT for Curriculum** | Apply ToT to education domain | ToT for puzzles/games | Section 5.2 prompts |
| **ToT + LinUCB Hybrid** | Strategic reasoning + fast RL | Separate approaches | Section 1.2 data flow |
| **Probabilistic Mastery Gate** | Prevent lucky-guess progression | Binary pass/fail | Section 3.2 algorithm |
| **5-Mode Adaptive Chaining** | FORWARD/BACKWARD/ACCELERATE/LATERAL/REVIEW | Fixed sequencing | Section 2.2.2 (whitebox) |

### 7.2 Summary

| Aspect | Description |
|--------|-------------|
| **Role** | "Navigator" - generates optimal learning sequence |
| **Scientific Basis** | ToT (Yao 2023), LinUCB (Li 2010), Spaced Repetition |
| **Key Innovation** | ToT + LinUCB Hybrid + Probabilistic Gate |
| **Resilience** | Fallback to LinUCB, Redis lock, cached paths |
| **Performance** | ~9s first time (ToT), ~100ms re-plan (LinUCB) |
| **Scalability** | Optimized for Medium Scale (1K concepts) |
