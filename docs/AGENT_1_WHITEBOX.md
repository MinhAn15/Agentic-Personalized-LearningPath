# Whitebox Analysis: Agent 1 (Knowledge Extraction)

**File chính**: `backend/agents/knowledge_extraction_agent.py`
**Version**: 2.1 (Refined for Scalability & Reliability)

---

## Bối cảnh & Mục tiêu

Trong hệ thống Personalized Learning Path, **Agent 1 ("The Librarian")** đóng vai trò nền tảng. Nhiệm vụ của nó là chuyển đổi dữ liệu thô (File PDF, Text, Transcript) thành tri thức có cấu trúc (**Course Knowledge Graph**).

Nếu Agent 1 sai sót (Concept rác, quan hệ sai), toàn bộ luồng phía sau (Profiler, Path Planner) sẽ sai theo.
Do đó, Agent 1 được thiết kế với các tiêu chí khắt khe: **Chính xác**, **Ổn định (Idempotent)** và **Mở rộng (Scalable)**.

---

## 1. Input (Đầu vào)

Agent 1 nhận một `Message` thông qua Event Bus hoặc API Call trực tiếp.

| Tham số | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|--------------|----------|-------|
| `document_content` | `str` | ✅ | Nội dung văn bản của tài liệu. |
| `document_title` | `str` | ✅ | Tiêu đề tài liệu (dùng để định danh và tạo Context). |
| `domain` | `str` | ❌ | (Mới) Vùng kiến thức (VD: "physics", "sql"). Nếu có, sẽ override AI classification. |
| `force_reprocess` | `bool` | ❌ | Nếu `True`, sẽ xử lý lại dù file đã tồn tại (Hash checking). |

**Cơ chế Idempotency (Chống trùng lặp):**
Trước khi xử lý, Agent tính mã băm `SHA-256` của `document_content`. Nếu mã này đã tồn tại trong `DocumentRegistry` (Redis/Postgres) và `force_reprocess=False`, Agent sẽ trả về trạng thái `SKIPPED` ngay lập tức để tiết kiệm tài nguyên.

---

## 2. Configuration & Constants

Các tham số này được tinh chỉnh dựa trên thực nghiệm để cân bằng giữa Tốc độ và Rate Limit của LLM.

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `MAX_CONCURRENCY` | `5` | Số lượng chunk được xử lý song song tối đa. |
| `CHUNK_SIZE` | `2000` | Số ký tự (xấp xỉ) cho mỗi phân đoạn ngữ nghĩa. |
| `FUZZY_THRESHOLD` | `0.8` | Độ tương đồng (Levenshtein distance) để coi 2 concept là ứng viên trùng nhau. |
| `SIMILARITY_THRESHOLD_STRICT` | `0.95` | Ngưỡng tự động merge không cần hỏi lại. |

---

### 2.5 Global Theme (Domain Context) - LightRAG Principle

**Cơ sở khoa học:**

| Paper/Concept | Năm | Đóng góp cho Global Theme |
|---------------|-----|---------------------------|
| **LightRAG** (Guo et al.) | 2024 | Dual-level retrieval: Low-level (entities) + **High-level (global themes)**. Global theme giúp LLM hiểu ngữ cảnh tổng thể. |
| **Prompt Engineering** (OpenAI) | 2023 | Context trong prompt giúp constrain output, giảm hallucination. |
| **Knowledge Graph** | - | Domain làm root node, giúp organize entities theo hierarchy. |

