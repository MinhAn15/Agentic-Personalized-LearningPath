---
description: Explore and Verify Agent 4 (Tutor / Chain of Thought).
---
# Agent 4: Tutor (The "Metacognitive Teacher")

This workflow guides you through understanding the **scientific basis**, **implementation**, and **verification** of Agent 4.

## 1. 🔬 Scientific Basis (Theory)
Agent 4 implements **Chain of Thought (CoT) (Wei 2022)**, ensuring the Tutor "thinks" (plans scaffolding) before "speaking" (sending a hint), simulating human pedagogical reasoning.
- **Read Theory**: `docs/SCIENTIFIC_BASIS.md` (Section 3.4).
- **View Whitebox**: `docs/AGENT_4_WHITEBOX.md`

## 2. 🗺️ Visual Architecture
Understanding the flow from Student Stuck -> Hidden CoT Phase -> Final Pedagogical Response.
- **View Diagram**: Open `docs/presentation/demo_dashboard.html` (Agent 4 Card).

## 3. 🧪 Live Verification
Run the test script to see the "Hidden Thought Trace".

```bash
python scripts/test_agent_4_cot.py
```

### What to Watch For:
- **[CoT TRACE]**: "Internal Monologue" logs (e.g., "Student is struggling with X... I should provide a hint about Y").
- **[RESPONSE]**: The final helpful message sent to the student.

## 4. 🔍 Code Deep Dive
Specialize in the `respond` method.
- **File**: `backend/agents/tutor_agent.py`
- **Key Method**: `_generate_cot_response` (The Thinking Before Speaking logic).

   - `✅ MOCK TEST PASSED`
