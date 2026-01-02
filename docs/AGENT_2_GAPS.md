# Agent 2: Identified Gaps & Technical Debt

> **Status**: Open
> **Date**: 2026-01-02
> **Priority**: High

## 1. Scalability: Process-Local Locking
- **Status**: ✅ **RESOLVED** (2026-01-02)
- **Description**: The current `_on_evaluation_completed` handler uses `asyncio.Lock`. This locks only within a single process.
- **Impact**: In a distributed deployment (e.g., Kubernetes with multiple replicas), multiple instances can race to update the same learner profile, leading to data corruption (Lost Update problem).
- **Fix Implemented**: Replaced `asyncio.Lock` with **Redis Distributed Lock** across all 4 event handlers (`evaluation`, `pace_check`, `artifact_created`, `kg_sync`).
- **Verification**: Verified via Code Audit and Test Runner logic.

## 2. Configuration: Hardcoded Paths
- **Status**: ✅ **RESOLVED** (2026-01-02)
- **Description**: `_get_vector_index` uses hardcoded path `"./storage/vector_index"`.
- **Impact**: Breaks if the application is run from a different working directory.
- **Fix Implemented**: Updated to use `os.getenv("VECTOR_INDEX_PATH")` with fallback.

## 3. Resilience: Strict Neo4j Dependency
- **Status**: ✅ **RESOLVED** (2026-01-02)
- **Description**: The file imports `Neo4jPropertyGraphStore` from `llama-index-graph-stores-neo4j` at the module level.
- **Impact**: If this package is missing (or optional), the entire agent fails to load.
- **Fix Implemented**: Wrapped import in `try/except` block and added runtime check in `_get_graph_retriever`.

## 4. Performance: Synchronous Vectorization
- **Status**: 🟡 **OPEN**
- **Description**: `_vectorize_profile` is an async method but performs pure CPU-bound math.
- **Impact**: Not a huge issue now, but conceptually it blocks the event loop slightly.
- **Proposed Fix**: Keep as async but ensure no I/O blocking inside. (Low priority).