**Nguyên lý ứng dụng:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Global Theme = Domain                                          │
│  (e.g., "sql", "machine_learning")                             │
│                                                                 │
│  Inject vào TẤT CẢ prompts:                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Chunking    │  │ Layer 1     │  │ Layer 2-3   │             │
│  │ (DSHP-LLM)  │  │ (Concepts)  │  │ (Relations) │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         └────────────────┼────────────────┘                     │
│                          ▼                                      │
│             "Domain: {domain}" in ALL prompts                   │
└─────────────────────────────────────────────────────────────────┘
```

**Thiết kế Domain System:**

| Aspect | Chi tiết |
|--------|----------|
| **Source** | Admin nhập khi upload document (required) |
| **Predefined List** | `config/domains.py` với danh sách domains |
| **Add New** | Admin có thể tạo domain mới nếu chưa có |
| **Purpose** | Giúp LLM hiểu context, **KHÔNG dùng để filter** |
| **Cross-domain** | Concepts có thể thuộc nhiều domains (e.g., SQL Server → sql, bi) |

**Lưu ý quan trọng:** Domain **KHÔNG phải metadata filtering**. Một concept có thể xuất hiện ở nhiều domains khác nhau. Domain chỉ để guide LLM extraction chính xác hơn.

### 2.6 Paper Alignment & Adaptation (LightRAG Deviation)

> [!IMPORTANT]
> Section này giải thích sự khác biệt giữa LightRAG paper gốc và implementation trong thesis.

#### 2.6.1 LightRAG Original Architecture (Guo et al., 2024)

```
┌─────────────────────────────────────────────────────────────┐
│                   LightRAG (Original Paper)                 │
├─────────────────────────────────────────────────────────────┤
│  DUAL-GRAPH Architecture:                                   │
│                                                             │
│  ┌─────────────────┐       ┌─────────────────┐             │
│  │  Entity Graph   │  +    │  Keyword Graph  │             │
│  │  (Nodes: Named  │       │  (Nodes: Thematic│             │
│  │   Entities)     │       │   Keywords)      │             │
│  │  (Edges: Relations)     │  (Edges: Co-occur)│             │
│  └─────────────────┘       └─────────────────┘             │
│          │                         │                        │
│          └─────────┬───────────────┘                        │
│                    ▼                                        │
│           Dual-Level Retrieval:                             │
│           - Low-Level: Entity traversal                     │
│           - High-Level: Keyword traversal                   │
└─────────────────────────────────────────────────────────────┘
```

#### 2.6.2 Thesis Adaptation (This Implementation)

```
┌─────────────────────────────────────────────────────────────┐
│                   Thesis Implementation                      │
├─────────────────────────────────────────────────────────────┤
│  HYBRID Architecture:                                        │
│                                                             │
│  ┌─────────────────┐       ┌─────────────────┐             │
│  │  Entity Graph   │       │  DocumentRegistry│             │
│  │  (Neo4j)        │       │  (PostgreSQL)    │             │
│  │  - Concepts     │       │  - Content Keywords│           │
│  │  - Relations    │       │  - Edge Keywords  │            │
│  │  - Edge Keywords│       │  (Hippocampal Index)│           │
│  └────────┬────────┘       └────────┬────────┘             │
│           │                         │                        │
│           └─────────┬───────────────┘                        │
│                     ▼                                        │
│           Retrieval Strategy:                                │
│           - Structural: Graph traversal (Neo4j)              │
│           - Semantic: Keyword lookup (Registry)              │
└─────────────────────────────────────────────────────────────┘
```

#### 2.6.3 What Was Adapted vs Simplified

| Aspect | LightRAG Original | Thesis Adaptation | Justification |
|--------|-------------------|-------------------|---------------|
| **Entity Graph** | ✅ Full | ✅ Full | Core mechanism, unchanged |
| **Keyword Graph** | Separate graph | Embedded in Registry | **Simplification**: Avoid 2nd graph overhead |
| **Edge Keywords** | Stored in keyword graph | Stored on relationship properties | Same semantics, simpler storage |
| **Dual Retrieval** | Graph + Graph | Graph + Registry lookup | **Equivalent functionality**, less complexity |
| **Global Theme** | Implicit via keywords | Explicit via Domain | **Enhancement**: More explicit context |

#### 2.6.4 Justification for Deviations

**Why not implement separate Keyword Graph?**

1. **Complexity vs Value**: A second graph adds operational complexity (sync, consistency) with marginal retrieval improvement for educational content.

2. **Educational Domain Specificity**: Educational content has well-defined structure (sections, concepts) unlike open-domain text. Entity graph alone captures most semantic structure.

3. **Registry as Index**: Using `DocumentRegistry` with keyword storage achieves the "Hippocampal Index" effect described in HippoRAG without full graph duplication.

4. **Thesis Scope**: Proving the concept of dual-level retrieval is achievable with simpler architecture. Full graph implementation is **Future Work**.

#### 2.6.5 Equivalent Mechanisms

| Paper Mechanism | Implementation Location | Code Reference |
|-----------------|------------------------|----------------|
| Entity extraction | `_extract_concepts_from_chunk()` | Line 499-568 |
| Relationship extraction | `_extract_relationships_from_chunk()` | Line 628-665 |
| **Edge keywords** | `keywords` field in relationship | `prompts.py` L52-87 |
| **Content keywords** | `_extract_content_keywords()` | Line 708-719 |
| Keyword storage | `DocumentRegistry.content_keywords` | COURSEKG_UPDATED event |

## 3. Process (Luồng xử lý chi tiết)

Pipeline của Agent 1 hoạt động theo mô hình **Parallel Semantic Processing**.

### 3.1 Giai đoạn 1: Semantic Chunking (Phân đoạn ngữ nghĩa)

**Cơ sở Khoa học (Papers bổ trợ):**

| Paper | Năm | Đóng góp cho Chunking |
|-------|-----|----------------------|
| **Reflexion** (Shinn et al.) | 2023 | Kỹ thuật self-critique cho phép LLM tự đánh giá và sửa lỗi phân đoạn. |
| **LightRAG** (Guo et al.) | 2024 | Nguyên lý bảo toàn "semantic boundaries" - không cắt giữa ý. |
| **Chain-of-Thought** (Wei et al.) | 2022 | Reasoning-based prompting để phân tích cấu trúc tài liệu. |

**Triển khai thực tế (Adaptive Pipeline):**

Thay vì dùng các phương pháp truyền thống (Fixed-size window, Regex), hệ thống áp dụng **Adaptive Agentic Chunking** với 3 chế độ:

| Chế độ | Điều kiện | Input type | Phương pháp |
|--------|-----------|------------|-------------|
| **Standard** | < 10K tokens | Plain text | 3-Phase Pipeline |
| **MultiDocFusion** | > 10K tokens | Plain text | 5-Stage Hierarchical |
| **Vision** | PDF/PPT/Image | Binary file | Gemini Vision → MultiDocFusion |

### 3.1.1 Vision Mode (Gemini Vision) - MultiDocFusion Paper

Khi input là **file binary** (PDF, PPT, Image), hệ thống sử dụng **Gemini Vision** để:

```
File Binary → Base64 Encode → Gemini Vision API → {paragraphs[], hierarchy{}} → DSHP-LLM → DFS → Chunks
```

**Tại sao cần Vision?**
- Paper MultiDocFusion (EMNLP 2025) dùng Vision model để detect visual layout
- Plain text extraction mất thông tin về heading sizes, fonts, spacing
- Vision model nhìn thấy cấu trúc trực quan → hierarchy chính xác hơn

**Prompt cho Gemini Vision:**
```
Analyze the visual layout of this document and extract:
1. All text paragraphs in reading order
2. The hierarchical structure (sections, subsections)
3. Identify headings based on visual cues (font size, boldness)

