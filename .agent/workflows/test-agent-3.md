---
description: Explore and Verify Agent 3 (Path Planner / Tree of Thoughts).
---
# Agent 3: Path Planner (The "Strategist")

This workflow guides you through understanding the **scientific basis**, **implementation**, and **verification** of Agent 3.

## 1. 🔬 Scientific Basis (Theory)
Agent 3 implements **Tree of Thoughts (ToT) (Yao 2023)**, using lookahead search (BFS) to simulate future user states before choosing the best educational path.
- **Read Theory**: `docs/SCIENTIFIC_BASIS.md` (Section 3.3).
- **View Whitebox**: `docs/AGENT_3_WHITEBOX.md`

## 2. 🗺️ Visual Architecture
Understanding the flow from Current State -> Candidate Generation -> Lookahead Evaluation -> Selection.
- **View Diagram**: Open `docs/presentation/demo_dashboard.html` (Agent 3 Card).

## 3. 🧪 Live Verification
Run the test script to see the agent choose the "Strategic" path over the "Easy" one.

```bash
python scripts/test_agent_3_tot.py
```

### What to Watch For:
- **[ToT]**: Logs showing "Expanding 3 thoughts...".
- **[EVAL]**: Logs showing scores for different paths (e.g., 0.2 vs 0.9).
- **[DECISION]**: Final selection of the high-value path.

## 4. 🔍 Code Deep Dive
Specialize in the `plan_path` method.
- **File**: `backend/agents/path_planner_agent.py`
- **Key Method**: `_beam_search` (The ToT BFS logic).
