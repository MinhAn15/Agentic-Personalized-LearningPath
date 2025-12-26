# 🔬 Deep Analysis: RAG vs GraphRAG Conflict Resolution

## 📝 Vấn đề đặt ra

Trong hệ thống 3-Layer Grounding của Agent 4:
- **Layer 1 (RAG)**: Vector-based retrieval từ documents
- **Layer 2 (Course KG)**: Structured knowledge từ Neo4j
- **Layer 3 (Personal KG)**: Learner-specific data

**Câu hỏi**: Nếu 2 layers trả về kết quả khác nhau hoặc mâu thuẫn, ta nên xử lý như thế nào?

---

## 🧪 Scientific Research (2024-2025)

### 1. TruthfulRAG (2024)

**Nguồn**: ResearchGate - "TruthfulRAG: Using Knowledge Graphs for Factual Conflict Resolution"

**Cơ chế**:
- Extract triples từ retrieved content
- Query Knowledge Graph để verify
- **Entropy-based filtering** để loại bỏ inconsistencies

**Insight**: KG được coi là **ground truth** vì dữ liệu đã được curated và validated.

### 2. HybGRAG (2024)

**Nguồn**: GraphRAG.com - Hybrid Graph-RAG for Semi-Structured Knowledge

**Cơ chế**:
- **Retriever Bank**: Nhiều retrievers song song
- **Critic Module**: Đánh giá chất lượng từng retrieval
- **Adaptive Selection**: Chọn retriever tốt nhất cho từng query

### 3. Reciprocal Rank Fusion (RRF)

**Nguồn**: Medium - "Hybrid RAG: Merging Dense and Sparse Retrieval"

**Formula**:
```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

**Cơ chế**: Combine rankings từ nhiều retrievers, không dựa vào absolute scores.

---

## 🔍 Systematic Problem Breakdown

### Scenario 1: Complementary Information (Không mâu thuẫn)

| Layer | Content |
|-------|---------|
| RAG | "SELECT is used to query data" |
| Course KG | Definition: "SELECT retrieves rows from tables" |
| Personal KG | Past error: "Confused SELECT with UPDATE" |

**Kết luận**: **Merge all** - Thông tin bổ sung cho nhau.

### Scenario 2: Different Granularity (Cùng hướng, khác độ chi tiết)

| Layer | Content |
|-------|---------|
| RAG | "SQL is a query language" (general) |
| Course KG | "SELECT syntax: SELECT col FROM table WHERE..." (specific) |

**Kết luận**: **Prioritize KG** - Structured knowledge có độ chính xác cao hơn.

### Scenario 3: Direct Conflict (Mâu thuẫn trực tiếp)

| Layer | Content |
|-------|---------|
| RAG | "NULL values can be compared with =" |
| Course KG | Misconception: "NULL = NULL returns FALSE, use IS NULL" |

**Kết luận**: **Trust Course KG** - Được curated bởi Agent 1, đã qua validation.

### Scenario 4: Outdated vs Current

| Layer | Content |
|-------|---------|
| RAG | "MySQL 5.7 syntax..." (old document) |
| Course KG | Current version info |

**Kết luận**: **Use confidence scores** - Document với low score sẽ bị downweight.

---

## 🎯 Recommended Strategy: Hierarchical Trust

```
Trust Hierarchy:
1. Course KG (Curated, validated) - HIGHEST
2. Personal KG (Learner-specific context)
3. RAG (Raw documents) - LOWEST (may contain outdated/incorrect info)
```

### Why This Order?

| Layer | Pros | Cons |
|-------|------|------|
| **Course KG** | Curated by Agent 1, validated, structured | May miss edge cases |
| **Personal KG** | Personalized, tracks learner's specific errors | Limited scope |
| **RAG** | Broad coverage, detailed examples | May contain errors, outdated |

---

## 💡 Implementation Recommendation

### Current System (Weight-based):
```python
confidence = 0.40 * doc_score + 0.35 * kg_score + 0.25 * personal_score
```

### Proposed Enhancement: Conflict-Aware Fusion

```python
def resolve_conflicts(doc_context, kg_context, personal_context):
    """
    TruthfulRAG-inspired conflict resolution.
    
    Strategy:
    1. If KG has `common_misconceptions` that match RAG content → WARN
    2. If Personal has `past_errors` matching current topic → PERSONALIZE
    3. Use KG as ground truth for factual claims
    """
    # Check if RAG content matches known misconceptions
    kg_misconceptions = kg_context.get("misconceptions", [])
    doc_chunks = doc_context.get("retrieved_chunks", [])
    
    conflicts = []
    for chunk in doc_chunks:
        for misconception in kg_misconceptions:
            if semantic_match(chunk, misconception):
                conflicts.append({
                    "source": "DOCUMENT",
                    "conflict_type": "MATCHES_MISCONCEPTION",
                    "content": chunk,
                    "correction": misconception
                })
    
    # Prioritize KG for definitions, use RAG for examples only
    return {
        "definition": kg_context.get("definition"),  # Always from KG
        "examples": doc_context.get("chunks", []),   # From RAG
        "warnings": conflicts,
        "personal_context": personal_context
    }
```

---

## 📊 When to Use Each Layer

| Question Type | Primary Layer | Secondary | Reason |
|---------------|---------------|-----------|--------|
| "What is X?" | Course KG | RAG | Definition cần chính xác |
| "Give me examples" | RAG | Course KG | Documents có nhiều examples |
| "I'm confused about..." | Personal KG | Course KG | Need learner's past errors |
| "What's the difference..." | Course KG | Course KG | Relationships are structured |

---

## ✅ Final Recommendation

Hệ thống 3-Layer **đã tối ưu** cho usecase này vì:

1. **Complementary by Design**: Mỗi layer phục vụ mục đích khác nhau
2. **Weights phản ánh trust**: KG (0.35) gần bằng RAG (0.40) nhưng structured hơn
3. **Personal layer là differentiator**: Không thể có từ RAG/KG thuần

### Improvements Applied:
1. ✅ Parallel execution (faster)
2. ✅ Dynamic scoring (more accurate)
3. ✅ Layer scores metadata (enables future conflict detection)

### Future Enhancement (TODO):
- Add semantic similarity check between RAG chunks and KG misconceptions
- Implement RRF-style ranking fusion
- Add confidence degradation over time for RAG content
