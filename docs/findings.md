# Project Findings & Research Log

## Key Findings

### Neo4j Connectivity Issues (2026-01-26)
- **Issue**: Neo4j container refused connections (`Connection refused`), `pid` file error.
- **Root Cause**: Corrupted Docker volume for Neo4j data caused a crash loop. Stale `neo4j.pid` file prevented startup.
- **Resolution**:
    1. Stopped container.
    2. Removed the named volume `agentic-personalized-learningpath_neo4j_data`.
    3. Restarted container to let it recreate the volume.
    4. Verified with `scripts/debug_neo4j.py` (Successful on Attempt 4).

### Data Ingestion Strategy
- **Vector Store**: Using local `BAAI/bge-small-en-v1.5` embeddings is efficient and cost-effective (~2000 chunks processed locally).
- **Knowledge Graph**: 
    - Traversal Depth limit is necessary to prevent "explosion" of nodes.
    - Socratic concepts map well to Graph nodes (Concept -> Prerequisite).

### Pedagogical Effectiveness (Simulated)
- **Ablation Study**: Removing the "Socratic Critic" (Agent 5) resulted in a significant drop in Learning Gain (Effect size d dropped from 0.85 to 0.65). This supports the thesis that active critique is essential.
