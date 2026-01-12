# Neo4j Vector Index Implementation Guide

This guide details how to implement Vector Search in Neo4j for the Agentic Personalized Learning Path project, enabling semantic search for Goal Node identification.

> **Verification**: Yes, Neo4j (v5.15+) natively supports Vector Indexing and Search via Cypher.

---

## 1. Prerequisites (Setup)

Ensure your Neo4j instance is version **5.15 or higher** (versions 5.11-5.14 had valid support but syntax may vary slightly; 5.15+ is stable).

You need to define 3 parameters:
1.  **Index Name**: e.g., `course_concept_index`
2.  **Vector Dimension**: Must match your Embedding Model.
    *   **Google Gemini (`embedding-001`)**: **768** dimensions.
    *   *Check your model documentation if different.*
3.  **Similarity Metric**: typically `cosine` for semantic text search.

---

## 2. Step 1: Create the Vector Index

Run this Cypher command **ONCE** (e.g., during system initialization or migration).

```cypher
CREATE VECTOR INDEX course_concept_index IF NOT EXISTS
FOR (c:CourseConcept)
ON (c.embedding)
OPTIONS {indexConfig: {
 `vector.dimensions`: 768,
 `vector.similarity_function`: 'cosine'
}}
```

*   **Target**: Nodes labeled `:CourseConcept`.
*   **Property**: Looking at `c.embedding` property on those nodes.

---

## 3. Step 2: Populate Embeddings (Ingestion)

When Agent 1 (Knowledge Extraction) creates a concept, you must compute embedding and store it.

**Python (Agent 1 Code):**
```python
# Assuming you have a list of concepts to insert
from llama_index.embeddings.gemini import GeminiEmbedding

# 1. Initialize Model
embed_model = GeminiEmbedding(model_name="models/embedding-001")

async def ingest_concept(tx, concept_data):
    # 2. Generate Embedding
    embedding_vector = await embed_model.aget_text_embedding(
        f"{concept_data['name']}: {concept_data['description']}"
    )

    # 3. Store in Neo4j
    await tx.run("""
        MERGE (c:CourseConcept {concept_id: $cid})
        SET c.name = $name,
            c.description = $desc,
            c.embedding = $vector  // List of floats
    """, 
    cid=concept_data['id'], 
    name=concept_data['name'], 
    desc=concept_data['description'],
    vector=embedding_vector
    )
```

---

## 4. Step 3: Querying (The Search)

When Agent 2 (Profiler) wants to find a Goal Node based on User Input.

**Scenario**: User says "I want to learn about neural networks".

**Python (Agent 2 Code):**
```python
async def find_goal_nodes(user_query: str, limit: int = 5):
    # 1. Embed the User Query
    query_vector = await embed_model.aget_text_embedding(user_query)

    # 2. Run Vector Search Cypher
    cypher_query = """
    CALL db.index.vector.queryNodes('course_concept_index', $k, $query_embedding)
    YIELD node, score
    
    // Optional: Filter by score threshold (e.g., > 0.7 relevant)
    WHERE score > 0.7
    
    RETURN 
        node.concept_id AS id, 
        node.name AS name, 
        node.bloom_level AS bloom,
        score
    ORDER BY score DESC
    """
    
    results = await neo4j_driver.run(cypher_query, 
                                     k=limit, 
                                     query_embedding=query_vector)
    return results
```

---

## 5. Verification Checklist

1.  **Check Index Status**:
    ```cypher
    SHOW VECTOR INDEXES
    ```
    Ensure status is `ONLINE` and `populationPercent` reaches 100%.

2.  **Dimension Mismatch Error**:
    If you try to set a 1536-dim vector (OpenAI) into a 768-dim index (Gemini), Neo4j will throw an error. **Consistency is key.**

3.  **Null Embeddings**:
    Nodes without the `embedding` property are simply ignored by the index. Ensure your Agent 1 backfill covers all nodes.

---

## 6. Advanced: Hybrid Search (Fulltext + Vector)

To improve precision (e.g., matching exact acronyms like "SQL"), compare vector results with keyword search:

```cypher
// 1. Vector Search
CALL db.index.vector.queryNodes('course_concept_index', 10, $emb) 
YIELD node, score AS vector_score

// 2. Keyword Filtering (Optional)
MATCH (node) 
WHERE toLower(node.name) CONTAINS toLower($keyword)

RETURN node.name, vector_score
```
