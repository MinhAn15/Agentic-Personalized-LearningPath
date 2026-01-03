# Walkthrough: Scientific Refinement (Agent 6 - KAG / Memory)

## 1. Goal
Upgrade Agent 6 from a passive Zettelkasten storage to a **MemGPT-inspired Operating System** capable of managing its own context window and performing multi-step reasoning.

## 2. Changes
### Backend (`kag_agent.py`)
*   **Added**: `WorkingMemory` class to simulate RAM (tracks content & token count).
*   **Added**: `is_pressure_high()` heuristic (70% threshold).
*   **Refactored**: `execute()` method turned into a `while` loop using a `request_heartbeat` flag.
*   **Added**: `_auto_archive()` triggered by system interrupts (Memory Pressure).

### Logic Refinement (Scientific Basis)
*   **System Interrupts**: Instead of waiting for the user, the agent self-monitors. If RAM > 70%, it triggers an internal "System Alert", causing the Agent to flush old memories to Disk (Neo4j) to prevent overflow.
*   **Heartbeat**: Enables "Function Chaining". The agent can now look up a note, read it, realize it needs more info, and search again—all in one "turn" before replying to the user (Packer 2023).

## 3. Verification
*   **Script**: `scripts/verify_memgpt.py`
*   **Tests**:
    1.  **Pressure Trigger**: Confirmed that filling `WorkingMemory` past 70/100 tokens triggers `_auto_archive`.
    2.  **Heartbeat Recursion**: Confirmed that if a step returns `request_heartbeat=True`, the `execute` loop continues automatically.

## 4. Documentation
*   Updated `SCIENTIFIC_BASIS.md` to reference MemGPT concepts (Heartbeat, Interrupts).
*   Updated `NOTEBOOKLM_PROMPTS.md` with the new architecture context.
