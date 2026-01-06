# Agent 6: KAG Agent (MemGPT) Whitebox Analysis [VERIFIED]

## 1. Internal Architecture

Agent 6 serves as the **Personal Knowledge OS**, implementing the MemGPT architecture [Packer 2023] to manage infinite context via a tiered memory system.

### 1.1 Memory Hierarchy
*   **Main Context (RAM)**:
    *   **System Instructions**: Immutable Persona + Function Schemas.
    *   **Core Memory**: Pinned facts (e.g., User Profile, Current Goals). Mutable via `core_memory_append`.
    *   **FIFO Queue**: Rolling conversation history. Evicted to Archival Storage when pressure > 70%.
*   **External Context (Disk)**:
    *   **Archival Storage**: Neo4j Graph + Vector Index. Accessible via `archival_memory_search`.
    *   **Recall Storage**: Chat logs synchronized to Disk.

### 1.2 Process Flow (OS Kernel)
The `execute` method runs a **Heartbeat Loop**:
1.  **Monitor**: Checks `WorkingMemory` pressure.
    *   *Interrupt*: If > 70%, triggers `_auto_archive` (Evict 50% -> Summarize -> Store).
2.  **Compile**: Constructs `[SYSTEM] + [CORE] + [HISTORY]` prompt.
3.  **Think (System 2)**: LLM generates response or Function Call.
4.  **Act (Paging)**: Executes `[FUNCTION] tool_name(args)`.
    *   *Tools*: `core_memory_append`, `archival_memory_search`, etc.
5.  **Loop**: If tool called, recurses (Heartbeat). If final answer, yields to User.

---

## 2. Algorithms & Data Structures

### 2.1 Context Management (`WorkingMemory`)
*   **Structure**: `System + Core + Queue`.
*   **Heuristic**: Tokens estimated via `len(chars) // 4`.
*   **Eviction**: `flush_queue(fraction=0.5)` removes oldest messages from Queue, preserving Core and System.

### 2.2 Constructivist Note Generation
*   **Dual-Code Theory**: Content includes both **Text** (Key Insight) and **Visuals** (Mermaid Concept Map).
*   **Zettelkasten**: Notes are atomic, linked, and tagged.

---

## 3. Resilience

### 3.1 Memory Pressure
*   **Trigger**: > 70% of `max_tokens` (default 8192).
*   **Handling**: `_auto_archive` creates a "Session Summary" node in Neo4j and clears the queue, preventing Context Window Overflow (Crash).

### 3.2 Infinite Loop Guard
*   **Constraint**: `max_steps` (default 5) prevents the Heartbeat Loop from getting stuck in a function calling cycle.

---

## 4. Verification Strategy

Verified via `scripts/test_agent_6_memgpt.py`:

1.  **Heartbeat Logic**: Validated that the agent can chain `core_memory_append` -> `archival_memory_search` -> `Final Answer`.
2.  **Context Compilation**: Verified prompt structure includes Core Memory block.
3.  **Pressure Interrupt**: Verified `_auto_archive` triggers when context is filled.

**Status**: Verified (Logic Implemented & Tested).