Return JSON: {paragraphs: [...], hierarchy: {title, children: [...]}}
```

**Fallback Strategy:**
- Nếu Vision fail → `pymupdf` text extraction → MultiDocFusion pipeline
- Nếu file không hỗ trợ → Standard text pipeline

### 3.1.2 Standard Pipeline (Docs < 10K tokens)

**Chế độ 1: Standard Pipeline (Docs < 10K tokens)**

1. **Architect Phase**: LLM phân tích *ý nghĩa* toàn bộ văn bản và đề xuất Table of Contents.
2. **Refiner Phase (Reflexion)**: LLM tự phản biện ("Example bị tách?", "Section quá nhỏ?").
3. **Executor Phase**: Trích xuất nội dung thực tế bằng fuzzy matching.

**Chế độ 2: MultiDocFusion Pipeline (Docs > 10K tokens) - EMNLP 2025**

| Stage | Mô tả | Phương thức kỹ thuật | Input → Output |
|-------|-------|---------------------|----------------|
| **1. Pre-split** | Tách theo paragraphs (multi-level fallback) | 4-level: `\n\n` → `\n` → sentence → fixed-size | `Document → List[Paragraph]` |
| **2. DSHP-LLM** | LLM xây dựng Hierarchical Tree | LLM Prompt → JSON Tree structure | `Paragraphs → Tree{title, level, children[], paragraphs[]}` |
| **3. DFS Grouping** | Duyệt tree depth-first | Recursive DFS traversal, leaf nodes → sections | `Tree → List[Section{start_text, end_text, purpose}]` |
| **4. Refiner** | LLM tự phản biện (Reflexion) | Same as Standard Pipeline | `Sections → Refined Sections` |
| **5. Executor** | Trích xuất nội dung thực tế | Fuzzy text matching (`_fuzzy_find`) | `Refined Sections → List[SemanticChunk]` |

**Stage 1 - Pre-split (Multi-level Fallback):**

| Level | Strategy | Khi nào dùng | Fallback condition |
|-------|----------|--------------|-------------------|
| **1** | `split('\n\n')` | Plain text, Markdown | < 3 paragraphs → Level 2 |
| **2** | `split('\n')` + chunk by size | PDF/OCR extraction | < 3 paragraphs → Level 3 |
| **3** | Sentence split (`. ? !`) | Continuous text | < 3 paragraphs → Level 4 |
| **4** | Fixed-size chunks (~2000 chars) | Last resort (messy text) | Always succeeds |


**Chi tiết kỹ thuật từng Stage:**

**Stage 2 - DSHP-LLM (Document Section Hierarchical Parsing):**

Áp dụng **Discourse Structure Theory** (Mann & Thompson, 1988): Câu đầu thường chứa topic sentence.

```python
# First 3 Sentences extraction (thay vì fixed 100 chars)
def extract_first_sentences(text, n=3, max_chars=400):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return ' '.join(sentences[:n])[:max_chars]

