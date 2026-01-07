---
description: Test Agent 5 (Evaluator Agent) functionality
---
description: Explore and Verify Agent 5 (Evaluator / JudgeLM).
---
# Agent 5: Evaluator (The "AI Judge")

This workflow guides you through understanding the **scientific basis**, **implementation**, and **verification** of Agent 5.

## 1. 🔬 Scientific Basis (Theory)
Agent 5 implements **JudgeLM (Zhu 2023)**, using a "Gold Reference" and "Rubric" to evaluate student answers with high correlation to human grading, mitigating LLM bias.
- **Read Theory**: `docs/SCIENTIFIC_BASIS.md` (Section 3.5).
- **View Whitebox**: `docs/AGENT_5_WHITEBOX.md`

## 2. 🗺️ Visual Architecture
Understanding the flow from Student Answer + Reference -> G-Eval Criteria -> Final Score.
- **View Diagram**: Open `docs/presentation/demo_dashboard.html` (Agent 5 Card).

## 3. 🧪 Live Verification
Run the test script to see the "Justification Trace" and Score.

```bash
python scripts/test_agent_5_judgelm.py
```

### What to Watch For:
- **"justification_trace"**: Detailed reasoning (e.g., "Student successfully mentioned X but failed to explain Y").
- **"score"**: A float value (0.0 - 1.0) aligning with the justification.

## 4. 🔍 Code Deep Dive
Specialize in the `evaluate` method.
- **File**: `backend/agents/evaluator_agent.py`
- **Key Method**: `_score_judgelm` (The Evaluation logic).
