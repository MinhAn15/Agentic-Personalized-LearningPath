---
description: Explore and Verify Agent 2 (Profiler / Semantic LKT).
---
# Agent 2: Profiler (The "Semantic Mapper")

This workflow guides you through understanding the **scientific basis**, **implementation**, and **verification** of Agent 2.

## 1. 🔬 Scientific Basis (Theory)
Agent 2 implements **Semantic LKT (Lee 2024)**, allowing zero-shot knowledge tracing using semantic similarities rather than just historical data.
- **Read Theory**: `docs/SCIENTIFIC_BASIS.md` (Section 3.2 Key Differences).
- **View Whitebox**: `docs/AGENT_2_WHITEBOX.md`

## 2. 🗺️ Visual Architecture
Understanding the flow from User Question -> Semantic Analysis -> Mastery Prediction.
- **View Diagram**: Open `docs/presentation/demo_dashboard.html` (Agent 2 Card).

## 3. 🧪 Live Verification
Run the test script to see the "Cold Start" prediction.

```bash
python scripts/test_agent_2_lkt.py
```

### What to Watch For:
- **[LKT]**: Logs showing "Cold Start Detected".
- **[PREDICTION]**: Logs showing "Semantic Probability" (e.g., 0.35 for hard concepts).

## 4. 🔍 Code Deep Dive
Specialize in the `update_mastery` method.
- **File**: `backend/agents/profiler_agent.py`
- **Key Method**: `_predict_mastery_lkt` (The Zero-Shot logic).
 runner should gracefully skip Graph RAG features, but check if `llama-index-graph-stores-neo4j` is installed.