# Prompt gửi LLM
prompt = f"""
Document Domain: {domain}
Document Title: {title}
Paragraphs: 
[P0] {extract_first_sentences(para_0)}
[P1] {extract_first_sentences(para_1)}

Task: Build HIERARCHICAL TREE, return JSON:
{{"title": "Root", "children": [...]}}
"""
```

**Stage 3 - DFS Grouping Algorithm:**
```python
def _dfs_group_tree(tree, paragraphs):
    sections = []
    def traverse(node, path=[]):
        if not node.children:  # Leaf node
            content = join(paragraphs[i] for i in node.paragraphs)
            sections.append({
                "title": node.title,
                "start_text": content[:50],
                "end_text": content[-50:]
            })
        else:
            for child in node.children:
                traverse(child, path + [node.title])
    traverse(tree)
    return sections
```

**Cấu hình:**
- `LARGE_DOC_TOKEN_THRESHOLD = 10000` (~40K chars, estimated 4 chars/token)
- `DEFAULT_PARAGRAPH_MIN_CHARS = 100` (paragraphs nhỏ hơn được merge)
- `domain` parameter: User có thể truyền domain hint (SQL, ML, etc.)

*   **Mục tiêu**: Chia nhỏ văn bản dài thành các đoạn nhỏ có ý nghĩa trọn vẹn (không cắt giữa chừng câu hoặc ý).
*   **Phương pháp**: Adaptive routing dựa trên document size.
*   **Kết quả**: List các `SemanticChunk` với metadata sư phạm (`pedagogical_purpose`).

### 3.2 Giai đoạn 2: Information Extraction (Trích xuất song song)
Đây là trái tim của Agent. Thay vì chạy tuần tự (Sequential), Agent sử dụng `asyncio.gather` để bắn nhiều request lên LLM cùng lúc.

**Code minh họa kiến trúc Semaphore:**
```python
# Semaphore limits concurrent tasks
semaphore = asyncio.Semaphore(self.MAX_CONCURRENCY)

async def _process_with_limit(chunk):
    async with semaphore:
        return await self._process_single_chunk(chunk)

# Run all chunks in parallel
tasks = [_process_with_limit(chunk) for chunk in chunks]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Trong mỗi Chunk, quy trình 3 lớp (3-Layer Extraction) diễn ra:**

| Layer | Mục đích | Domain Injection | Input | Output |
|-------|----------|------------------|-------|--------|
| **Layer 1** | Concept Extraction | ✅ `Domain/Subject Area: {domain}` | `SemanticChunk.content` | `List[Concept{id, name, context}]` |
| **Layer 2** | Relationship Extraction | ✅ `{domain_context}` in template | `List[concept_id]` | `List[Relationship]` |
| **Layer 3** | Metadata Enrichment | ✅ `{domain_context}` prefix | `Concept` list | `{bloom_level, tags[]}` |

**Layer 1 - Concept Extraction (Chi tiết):**
- **Input**: `SemanticChunk` với `content`, `chunk_type`, `pedagogical_purpose`
- **Domain Context**: Inject ở đầu prompt (Global Theme)
- **LLM Prompt**:
  ```
  You are extracting learning concepts from a document section.
  Domain/Subject Area: SQL  # ← DOMAIN INJECTED HERE
  Document: SQL Basics Tutorial
  Section: ...
  ```
