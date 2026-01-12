---
description: Verify Neo4j Vector Search Setup
---
# Neo4j Vector Search Validation Workflow

This workflow validates that the Neo4j Vector Index is correctly configured and that agents can perform hybrid retrieval.

## 1. Verify Index Existence
Run this Cypher query in Neo4j Browser:
```cypher
SHOW VECTOR INDEXES
```
*   **Expected**: Row with name `course_concept_index`, state `ONLINE`, dimensions `768`.

## 2. Verify Embeddings
Check if nodes have embeddings populated.
```cypher
MATCH (c:CourseConcept)
WHERE c.embedding IS NOT NULL
RETURN count(c) AS embedded_count
```
*   **Expected**: Count > 0.

## 3. Test Vector Search
Test the semantic search capability.
```cypher
WITH [0.01, 0.02, ...] AS dummy_vector // In reality, use Python driver to generate real vector
CALL db.index.vector.queryNodes('course_concept_index', 5, dummy_vector)
YIELD node, score
RETURN node.name, score
```

## 4. Run Python Unit Test
Create a test file `tests/test_vector_search.py`:
```python
import asyncio
from backend.agents.profiler_agent import ProfilerAgent

async def test_search():
    agent = ProfilerAgent("test_profiler", ...)
    results = await agent._find_goal_node_hybrid("machine learning")
    print(results)

if __name__ == "__main__":
    asyncio.run(test_search())
```
