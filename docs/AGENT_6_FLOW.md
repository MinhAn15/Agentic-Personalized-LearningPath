# Agent 6: KAG Agent Flow (Knowledge Graph Aggregator)

## 1. High-Level Architecture

The KAG Agent is responsible for **Knowledge Alignment**, **Artifact Generation**, and **System-Wide Learning**.

```mermaid
graph TD
    subgraph Trigger
        EVAL[EVALUATION_COMPLETED Event] --> GENERATE
        TIMER[Scheduled Task] --> ANALYZE
    end

    subgraph Phase1_OS_Kernel[Phase 1: MemGPT OS Kernel]
        TRIGGER --> PRES_CHECK{Memory Pressure > 70%?}
        PRES_CHECK -- Yes --> AUTO_ARCH[Auto-Archive: Evict & Summarize]
        PRES_CHECK -- No --> COMPILE[Compile Context: System+Core+Queue]
        
        AUTO_ARCH --> COMPILE
        COMPILE --> THINK[LLM: Generate Thought/Call]
        
        THINK -- Function Call --> EXEC_TOOL[Execute Tool]
        EXEC_TOOL --> LOOP_BACK[Heartbeat: Recurse]
        LOOP_BACK --> PRES_CHECK
        
        THINK -- Final Answer --> YIELD[Yield Response]
    end

    subgraph Phase2_Tools[Phase 2: Memory Tools]
        EXEC_TOOL -->|core_memory_append| RAM_UPD[Update Working Memory]
        EXEC_TOOL -->|archival_memory_search| DISK_READ[Search Neo4j]
        EXEC_TOOL -->|archival_memory_insert| DISK_WRITE[Create NoteNode]
    end
```

## 2. Core Workflows

### 2.1 OS Kernel (Heartbeat Loop)
The `execute` method runs a recursive loop (max 5 steps):
1.  **Monitor**: Checks `WorkingMemory.is_pressure_high()` (Token Limit).
2.  **Interrupt**: If high, evicts 50% of queue, summarizes, and stores to Archive.
3.  **Act**: LLM decides to call a tool (e.g., `archival_memory_search`) or answer.
4.  **Recurse**: If tool called, loop continues (Heartbeat) with tool output in context.

### 2.2 Zettelkasten Generation (Legacy/Tool)
*Exposed as `generate_artifact` tool.*
1.  **Extraction**: LLM extracts `key_insight`, `personal_example`.
2.  **Grounding**: Finds related existing notes.
3.  **Storage**: Creates `NoteNode` in Neo4j.

### 2.3 System Learning (Batch)
Aggregates data across ALL learners to find bottleneck concepts.