- **ID Generation**: `ConceptIdBuilder._sanitize()` tạo Stable ID:
  - `"SELECT Statement"` → `sql.select_statement`
  - `"SELECT Query"` → `sql.select_query`
- **Output**: `List[Concept]` với `concept_code = {domain}.{snake_case_name}`
- **Code Reference**: `_extract_concepts_from_chunk()` line 499-568

**Layer 2 - Relationship Extraction (Chi tiết):**
- **Input**: Danh sách `concept_id` từ Layer 1 + original chunk content
- **Domain Context**: `{domain_context}` placeholder trong `LIGHTRAG_RELATIONSHIP_EXTRACTION_PROMPT`
- **Prompt Pattern**: LightRAG (Guo et al., 2024) - Knowledge Graph extraction
- **7 Relationship Types**:
  - `PREREQUISITE_OF`, `RELATED_TO`, `PART_OF`, `EXAMPLE_OF`, `DERIVED_FROM`, `USED_IN`, `CONTRASTS_WITH`
- **Output per relation**: `{source_id, target_id, type, keywords[], weight, confidence}`
- **Code Reference**: `_extract_relationships_from_chunk()` line 628-665, `prompts.py` line 52-87

**Layer 3 - Metadata Enrichment (Chi tiết):**
- **Input**: `Concept` object + chunk context
- **Domain Context**: `{domain_context}` prepended to prompt
- **Classification Tasks**:
  - Bloom's Taxonomy: `REMEMBER → UNDERSTAND → APPLY → ANALYZE → EVALUATE → CREATE`
  - Time Estimate: 15-120 phút (dựa trên complexity)
  - Semantic Tags: 3-5 keywords cho search/filter
- **Output**: Updated `Concept` với enriched metadata
- **Code Reference**: `_enrich_metadata()` line 669-720

### 3.3 Giai đoạn 3: Entity Resolution (Hợp nhất thực thể)

**Vấn đề**: `SELECT_STATEMENT` vs `SELECT_QUERY` có thể là cùng 1 khái niệm.

**Giải pháp (3-Way Similarity)**:

| Component | Weight | Phương pháp |
|-----------|--------|-------------|
| Semantic | 60% | Embedding cosine similarity |
| Structural | 30% | Prerequisite overlap (Jaccard) |
| Contextual | 10% | Tag overlap (Jaccard) |

**Quy trình 2 giai đoạn**:
1. **Within-Batch Dedup**: Agglomerative clustering trong batch mới (threshold 0.80)
2. **External Merge**: So sánh với Neo4j existing concepts (threshold 0.80)

**Threshold**: `MERGE_THRESHOLD = 0.80` (giảm từ 0.85 để merge aggressive hơn)

**Tối ưu hóa**: Two-Stage Resolution - Candidate Retrieval (Top-K=20) trước Deep Comparison → O(1) thay vì O(N).

### 3.4 Giai đoạn 4: Persistence (Lưu trữ)
Sử dụng `Neo4jBatchUpserter` để ghi dữ liệu theo lô (Batch), giảm số lượng Transaction, tăng tốc độ ghi gấp 10-50 lần so với ghi từng node.

---

## 4. Output (Đầu ra)

Kết quả trả về là một Dict báo cáo thống kê:

```json
{
  "status": "COMPLETED", // hoặc PARTIAL_SUCCESS
  "stats": {
    "concepts_created": 15,
    "relationships_created": 20,
    "chunks_processed": 5,
    "chunks_failed": 0
  },
  "execution_time": 4.5,
  "document_id": "..."
}
```

**Cơ chế Partial Success**: Nếu một vài chunk bị lỗi (do LLM time out), Agent **không** fail toàn bộ file. Nó sẽ ghi nhận `failed_chunks` và trả về trạng thái `PARTIAL_SUCCESS`. Điều này cực kỳ quan trọng khi xử lý sách giáo khoa dày hàng trăm trang.

---

## 5. Các thuật toán & Kỹ thuật đặc biệt

### 5.1 Dynamic Domain Injection
Cho phép "User Override". Hệ thống AI thường đoán Domain (Vùng kiến thức), nhưng đôi khi người dùng muốn ép buộc.
*   Logic: `final_domain = user_domain OR llm_predicted_domain`.
*   Tác dụng: Giúp tổ chức Graph ngăn nắp theo ý đồ giảng dạy.

