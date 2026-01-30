---
description: Deep Dive into Agent Technical Flow (System Perspective: Input -> Process -> Output)
---

# System Flow Deep Dive Workflow

This workflow guides the detailed analysis of an Agent's internal technical flow from a "Systems Engineering" perspective. It decomposes each phase into **Input**, **Process**, and **Output**, with a focus on Data Flow, Technical Mechanisms, and Engineering Rationale.

## Step 1: Context Loading & Target Identification
<!-- // turbo -->
1. Identify the target Agent (e.g., Agent 1, Agent 2...).
2. Read the Master Architecture Document: `docs/SYSTEM_ARCHITECTURE.md`.
3. Read the Agent's Whitebox Specification: `docs/AGENT_X_WHITEBOX.md`.
4. (Optional) Read the Agent's source code if specific implementation details are missing in the docs.

## Step 2: Phase Decomposition & Analysis
For *each* major phase identified in the Whitebox Spec, perform the following "Black Box Analysis":

### Template for Each Phase

#### **Phase Name** (e.g., Semantic Chunking, LKT Inference)

**1. INPUT (Đầu vào)**
*   **Source**: Where does the data come from? (e.g., RabbitMQ Event, API Request, Redis Cache).
*   **Data Structure**: detailed schema (e.g., `JSON {content: str, metadata: dict}`, `Vector[768]`).
*   **State Dependencies**: What prior state is required? (e.g., `UserLoggedIn`, `GraphIndexLoaded`).

**2. PROCESS (Quy trình Xử lý)**
*   **Data Flow (Luồng dữ liệu)**:
    *   How does data move? (e.g., "Streamed byte-by-byte", "Batched in groups of 500", "Async dispatched").
*   **Technical Mechanism (Cơ chế Kỹ thuật)**:
    *   **Algorithms**: (e.g., LinUCB, Cosine Similarity, ANN Search).
    *   **Patterns**: (e.g., Semaphore Throttling, Double-Checked Locking, Chain-of-Thought).
    *   **Libraries/Tools**: (e.g., `asyncio`, `Neo4j GraphDataScience`, `LangChain`).
*   **Rationale (Tại sao làm vậy?)**:
    *   **Engineering**: (e.g., "To handle 10k concurrent users", "To prevent Race Conditions").
    *   **Scientific**: (e.g., "Aligned with LightRAG dual-retrieval", "Based on Ebbinghaus Forgetting Curve").

**3. OUTPUT (Đầu ra)**
*   **Destination**: Where does the result go? (e.g., Neo4j DB, Frontend via SSE, SQS Queue).
*   **Artifact**: The concrete result (e.g., `ConceptNode` created, `Feedback` returned).
*   **Side Effects**: (e.g., "Cache invalidated", "Log entry created").

## Step 3: Synthesis & Reporting
1. Compile the phase analyses into a structured Markdown report.
2. Highlight any **Critical Paths** or **Bottlenecks** identified during the deep dive.
3. Ensure the language is strict "Systems Engineering" terminology (e.g., "Idempotency", "Throughput", "Latency", "ACID").

## Usage Example
"Run system-flow-deep-dive for Agent 1"
