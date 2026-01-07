---
description: Explore and Verify Agent 6 (KAG / MemGPT).
---
# Agent 6: KAG (The "Operating System")

This workflow guides you through understanding the **scientific basis**, **implementation**, and **verification** of Agent 6.

## 1. 🔬 Scientific Basis (Theory)
Agent 6 implements **MemGPT (Packer 2023)**, treating the LLM as an OS that manages its own memory hierarchy (System, Core, Archival) and runs an autonomous "Heartbeat" loop.
- **Read Theory**: `docs/SCIENTIFIC_BASIS.md` (Section 3.6).
- **View Whitebox**: `docs/AGENT_6_WHITEBOX.md`

## 2. 🗺️ Visual Architecture
Understanding the Heartbeat Loop: Monitor -> Interrupt -> Think -> Tool -> Loop.
- **View Diagram**: Open `docs/presentation/demo_dashboard.html` (Agent 6 Card).

## 3. 🧪 Live Verification
Run the test script to see the Heartbeat and Memory Pressure system.

```bash
python scripts/test_agent_6_memgpt.py
```

### What to Watch For:
- **💓 Heartbeat triggered**: Showing the autonomous loop.
- **💾 Auto-Archiving**: Showing memory management (eviction) when token limit is hit.

## 4. 🔍 Code Deep Dive
Specialize in the `execute` method.
- **File**: `backend/agents/kag_agent.py`
- **Key Method**: `execute` (The Heartbeat Loop implementation).

   - `✅ MOCK TEST PASSED`