### 5.2 Fuzzy Fulltext Retrieval
Sử dụng Lucene Engine tích hợp trong Neo4j.
*   Query: `CALL db.index.fulltext.queryNodes("conceptNameIndex", "name~0.8")`
*   Ưu điểm: Bắt được cả lỗi chính tả (Typo) và các biến thể từ vựng (plural/singular).

### 5.3 Scalability Analysis (Phân tích khả năng mở rộng)

Agent 1 được thiết kế cho môi trường **Medium-Scale Educational Platform** (1-10K concepts). Dưới đây là phân tích chi tiết:

#### 5.3.1 Complexity Analysis

| Component | Complexity | Description |
|-----------|------------|-------------|
| **Chunking** | O(N) | N = document length, linear scan |
| **LLM Extraction** | O(C × L) | C = chunks, L = LLM calls per chunk (3) |
| **Entity Resolution** | O(C × K) | C = new concepts, K = candidates (Top-20) |
| **Neo4j Write** | O(C + R) | C = concepts, R = relationships |

**Bottleneck**: Entity Resolution với large existing graph.

#### 5.3.2 Scalability Limits

| Scale | # Concepts | # Documents | Entity Resolution | Status |
|-------|------------|-------------|-------------------|--------|
| **Small** | < 500 | < 50 | 500 × 20 = 10K comparisons | ✅ Fast |
| **Medium** | 500 - 5K | 50 - 500 | 5K × 20 = 100K comparisons | ✅ Acceptable |
| **Large** | 5K - 50K | 500 - 5K | 50K × 20 = 1M comparisons | ⚠️ Slow |
| **Enterprise** | > 50K | > 5K | > 1M comparisons | ❌ Needs optimization |

**Current Implementation**: Optimized cho **Medium Scale** (trường đại học nhỏ, ~5K concepts).

#### 5.3.3 Current Mitigations

| Optimization | Impact | Implementation |
|--------------|--------|----------------|
| **Two-Stage Resolution** | O(N) → O(K) | Candidate retrieval (Top-K=20) trước Deep Comparison |
| **Fulltext Index** | Fast name lookup | Neo4j Lucene index trên `CourseConcept.name` |
| **Batch Upsert** | 10-50x faster writes | `Neo4jBatchUpserter` với batch_size=100 |
| **Semaphore Concurrency** | Rate limit protection | MAX_CONCURRENCY=5 cho LLM calls |

#### 5.3.4 Future Optimizations (Documented for Thesis)

Nếu cần scale lên Enterprise level, các optimization sau có thể được áp dụng:

| Optimization | Expected Impact | Complexity |
|--------------|-----------------|------------|
| **Approximate Nearest Neighbor (ANN)** | O(log N) similarity search | Medium |
| **LSH (Locality-Sensitive Hashing)** | O(1) candidate retrieval | High |
| **Hierarchical Clustering** | Reduce comparison space | Medium |
| **Vector Database (Pinecone/Weaviate)** | Native ANN support | Low (integration) |

**Thesis Scope**: Current implementation đủ cho **Proof of Concept** và **Medium-Scale Deployment**. Enterprise optimization là **Future Work**.

#### 5.3.5 Latency Analysis (LLM Call Count)

| Document Size | Chunks | LLM Calls | Est. Time (5 concurrent) |
|---------------|--------|-----------|--------------------------|
| 5K tokens | 2 | 6 | ~3 seconds |
| 20K tokens | 10 | 30 | ~15 seconds |
| 100K tokens | 50 | 150 | ~75 seconds |
| 500K tokens | 250 | 750 | ~6 minutes |

**Note**: LLM latency ~500ms per call. Semaphore limits to 5 concurrent.

## 6. Evaluation Methodology (Đánh giá chất lượng)

Để chứng minh Agent 1 hoạt động chính xác, cần có phương pháp đo lường khách quan.

### 6.1 Ground Truth Approach

**Vấn đề**: Không có "Gold Standard" dataset cho Knowledge Graph extraction từ tài liệu giáo dục.

**Giải pháp**: Tạo **Semi-Automated Ground Truth**:

| Phương pháp | Mô tả | Ưu/Nhược |
|-------------|-------|----------|
| **Expert Annotation** | Chuyên gia tạo manual KG từ 3-5 tài liệu mẫu | ✅ Chính xác, ❌ Tốn thời gian |
| **LLM-as-Judge** | GPT-4 so sánh extracted vs expected | ✅ Scalable, ❌ LLM bias |
| **Cross-Validation** | 2 người annotate độc lập, tính Inter-Rater Agreement | ✅ Khách quan, ❌ Cần 2 experts |

**Đề xuất cho Thesis**: Kết hợp **Expert Annotation** (3 tài liệu) + **LLM-as-Judge** (10 tài liệu).

### 6.2 Metrics (Chỉ số đánh giá)

#### Concept Extraction Quality

| Metric | Công thức | Ý nghĩa |
|--------|-----------|---------|
| **Precision** | `TP / (TP + FP)` | % concepts đúng trong số được extract |
| **Recall** | `TP / (TP + FN)` | % concepts được extract trong số thực tế có |
| **F1-Score** | `2 * P * R / (P + R)` | Harmonic mean của Precision và Recall |

**Định nghĩa**:
- **True Positive (TP)**: Concept extracted khớp với Ground Truth
- **False Positive (FP)**: Concept extracted nhưng không có trong Ground Truth (rác)
- **False Negative (FN)**: Concept có trong Ground Truth nhưng bị miss

**Khớp (Match)**: Sử dụng 3-Way Similarity với threshold 0.80.

#### Relationship Extraction Quality

| Metric | Công thức |
|--------|-----------|
| **Edge Precision** | `Correct edges / Extracted edges` |
| **Edge Recall** | `Correct edges / Ground Truth edges` |
| **Edge F1** | Harmonic mean |

**Correct Edge**: `(source, target, type)` tuple khớp với Ground Truth.

#### Entity Resolution Quality

| Metric | Công thức | Ý nghĩa |
|--------|-----------|---------|
| **Merge Accuracy** | `Correct merges / Total merges` | % merge decisions đúng |
| **Over-merge Rate** | `False merges / Total merges` | % merge nhầm (2 concepts khác nhau bị gộp) |
| **Under-merge Rate** | `Missed merges / Should merge` | % bỏ lỡ (2 concepts giống nhau không được gộp) |

### 6.3 Practical Evaluation Protocol

**Bước 1: Chuẩn bị Ground Truth**
```
1. Chọn 3 tài liệu đại diện (Short, Medium, Long)
2. Expert tạo manual KG (concepts + relationships)
3. Lưu vào docs/evaluation/ground_truth_{n}.json
```

**Bước 2: Chạy Extraction**
```bash
python scripts/evaluate_agent_1.py --ground_truth docs/evaluation/ground_truth_1.json
```

**Bước 3: Tính Metrics**
```python
# Pseudo-code
def evaluate(extracted: List[Concept], ground_truth: List[Concept]):
    tp = count_matches(extracted, ground_truth, threshold=0.80)
    fp = len(extracted) - tp
    fn = len(ground_truth) - tp
    
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall)
    
    return {"precision": precision, "recall": recall, "f1": f1}
```

### 6.4 Target Benchmarks

Dựa trên literature review các hệ thống KG extraction:

| Metric | Target (Thesis) | SOTA Reference |
|--------|-----------------|----------------|
| **Concept Precision** | ≥ 0.85 | LightRAG: 0.87 |
| **Concept Recall** | ≥ 0.75 | LightRAG: 0.79 |
| **Concept F1** | ≥ 0.80 | LightRAG: 0.83 |
| **Edge Precision** | ≥ 0.70 | (Relationships harder) |
| **Edge Recall** | ≥ 0.60 | |

### 6.5 Limitations & Threats to Validity

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Ground Truth bias | Expert may miss concepts | Cross-validation với 2 experts |
| Domain-specific | Results may not generalize | Test trên 3 domains khác nhau |
| LLM variance | Same input → different output | Run 3 lần, report mean ± std |

---

## 7. Kết luận (Dành cho phản biện luận văn)

Agent 1 không chỉ là một script gọi GPT-4. Nó là một **Engineering Pipeline** hoàn chỉnh giải quyết các vấn đề thực tế của ứng dụng LLM:
1.  **Chi phí & Tốc độ**: Nhờ Parallel Processing.
2.  **Chất lượng dữ liệu**: Nhờ Entity Resolution & Stable IDs.
3.  **Độ tin cậy**: Nhờ Idempotency & Partial Success handling.
4.  **Đánh giá khách quan**: Nhờ Evaluation Methodology với Ground Truth.

Hệ thống sẵn sàng để scale cho khối lượng dữ liệu của một trường đại học.
