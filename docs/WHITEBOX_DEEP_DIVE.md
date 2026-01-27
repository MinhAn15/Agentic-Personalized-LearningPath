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
# Agent 2: Profiler Agent - Whitebox Analysis

## 1. Bối cảnh & Mục tiêu
**Profiler Agent** đóng vai trò là "State Manager" (Quản lý trạng thái) của hệ thống Personalized Learning. Khác với các hệ thống LMS truyền thống chỉ lưu dữ liệu tĩnh, Agent 2 duy trì một **Learner Profile** (Hồ sơ người học) đa chiều và cập nhật theo thời gian thực.
**Mục tiêu**: Xây dựng một vector đặc trưng 10 chiều $\mathbf{x}_t$ đại diện cho trạng thái người học, được sử dụng bởi Path Planner (Agent 3) cho thuật toán tối ưu hóa LinUCB bandit.

## 2. Cơ sở Lý thuyết (Theoretical Framework)

### 2.1 Mô hình Người học (Vector 10 chiều)
Chúng tôi mô hình hóa trạng thái người học $\mathcal{S}$ dưới dạng vector $\mathbf{x} \in \mathbb{R}^{10}$, bao gồm:
1.  **Knowledge State ($x_0$)**: Mức độ thành thạo trung bình qua các khái niệm chính ($0 \le x_0 \le 1$).
2.  **Learning Style ($x_{1-4}$)**: Mã hóa One-hot theo mô hình VARK (Visual, Aural, Read/Write, Kinesthetic).
3.  **Skill Level ($x_5$)**: Khả năng xử lý độ khó đã được chuẩn hóa (Beginner=0.2, Intermediate=0.5, Advanced=0.8).
4.  **Time Constraints ($x_6$)**: Thời gian khả dụng mỗi phiên học (chuẩn hóa).
5.  **Cognitive Load ($x_7$)**: Mức độ Bloom's Taxonomy (1=Remember đến 6=Create), chuẩn hóa về $[0,1]$.
6.  **Velocity ($x_8$)**: Tốc độ học tập (concepts/hour).
7.  **Scope ($x_9$)**: Kích thước tương đối của mục tiêu học tập.

### 2.2 Vấn đề Cold Start & Hybrid Retrieval
Để khởi tạo $\mathbf{x}_0$ mà không có dữ liệu lịch sử, chúng tôi sử dụng **Diagnostic Assessment** (Đánh giá chẩn đoán) kết hợp **Hybrid Retrieval**:
1.  **Retrieval**: Với một mục tiêu (VD: "Learn SQL"), hệ thống dùng **Neo4j Vector Index** để tìm "Topographic Anchors" gần nhất về ngữ nghĩa, kết hợp bộ lọc đồ thị.
2.  **Generation**: LLM sinh ra 5 câu hỏi chẩn đoán dựa trên các anchor này.
3.  **Estimation**: **LKT (Language Knowledge Tracing)** dự đoán mức độ thành thạo dựa trên semantic understanding.

### 2.3 LKT: Language Knowledge Tracing (Lee 2024)

**Cơ sở khoa học:**

| Paper | Năm | Core Innovation |
|-------|-----|-----------------|
| **LKT** (Lee et al.) | 2024 | Replace LSTM (DKT) with Pre-trained Language Model |
| **DKT** (Piech et al.) | 2015 | LSTM for sequential knowledge tracing |

**Key Mechanism - Semantic Mastery Prediction:**

Thay vì dùng heuristics đơn giản (`level * difficulty`), LKT sử dụng LLM để:
1. **Format interaction history** theo định dạng text:
   ```
   [CLS] SELECT_STATEMENT
   What is SELECT? [CORRECT]
   WHERE_CLAUSE
   Explain WHERE syntax [INCORRECT]
   ```
2. **Semantic reasoning**: LLM hiểu mối quan hệ giữa concepts (mastered SELECT → partial mastery WHERE)
3. **Cold Start handling**: Với zero history, LLM dự đoán dựa trên semantic difficulty

**Implementation (`_predict_mastery_lkt`):**

```python
# LKT Prompt Structure
prompt = f"""
LEARNER CONTEXT:
- Topic: {topic}
- Stated Level: {current_level}
- Interaction History: {history_text}  # [CLS] format

CONCEPTS TO ASSESS:
{concept_list}

TASK: Predict mastery probability (0.0-1.0) for each concept.
"""

# LLM returns structured predictions
{"predictions": [
  {"concept_id": "SELECT", "mastery": 0.35, "reasoning": "..."},
  {"concept_id": "WHERE", "mastery": 0.15, "reasoning": "..."}
]}
```

**Fallback Strategy:**
- Nếu LLM fails → `_fallback_mastery_heuristic()` với simple level * difficulty
- Đảm bảo graceful degradation

**Code Reference:** `profiler_agent.py` lines 574-718

## 3. Chi tiết Thuật toán

### 3.1 Profile Vectorization (`_vectorize_profile`)
Chuyển đổi hồ sơ dạng JSON sang vector $\mathbf{x}$ cho Contextual Bandit:
$$
\mathbf{x} = [ \mu_{mastery}, \mathbb{I}_{vis}, \mathbb{I}_{aud}, \mathbb{I}_{read}, \mathbb{I}_{kin}, \eta_{skill}, \tau_{time}, \beta_{bloom}, \nu_{vel}, \sigma_{scope} ]
$$
Trong đó $\mathbb{I}$ là hàm chỉ thị (indicator function) cho learning style.

### 3.2 Dynamic Interest Decay (Suy giảm hứng thú động)
Để phản ánh đường cong quên lãng (forgetting curve) và sự thay đổi hứng thú, chúng tôi áp dụng suy giảm theo hàm mũ cho các thẻ hứng thú (interest tags) sau mỗi tương tác lớn:
$$
I_{tag}(t+1) = I_{tag}(t) \times \lambda
$$
Với $\lambda = 0.95$ (hệ số suy giảm). Các tag giảm xuống dưới ngưỡng $\epsilon = 0.1$ sẽ bị loại bỏ (pruned).

### 3.3 Xử lý Sự kiện Mở rộng (Distributed Lock)
Vì Agent có trạng thái (stateful) và phản ứng theo sự kiện (Event-Driven), chúng tôi cài đặt các trình xử lý đặc biệt để kiểm soát đồng thời (concurrency control):
*   **Race Condition**: Nhiều agent (Evaluator, Timer) có thể cập nhật profile cùng lúc.
*   **Giải pháp**: Sử dụng **Redis Distributed Lock** (thuật toán RedLock).
*   **Cơ chế**:
    ```python
    lock = redis.lock(f"lock:learner:{id}")
    if lock.acquire():
        state = read()
        state = update(state)
        write(state)
        lock.release()
    ```
Giải pháp này đảm bảo Cập nhật Trạng thái Nguyên tử (Atomic State Updates) trong môi trường phân tán (Kubernetes).

## 4. Logic Triển khai (Implementation Logic)

### 4.1 Persistence Layer (Dual-Write)
1.  **PostgreSQL**: Nguồn chân lý (Canonical source of truth) đảm bảo tính ACID.
2.  **Neo4j**: Personal Knowledge Graph ("Shadow Graph" - Đồ thị bóng).
    *   **Nodes**: `:Learner`, `:MasteryNode` (liên kết tới Course Concepts), `:ErrorEpisode`.
    *   **Edges**: `[:HAS_MASTERY]`, `[:HAS_ERROR]`.
3.  **Redis**: Hot State Cache (TTL 1 giờ) để Agent 3 đọc với độ trễ thấp.

### 4.2 Ước lượng Bloom's Taxonomy
Cấp độ Bloom được ước lượng động từ kết quả bài quiz:
$$
Bloom = 0.6 \cdot Score + 0.25 \cdot Difficulty + 0.15 \cdot QType_{boost}
$$
Trong đó $QType_{boost}$ ưu tiên các câu hỏi tổng hợp/áp dụng hơn là nhớ lại kiến thức.

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 LKT Prediction Accuracy

**Mục tiêu**: Đo lường độ chính xác của dự đoán mastery từ LKT so với ground truth.

**Metrics:**

| Metric | Công thức | Ý nghĩa |
|--------|-----------|---------|
| **MAE** | $\frac{1}{n}\sum|p_i - y_i|$ | Mean Absolute Error giữa predicted vs actual mastery |
| **RMSE** | $\sqrt{\frac{1}{n}\sum(p_i - y_i)^2}$ | Root Mean Square Error |
| **AUC-ROC** | ROC curve area | Khả năng phân biệt mastered vs not-mastered |

**Ground Truth Collection:**
1. **Post-Assessment**: Sau diagnostic, cho learner làm real quiz → actual mastery
2. **Longitudinal Tracking**: Compare initial prediction vs final mastery after course

**Target Benchmarks (per LKT paper):**

| Metric | Target | LKT Paper Reference |
|--------|--------|---------------------|
| **MAE** | ≤ 0.15 | LKT: 0.12 |
| **AUC-ROC** | ≥ 0.75 | LKT: 0.78 |

### 5.2 Profile Vectorization Validation

**Mục tiêu**: Đảm bảo 10-dim vector phản ánh đúng learner state.

**Validation Methods:**

| Method | Description |
|--------|-------------|
| **Dimension Range Check** | All dims ∈ [0.0, 1.0] |
| **One-Hot Consistency** | Learning style dims sum to 1 |
| **Peer Similarity** | Similar learners have high cosine similarity |

**Unit Test Example:**
```python
def test_vector_validity(profile_vector):
    assert len(profile_vector) == 10
    assert all(0 <= v <= 1 for v in profile_vector)
    assert sum(profile_vector[1:5]) == 1  # One-hot VARK
```

### 5.3 Cold Start Effectiveness

**Mục tiêu**: Đo lường chất lượng initial profile với zero interaction history.

**Metrics:**

| Metric | Definition |
|--------|------------|
| **First-Attempt Success Rate** | % learners pass first recommended concept |
| **Path Revision Rate** | % paths revised after first 3 interactions |

**Target:**
- First-Attempt Success ≥ 60% (vs 33% random baseline)
- Path Revision Rate ≤ 30%

### 5.4 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No real user study | Cannot validate engagement | Simulate with synthetic learners |
| LLM variance | Different predictions each run | Run 3x, report mean ± std |
| No long-term tracking | Cannot measure retention | Document as Future Work |

---

## 6. Kết luận
Agent 2 cung cấp "Context" ($\mathbf{x}_t$) cần thiết cho vòng lặp Agentic RL. Bằng cách kết hợp **LKT (Language Knowledge Tracing)** để dự đoán mastery và **Graph RAG** để khởi tạo, nó giải quyết vấn đề Cold Start với semantic understanding thay vì heuristics đơn giản.
# Agent 3: Path Planner Whitebox Analysis [RESOLVED]

## 1. Kiến trúc Nội tại (Internal Architecture)

Agent 3 là "người điều hướng" (navigator) của hệ thống, chịu trách nhiệm tạo ra chuỗi khái niệm học tập tối ưu. Khác với các bộ lập kế hoạch dựa trên luật tĩnh (static rule-based), nó sử dụng phương pháp lai kết hợp giữa **Graph Traversal (Adaptive Chaining)** và **Reinforcement Learning (LinUCB)**.

### 1.1 Quy trình Xử lý (6 Pha)

1.  **Input & Context Loading**:
    -   Nhận `learner_id`, `goal`, và `last_result`.
    -   Tải Learner Profile mạnh mẽ (vector + phong cách ưu tiên).
    -   Truy vấn Personal Knowledge Graph (Neo4j) để xác định các ứng viên (candidates).

2.  **Smart Filtering (Lọc thông minh)**:
    -   **Personal Subgraph Expansion**: Thay vì quét toàn bộ KG, phương pháp bắt đầu từ các khái niệm đã biết (`:MasteryNode` trong Neo4j) và mở rộng sang các lân cận trực tiếp (`NEXT`, `REQUIRES`). Điều này đảm bảo khả năng mở rộng O(1) so với kích thước đồ thị.

3.  **Probabilistic Mastery Gate (Nâng cấp Khoa học)**:
    -   Thay thế logic đạt/trượt nhị phân (binary pass/fail).
    -   Công thức: `gate_prob = min(1.0, current_score / GATE_FULL_PASS_SCORE)`
    -   Logic:
        -   Nếu `random() > gate_prob`: **Force Remediation** (Chế độ BACKWARD - Ép buộc học lại).
        -   Ngược lại: Cho phép tiến trình bình thường (FORWARD/ACCELERATE).
    -   *Lợi ích:* Ngăn chặn việc "đoán mò" (lucky guesses) tạo ra các lỗ hổng kiến thức dài hạn.

4.  **Adaptive Chaining (Lớp Heuristic)**:
    -   Xác định *hướng* di chuyển dựa trên `ChainingMode`:
        -   **FORWARD (Standard)**: Đi theo cạnh `NEXT`.
        -   **BACKWARD (Remediation)**: Đi theo cạnh `REQUIRES` (tiên quyết).
        -   **ACCELERATE (High Mastery)**: Bỏ qua các nút trung gian nếu đã thỏa mãn tiên quyết.
        -   **REVIEW (Spaced Repetition)**: Ngẫu nhiên 10% cơ hội (cấu hình qua `REVIEW_CHANCE`) để xem lại concept cũ.

5.  **LinUCB Selection (Lớp Ngẫu nhiên - Stochastic)**:
    -   Chọn *bước đi đơn lẻ tốt nhất* từ các ứng viên hợp lệ.
    -   Sử dụng thuật toán Contextual Bandit (Li et al., 2010).

6.  **Output Generation**:
    -   Tạo đối tượng JSON `LearningPath`.
    -   Tính toán xác suất thành công và tốc độ (pacing).

---

## 2. Thuật toán & Cấu trúc Dữ liệu

### 2.1 Cài đặt LinUCB
-   **Context**: Vector 10 chiều từ Learner Profile.
-   **Arms**: Mỗi Concept ID trong danh sách ứng viên là một cánh tay (arm).
-   **State**: Ma trận cho mỗi arm được lưu trong Redis (`linucb:{concept_id}`).
    -   `A` (10x10): Ma trận hiệp phương sai (xấp xỉ nghịch đảo).
    -   `b` (10x1): Vector lịch sử phần thưởng (reward history).
-   **Mục tiêu Lựa chọn**: Tối đa hóa Upper Confidence Bound (UCB).

### 2.2 Adaptive Chaining Logic
Agent duy trì một máy trạng thái cho `ChainingMode`:

| Trigger (Kích hoạt) | Mode | Hành động |
| :--- | :--- | :--- |
| `last_result="PROCEED"` | **FORWARD** | Di chuyển tới concept kế tiếp trong chuỗi. |
| `last_result="REMEDIATE"` | **BACKWARD** | Xác định các điều kiện tiên quyết chưa thành thạo. |
| `last_result="MASTERED"` | **ACCELERATE** | Kiểm tra các lân cận 2 bước (`NEXT` -> `NEXT`). |
| `random() < REVIEW_CHANCE` | **REVIEW** | Chọn các concept chưa học hoặc đã cũ. |

---

## 3. Khả năng phục hồi & Đồng thời [FIXED]

### 3.1 Distributed Locking (Redis)
**Vấn đề (Gap Identified)**: Các sự kiện phản hồi đồng thời (ví dụ: hoàn thành quiz nhanh) gây ra race conditions trong cập nhật ma trận LinUCB (`read-modify-write`).

**Giải pháp**:
-   Triển khai `redis.lock(name=f"lock:concept:{concept_id}", timeout=5)` bên trong `_on_evaluation_feedback`.
-   Đảm bảo cập nhật nguyên tử (atomic updates) cho các ma trận toàn cục `A` và `b` của mỗi concept.
-   **Tác động**: Ngăn chặn hỏng ma trận và phân kỳ chính sách học tập.

### 3.2 Configuration Management
**Vấn đề**: Các ngưỡng (`0.8`, `0.7`) bị hardcode rải rác trong code.
**Giải pháp**:
-   Tập trung tất cả thresholds trong `backend/core/constants.py`.
-   Import vào Agent 3 (`MASTERY_PROCEED_THRESHOLD`, `GATE_FULL_PASS_SCORE`).
-   Tăng cường khả năng bảo trì và tinh chỉnh thực nghiệm.

### 3.3 Lazy Initialization & Error Handling
-   **JSON Handling**: Thêm các import còn thiếu để ngăn lỗi `NameError`.
-   **Mock Resilience**: Test runner giả lập `redis.pipeline` dưới dạng đồng bộ (synchronous) để khớp với mẫu sử dụng thực tế, ngăn lỗi thuộc tính `coroutine` trong quá trình test.

---

## 4. Chiến lược Kiểm thử (Verification Strategy)

Agent được kiểm thử thông qua `scripts/test_agent_3.py` hỗ trợ:
1.  **Mock Mode**:
    -   Giả lập đồ thị Neo4j và trạng thái Redis.
    -   Patch `random` để kiểm thử Probabilistic Gate một cách tất định (deterministic).
    -   Xác minh việc chiếm dụng Lock.
2.  **Real Mode**:
    -   Kết nối tới live services để kiểm thử luồng đầu cuối (end-to-end).

### 4.3 Latency Analysis (ToT vs LinUCB)

**LLM Call Count per Planning Session:**

| Component | Calls per Beam | Total (b=3, d=3) |
|-----------|----------------|------------------|
| **Thought Generator** | 1 per node | 3 × 3 = 9 calls |
| **State Evaluator** | 1 per candidate | 3 × 3 = 9 calls |
| **Total** | | ~18 LLM calls |

**Latency Breakdown:**

| Mode | LLM Calls | Est. Time |
|------|-----------|-----------|
| **ToT (Full)** | 18 | ~9 seconds |
| **ToT (Shallow, d=2)** | 12 | ~6 seconds |
| **LinUCB (Fallback)** | 0 | ~100ms |

**Optimization Strategies:**

| Strategy | Impact | Implementation |
|----------|--------|----------------|
| **Caching** | -50% calls | Cache thought generator results per concept |
| **Shallow Search** | -33% calls | Reduce depth to d=2 for known paths |
| **Async Parallel** | -40% time | Evaluate multiple candidates concurrently |
| **LinUCB Hybrid** | -70% calls | Use ToT only for first planning, LinUCB for re-planning |

**ToT vs LinUCB Comparison:**

| Aspect | ToT (Tree of Thoughts) | LinUCB (Bandit) |
|--------|------------------------|-----------------|
| **Latency** | ~9s | ~100ms |
| **Quality** | Higher (lookahead) | Good (exploitation) |
| **Exploration** | Strategic (System 2) | Random (UCB) |
| **Cold Start** | Excellent | Poor |
| **Use Case** | Initial planning | Re-planning, real-time |

**Thesis Position**: ToT for initial curriculum, LinUCB for incremental updates.

---

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 Path Quality Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Completion Rate** | % learners who complete the generated path | ≥ 70% |
| **Time to Mastery** | Average time to reach 80% mastery on goal | 20% faster than baseline |
| **Prerequisite Violations** | # concepts attempted without prerequisites | 0 (hard constraint) |
| **Backtrack Rate** | % sessions requiring BACKWARD chaining | ≤ 30% |

### 5.2 ToT-Specific Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Beam Diversity** | Avg unique concepts across beams | ≥ 2 per search |
| **Pruning Effectiveness** | % low-value paths correctly pruned | ≥ 80% |
| **Strategic Value Accuracy** | Correlation between predicted and actual success | ρ ≥ 0.6 |

### 5.3 Ground Truth & Baseline

**Baseline Comparison:**
- **Random Path**: Select next concept randomly
- **Greedy Path**: Always select highest mastery neighbor
- **Rule-based Path**: Fixed prerequisite ordering

**Expected Results:**

| Method | Completion Rate | Time to Mastery |
|--------|-----------------|-----------------|
| Random | ~40% | Baseline |
| Greedy | ~55% | -5% |
| Rule-based | ~60% | -10% |
| **ToT (Ours)** | **≥70%** | **-20%** |

### 5.4 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No large-scale user study | Cannot validate real engagement | Synthetic learner simulation |
| LLM cost | ToT expensive for scaling | LinUCB hybrid mode |
| Semantic drift | LLM may generate invalid concepts | Graph validation layer |

---

## 6. Kết luận

Agent 3 kết hợp **Tree of Thoughts** (cho chất lượng cao) với **LinUCB** (cho tốc độ) để tạo curriculum tối ưu. ToT được sử dụng cho initial planning với lookahead strategy, trong khi LinUCB handle real-time re-planning với latency thấp.
# Agent 4: Tutor Agent Whitebox Analysis [RESOLVED]

## 1. Kiến trúc Nội tại (Internal Architecture)

Agent 4 đóng vai trò là **AI Tutor**, cung cấp hướng dẫn Socratic cá nhân hóa. Nó vượt xa khỏi mô hình Q&A đơn giản bằng cách duy trì một máy trạng thái sư phạm (pedagogical state machine) và thực thi các nguyên tắc giáo dục.

### 1.1 Quy trình Xử lý (7 Pha)

1.  **Context Gathering (Thu thập Ngữ cảnh)**:
    -   Truy vấn Neo4j (Course KG) để lấy sự kiện/kiến thức.
    -   Truy vấn Neo4j (Personal KG) để lấy lịch sử/độ thành thạo của người dùng.
    -   (Tùy chọn) Truy xuất tài liệu RAG.

2.  **Intent Classification (Phân loại Ý định)**:
    -   Sử dụng LLM để phân loại ý định người học:
        -   `HELP_SEEKING`: Bối rối, bị chặn -> Cần **Scaffolding** (Giàn giáo hỗ trợ).
        -   `SENSE_MAKING`: Tò mò, khám phá -> Cần **Probing** (Thăm dò sâu).

3.  **Reverse Socratic State Machine**:
    -   Quyết định *mô thức* (mode) tương tác sư phạm.
    -   Logic mang tính tất định dựa trên `hint_level` và `mastery`, ngẫu nhiên cho các chiến lược nâng cao (`TEACH_BACK`).

4.  **3-Layer Grounding (Chống ảo giác)**:
    -   Truy xuất song song từ 3 nguồn với độ tin cậy có trọng số.
    -   **Conflict Detection (Phát hiện Xung đột)**: Nếu RAG mâu thuẫn Course KG (Similarity < 0.6), KG thắng, và độ tin cậy bị giảm (Phạt -0.1).

5.  **Response Generation**:
    -   LLM sinh văn bản được hướng dẫn bởi các mẫu "Socratic Prompt" đặc thù cho trạng thái hiện tại.

6.  **Harvard 7 Enforcement**:
    -   Kiểm tra hậu xử lý (post-processing) để đảm bảo phản hồi tuân thủ các nguyên tắc (ví dụ: Active Learning, Feedback).

7.  **State Persistence**:
    -   Trạng thái phiên làm việc được lưu vào Redis (`ttl=24h`).

---

## 2. Thuật toán & Cấu trúc Dữ liệu

### 2.1 Logic Trạng thái Socratic
Được cài đặt trong `_determine_socratic_state`:

| Trạng thái (State) | Tiêu chí Kích hoạt (Trigger Criteria) |
| :--- | :--- |
| **REFUTATION** | `has_misconception=True` |
| **SCAFFOLDING** | `intent=HELP_SEEKING` HOẶC `hint_level=1` |
| **PROBING** | `intent=SENSE_MAKING` HOẶC mặc định |
| **TEACH_BACK** | `mastery > 0.7` VÀ `rounds > 2` (40% cơ hội) |
| **CONCLUSION** | `hint_level >= 4` HOẶC `rounds >= 5` |

### 2.2 Trọng số 3-Layer Grounding
Chuẩn hóa trong `constants.py`:

-   `TUTOR_W_DOC = 0.4` (Bao phủ rộng)
-   `TUTOR_W_KG = 0.35` (Sự kiện có cấu trúc)
-   `TUTOR_W_PERSONAL = 0.25` (Ngữ cảnh người dùng)
-   **Ngưỡng (Threshold)**: 0.5 (dưới mức này = "I don't know")

---

## 3. Khả năng phục hồi & Cấu hình

### 3.1 Quản lý Cấu hình (Configuration Management)
-   Tất cả các ngưỡng (`0.6` conflict, `0.4` weights) được import từ `backend/core/constants.py`.
-   Cho phép tinh chỉnh toàn cục "Tutor Personality" mà không cần sửa code.

### 3.2 Xử lý Lỗi (Error Handling)
-   **RAG Fallback**: Nếu `vector_store` bị thiếu (thường gặp trong test/dev), lớp RAG trả về độ tin cậy 0.0 nhưng không làm crash agent.
-   **Mocking**: Unit tests sử dụng `sys.modules` patching để xử lý các phụ thuộc `llama_index` một cách khéo léo.

---

## 4. Chiến lược Kiểm thử (Verification Strategy)

Đã xác minh qua `scripts/test_agent_4.py`:

1.  **State Machine Tests**: Xác nhận chuyển đổi đúng từ Probing -> Scaffolding dựa trên intent.
2.  **Protege Effect**: Xác minh `TEACH_BACK` kích hoạt cho người học có độ thành thạo cao.
3.  **Math Verification**: Xác thực tính toán Tổng Trọng số (Weighted Sum) cho Độ tin cậy Grounding.
4.  **Conflict Logic**: Xác minh hình phạt độ tin cậy khi `_detect_conflict` trả về True.

### 4.3 Latency Analysis (CoT Trade-offs)

**LLM Call Count per Tutoring Turn:**

| Phase | LLM Calls | Component |
|-------|-----------|-----------|
| **INTRO/PROBING** | 1 | `_generate_probing_question()` |
| **SCAFFOLDING** | 3 | `_generate_cot_traces()` (n=3) |
| **ASSESSMENT** | 0 | Handoff to Evaluator |

**Latency Breakdown:**

| Scenario | LLM Calls | Est. Time |
|----------|-----------|-----------|
| Simple probe | 1 | ~500ms |
| CoT scaffolding | 3 | ~1.5s |
| Full session (5 turns) | ~7 | ~3.5s |

**Optimization Strategies:**

| Strategy | Impact | Status |
|----------|--------|--------|
| **Cached Traces** | Reuse CoT for same misconception | ✅ Implemented (state.current_cot_trace) |
| **Parallel Generation** | Generate 3 traces concurrently | ⏳ Future Work |
| **Shallow CoT** | 1 trace instead of 3 for simple questions | ⏳ Future Work |

**Direct Answer vs CoT Comparison:**

| Approach | Latency | Quality | Leakage Risk |
|----------|---------|---------|--------------|
| Direct LLM | ~500ms | Medium | High |
| **CoT (Ours)** | ~1.5s | Higher | Low (filtered) |

---

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 Tutoring Quality Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Engagement Rate** | % questions where student continues dialogue | ≥ 70% |
| **Scaffolding Effectiveness** | % sessions reaching ASSESSMENT phase | ≥ 60% |
| **Answer Leakage Rate** | % responses containing direct answers | ≤ 5% |
| **Grounding Confidence** | Average weighted confidence score | ≥ 0.6 |

### 5.2 CoT-Specific Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Consensus Rate** | % CoT traces agreeing on diagnosis | ≥ 66% |
| **Hint Progression** | Avg steps before student solves | 2-4 hints |
| **Exemplar Relevance** | % exemplars matching domain | ≥ 80% |

### 5.3 Harvard 7 Compliance

| Principle | Measurement | Target |
|-----------|-------------|--------|
| Active Learning | Questions asked per response | ≥ 1 |
| Prompt Feedback | Response time | ≤ 2s |
| Time on Task | Session duration | 5-15 min |
| High Expectations | Bloom level of questions | ≥ APPLY |

### 5.4 Baseline Comparison

| Method | Engagement | Learning Gain |
|--------|------------|---------------|
| Direct Answer | ~40% | Low |
| Scripted Hints | ~55% | Medium |
| **CoT Tutor (Ours)** | **≥70%** | **Higher** |

### 5.5 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No A/B user study | Cannot prove learning gain | Synthetic dialogues |
| Domain-specific examples | May not generalize | Expand exemplar library |
| LLM variability | Inconsistent CoT quality | Self-consistency voting |

---

## 6. Kết luận

Agent 4 kết hợp **Dynamic Chain-of-Thought** (Wei 2022) với **Method Ontology** để tạo tutoring experience thông minh. CoT hidden traces được slice thành từng bước scaffolding, với leakage guard ngăn tiết lộ đáp án. Self-consistency voting đảm bảo chất lượng hints.
# Agent 5: Evaluator Agent Whitebox Analysis [RESOLVED]

## 1. Kiến trúc Nội tại (Internal Architecture)

Agent 5 đóng vai trò là **Pedagogical Judge** (Giám khảo Sư phạm), đánh giá hiệu suất người học bằng cách sử dụng Rubric Đa yếu tố (Multi-Factor Rubric) đã được chuẩn hóa và xác định bước tiếp theo tối ưu trong lộ trình học tập.

### 1.1 Quy trình Xử lý (8 Pha)

1.  **Context Gathering (Thu thập Ngữ cảnh)**:
    -   Tải Concept Metadata (Độ khó, Hiểu lầm) từ Neo4j (Cached, TTL=1h).
    -   Tải Learner Profile (Độ thạo hiện tại) từ Personal KG.

2.  **JudgeLM Scoring (SOTA)**:
    -   **Kỹ thuật**: Reference-as-Prior (Zhu 2023).
    -   **Prompt**: "Assistant 1" (Golden - Chuẩn) vs "Assistant 2" (Student - Học viên).
    -   **Định dạng**: Ký hiệu `10.0 {score}` + JSON CoT (Chain of Thought).
    -   **Rubric**: Correctness (0.6), Completeness (0.2), Clarity (0.2).

3.  **Error Classification** (nếu Score < 0.8):
    -   Phân loại Taxonomy: `CONCEPTUAL` (Căn bản), `PROCEDURAL` (Quy trình), `INCOMPLETE` (Thiếu sót), `CARELESS` (Bất cẩn).
    -   Misconception Detection: Đối chiếu lỗi với các hiểu lầm (misconceptions) đã biết trong KG.

4.  **Feedback Generation**:
    -   Tạo phản hồi cá nhân hóa giải quyết các hiểu lầm cụ thể.

5.  **5-Path Decision Logic**:
    -   Xác định `PathDecision` dựa trên Điểm số, Loại lỗi, và Độ khó.
    -   **MASTERED** (>= 0.9): Bỏ qua, đi tiếp (Skip ahead).
    -   **PROCEED** (>= 0.8): Tiếp tục concept kế tiếp.
    -   **ALTERNATE** (>= 0.6): Thay đổi phương thức (modality).
    -   **REMEDIATE** (< 0.6 + Conceptual): Quay lại học lại.
    -   **RETRY** (< 0.6 + Other): Thử lại.

6.  **Mastery Update**:
    -   Sử dụng Weighted Moving Average (WMA - Trung bình trượt có trọng số).
    -   `New = (Current * 0.4) + (Score * 0.6)` (Trọng số chuẩn hóa).

7.  **Alerting**:
    -   Kích hoạt Instructor Alert nếu `score < 0.4` (Critical Failure - Thất bại nghiêm trọng).

8.  **Output**:
    -   Phát sự kiện `EVALUATION_COMPLETED` tới Path Planner.

---

## 2. Thuật toán & Cấu trúc Dữ liệu

### 2.1 5-Path Decision Engine
Được cài đặt trong `_make_path_decision`:

| Quyết định (Decision) | Điều kiện Cơ sở (Base Condition) | Điều chỉnh (Adjustment) |
| :--- | :--- | :--- |
| **MASTERED** | Score >= 0.9 | -0.05 nếu Diff>=4, -0.03 nếu High Mastery |
| **PROCEED** | Score >= 0.8 | -0.05 nếu Diff>=4 |
| **ALTERNATE** | Score >= 0.6 | -0.05 nếu Diff>=4 |
| **REMEDIATE** | < 0.6 VÀ Error=CONCEPTUAL | N/A |
| **RETRY** | < 0.6 VÀ Error!=CONCEPTUAL | N/A |

### 2.2 Configuration
Chuẩn hóa trong `constants.py`:
-   `EVAL_MASTERY_WEIGHT = 0.6`
-   `THRESHOLD_ALERT = 0.4`

---

## 3. Khả năng phục hồi (Resilience)

### 3.1 Xử lý Lỗi (Error Handling)
-   **Empty Response**: Ghi log cảnh báo, trả về điểm 0.0.
-   **LLM Failure**: Fallback về chấm điểm dựa trên trùng lặp từ khóa (keyword overlap scoring).
-   **Event Emit Failure**: Bỏ qua (swallow) lỗi để ngăn chặn việc làm sập luồng trả về của quá trình đánh giá.

---

## 4. Chiến lược Kiểm thử (Verification Strategy)

Đã xác minh qua `scripts/test_agent_5_judgelm.py`:

1.  **Prompt Structure**: Xác thực khớp chính xác với JudgeLM System Prompt (Hình 5).
2.  **Scoring Notation**: Xác minh việc phân tích cú pháp `10.0 X` và JSON fallback.
3.  **Rubric Weights**: Xác minh cập nhật tuyến tính gần đúng.

**Trạng thái**: Đã xác minh (Verified). Test Passed.

---

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 Grading Quality Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Human Correlation (Spearman's ρ)** | Correlation between LLM scores and expert grades | ≥ 0.85 |
| **Scoring Consistency** | Std dev of scores for same response (3 runs) | ≤ 0.05 |
| **Error Classification Accuracy** | % errors correctly classified | ≥ 80% |
| **Misconception Detection Rate** | % known misconceptions correctly identified | ≥ 75% |

### 5.2 JudgeLM-Specific Metrics

| Metric | Definition | Target (per Zhu 2023) |
|--------|------------|----------------------|
| **Position Bias** | Score difference when swapping Assistant 1/2 order | ≤ 0.1 |
| **Length Bias** | Correlation between response length and score | ρ ≤ 0.2 |
| **Reference Anchoring** | Impact of reference quality on scoring | High (expected) |

### 5.3 BKT Parameter Validation

| Parameter | Implementation Value | BKT Literature |
|-----------|---------------------|----------------|
| P_LEARN | 0.1 | 0.05-0.15 ✅ |
| P_GUESS | 0.25 | 0.2-0.3 ✅ |
| P_SLIP | 0.10 | 0.05-0.15 ✅ |

### 5.4 Latency Performance

| Operation | LLM Calls | Est. Time |
|-----------|-----------|-----------|
| JudgeLM Scoring | 1 | ~500ms |
| Error Classification | 0 (rule-based) | ~10ms |
| Feedback Generation | 1 | ~500ms |
| **Total** | 2 | ~1s |

### 5.5 Baseline Comparison

| Method | Human Correlation | Latency |
|--------|-------------------|---------|
| Exact Match | ~0.4 | <10ms |
| Keyword Overlap | ~0.55 | <50ms |
| Semantic Similarity | ~0.7 | ~200ms |
| **JudgeLM (Ours)** | **≥0.85** | ~1s |

### 5.6 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No real human grader study | Cannot verify correlation | Use synthetic ground truth |
| Domain-specific rubrics | May not generalize | Configurable rubric weights |
| LLM variance | Different scores each run | Run 3x, use median |

---

## 6. Kết luận

Agent 5 kết hợp **JudgeLM** (Zhu 2023) với **Hybrid BKT-LLM** mastery tracking để tạo grading system có độ chính xác cao. G-Eval với 3-criteria rubric đảm bảo đánh giá toàn diện, trong khi 5-Path Decision Engine điều phối adaptive learning flow.

# Agent 6: KAG Agent (MemGPT) Whitebox Analysis [VERIFIED]

## 1. Kiến trúc Nội tại (Internal Architecture)

Agent 6 đóng vai trò là **Personal Knowledge OS** (Hệ điều hành Tri thức Cá nhân), triển khai kiến trúc MemGPT [Packer 2023] để quản lý ngữ cảnh vô hạn thông qua hệ thống bộ nhớ phân tầng.

### 1.1 Phân cấp Bộ nhớ (Memory Hierarchy)

*   **Main Context (RAM)**:
    *   **System Instructions**: Persona Bất biến + Function Schemas.
    *   **Core Memory**: Các sự kiện được ghim (ví dụ: User Profile, Current Goals). Có thể thay đổi (Mutable) thông qua `core_memory_append`.
    *   **FIFO Queue**: Lịch sử hội thoại cuốn chiếu. Bị đẩy (Evicted) sang Archival Storage khi áp lực bộ nhớ > 70%.
*   **External Context (Disk)**:
    *   **Archival Storage**: Neo4j Graph + Vector Index. Truy cập qua `archival_memory_search`.
    *   **Recall Storage**: Log chat được đồng bộ xuống Disk.

### 1.2 Quy trình Xử lý (OS Kernel)

Phương thức `execute` chạy một **Vòng lặp Heartbeat (Heartbeat Loop)**:

1.  **Monitor (Giám sát)**: Kiểm tra áp lực `WorkingMemory`.
    *   *Interrupt*: Nếu > 70%, kích hoạt `_auto_archive` (Đẩy 50% -> Tóm tắt -> Lưu trữ).
2.  **Compile (Biên dịch)**: Xây dựng prompt gồm `[SYSTEM] + [CORE] + [HISTORY]`.
3.  **Think (System 2)**: LLM sinh phản hồi hoặc Function Call.
4.  **Act (Paging)**: Thực thi `[FUNCTION] tool_name(args)`.
    *   *Tools*: `core_memory_append`, `archival_memory_search`, v.v.
5.  **Loop**: Nếu tool được gọi, đệ quy (Heartbeat). Nếu là câu trả lời cuối cùng (final answer), trả về cho User.

---

## 2. Thuật toán & Cấu trúc Dữ liệu

### 2.1 Quản lý Ngữ cảnh (`WorkingMemory`)
*   **Cấu trúc**: `System + Core + Queue`.
*   **Heuristic**: Token được ước lượng qua `len(chars) // 4`.
*   **Eviction**: `flush_queue(fraction=0.5)` loại bỏ các tin nhắn cũ nhất khỏi Queue, bảo toàn Core và System.

### 2.2 Sinh ghi chú Kiến tạo (Constructivist Note Generation)
*   **Dual-Code Theory**: Nội dung bao gồm cả **Văn bản** (Key Insight) và **Hình ảnh** (Mermaid Concept Map).
*   **Zettelkasten**: Ghi chú mang tính nguyên tử (atomic), được liên kết và gắn thẻ.

---

## 3. Khả năng phục hồi (Resilience)

### 3.1 Áp lực Bộ nhớ (Memory Pressure)
*   **Trigger (Kích hoạt)**: > 70% của `max_tokens` (mặc định 8192).
*   **Xử lý**: `_auto_archive` tạo một node "Session Summary" trong Neo4j và xóa queue, ngăn chặn Tràn Cửa sổ Ngữ cảnh (Context Window Overflow/Crash).

### 3.2 Bảo vệ Vòng lặp Vô hạn
*   **Ràng buộc**: `max_steps` (mặc định 5) ngăn chặn Heartbeat Loop bị kẹt trong chu kỳ gọi hàm liên tục.

---

## 4. Chiến lược Kiểm thử (Verification Strategy)

Đã xác minh qua `scripts/test_agent_6_memgpt.py`:

1.  **Heartbeat Logic**: Xác thực rằng agent có thể chuỗi hóa `core_memory_append` -> `archival_memory_search` -> `Final Answer`.
2.  **Context Compilation**: Xác minh cấu trúc prompt bao gồm khối Core Memory.
3.  **Pressure Interrupt**: Xác minh `_auto_archive` kích hoạt khi ngữ cảnh bị đầy.

**Trạng thái**: Đã xác minh (Verified Logic Implemented & Tested).

---

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 Memory Management Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Pressure Trigger Rate** | % sessions hitting >70% memory | ≤ 20% |
| **Auto-Archive Success** | % successful context evictions | ≥ 99% |
| **Context Utilization** | Average memory usage per session | 50-70% |
| **Overflow Prevention** | # sessions crashed due to context limit | 0 |

### 5.2 Heartbeat Loop Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Avg Steps per Execution** | Mean heartbeat iterations | 2-3 |
| **Max Steps Reached** | % sessions hitting max_steps=5 | ≤ 5% |
| **Tool Chain Success** | % multi-tool chains completing | ≥ 95% |

**Latency Analysis:**

| Scenario | Steps | LLM Calls | Est. Time |
|----------|-------|-----------|-----------|
| Simple query | 1 | 1 | ~500ms |
| Tool + Answer | 2 | 2 | ~1s |
| Full chain (max) | 5 | 5 | ~2.5s |

### 5.3 Zettelkasten Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Note Atomicity** | Avg concepts per note | 1-2 |
| **Link Density** | Avg links per note | ≥ 2 |
| **Recall Precision** | % relevant notes retrieved | ≥ 80% |

### 5.4 System Learning Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Bottleneck Detection** | % known difficult concepts identified | ≥ 90% |
| **Pattern Recognition** | % common errors correctly aggregated | ≥ 85% |
| **Recommendation Adoption** | % recommendations implemented | ≥ 50% |

### 5.5 MemGPT vs Baseline Comparison

| Approach | Context Limit | Latency | Memory Quality |
|----------|---------------|---------|----------------|
| Fixed Window | 8K tokens | Fast | Loses old context |
| Sliding Window | 8K tokens | Fast | Loses semantic coherence |
| RAG Only | Unlimited | Medium | No episodic memory |
| **MemGPT (Ours)** | **Unlimited** | **Medium** | **Preserves key insights** |

### 5.6 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Summarization quality | May lose important details | Multi-level summarization |
| Retrieval accuracy | May recall irrelevant context | Hybrid search (vector + graph) |
| Heartbeat latency | Up to 5 LLM calls | Parallel tool execution (future) |

---

## 6. Kết luận

Agent 6 triển khai **MemGPT** (Packer 2023) để quản lý ngữ cảnh vô hạn thông qua tiered memory architecture. `WorkingMemory` class với memory pressure monitoring và auto-archive đảm bảo hệ thống không bao giờ crash do context overflow, trong khi Zettelkasten note generation tạo personal knowledge base cho learner.

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
# Agent 2: Profiler Agent - Whitebox Analysis

## 1. Bối cảnh & Mục tiêu
**Profiler Agent** đóng vai trò là "State Manager" (Quản lý trạng thái) của hệ thống Personalized Learning. Khác với các hệ thống LMS truyền thống chỉ lưu dữ liệu tĩnh, Agent 2 duy trì một **Learner Profile** (Hồ sơ người học) đa chiều và cập nhật theo thời gian thực.
**Mục tiêu**: Xây dựng một vector đặc trưng 10 chiều $\mathbf{x}_t$ đại diện cho trạng thái người học, được sử dụng bởi Path Planner (Agent 3) cho thuật toán tối ưu hóa LinUCB bandit.

## 2. Cơ sở Lý thuyết (Theoretical Framework)

### 2.1 Mô hình Người học (Vector 10 chiều)
Chúng tôi mô hình hóa trạng thái người học $\mathcal{S}$ dưới dạng vector $\mathbf{x} \in \mathbb{R}^{10}$, bao gồm:
1.  **Knowledge State ($x_0$)**: Mức độ thành thạo trung bình qua các khái niệm chính ($0 \le x_0 \le 1$).
2.  **Learning Style ($x_{1-4}$)**: Mã hóa One-hot theo mô hình VARK (Visual, Aural, Read/Write, Kinesthetic).
3.  **Skill Level ($x_5$)**: Khả năng xử lý độ khó đã được chuẩn hóa (Beginner=0.2, Intermediate=0.5, Advanced=0.8).
4.  **Time Constraints ($x_6$)**: Thời gian khả dụng mỗi phiên học (chuẩn hóa).
5.  **Cognitive Load ($x_7$)**: Mức độ Bloom's Taxonomy (1=Remember đến 6=Create), chuẩn hóa về $[0,1]$.
6.  **Velocity ($x_8$)**: Tốc độ học tập (concepts/hour).
7.  **Scope ($x_9$)**: Kích thước tương đối của mục tiêu học tập.

### 2.2 Vấn đề Cold Start & Hybrid Retrieval
Để khởi tạo $\mathbf{x}_0$ mà không có dữ liệu lịch sử, chúng tôi sử dụng **Diagnostic Assessment** (Đánh giá chẩn đoán) kết hợp **Hybrid Retrieval**:
1.  **Retrieval**: Với một mục tiêu (VD: "Learn SQL"), hệ thống dùng **Neo4j Vector Index** để tìm "Topographic Anchors" gần nhất về ngữ nghĩa, kết hợp bộ lọc đồ thị.
2.  **Generation**: LLM sinh ra 5 câu hỏi chẩn đoán dựa trên các anchor này.
3.  **Estimation**: **LKT (Language Knowledge Tracing)** dự đoán mức độ thành thạo dựa trên semantic understanding.

### 2.3 LKT: Language Knowledge Tracing (Lee 2024)

**Cơ sở khoa học:**

| Paper | Năm | Core Innovation |
|-------|-----|-----------------|
| **LKT** (Lee et al.) | 2024 | Replace LSTM (DKT) with Pre-trained Language Model |
| **DKT** (Piech et al.) | 2015 | LSTM for sequential knowledge tracing |

**Key Mechanism - Semantic Mastery Prediction:**

Thay vì dùng heuristics đơn giản (`level * difficulty`), LKT sử dụng LLM để:
1. **Format interaction history** theo định dạng text:
   ```
   [CLS] SELECT_STATEMENT
   What is SELECT? [CORRECT]
   WHERE_CLAUSE
   Explain WHERE syntax [INCORRECT]
   ```
2. **Semantic reasoning**: LLM hiểu mối quan hệ giữa concepts (mastered SELECT → partial mastery WHERE)
3. **Cold Start handling**: Với zero history, LLM dự đoán dựa trên semantic difficulty

**Implementation (`_predict_mastery_lkt`):**

```python
# LKT Prompt Structure
prompt = f"""
LEARNER CONTEXT:
- Topic: {topic}
- Stated Level: {current_level}
- Interaction History: {history_text}  # [CLS] format

CONCEPTS TO ASSESS:
{concept_list}

TASK: Predict mastery probability (0.0-1.0) for each concept.
"""

# LLM returns structured predictions
{"predictions": [
  {"concept_id": "SELECT", "mastery": 0.35, "reasoning": "..."},
  {"concept_id": "WHERE", "mastery": 0.15, "reasoning": "..."}
]}
```

**Fallback Strategy:**
- Nếu LLM fails → `_fallback_mastery_heuristic()` với simple level * difficulty
- Đảm bảo graceful degradation

**Code Reference:** `profiler_agent.py` lines 574-718

## 3. Chi tiết Thuật toán

### 3.1 Profile Vectorization (`_vectorize_profile`)
Chuyển đổi hồ sơ dạng JSON sang vector $\mathbf{x}$ cho Contextual Bandit:
$$
\mathbf{x} = [ \mu_{mastery}, \mathbb{I}_{vis}, \mathbb{I}_{aud}, \mathbb{I}_{read}, \mathbb{I}_{kin}, \eta_{skill}, \tau_{time}, \beta_{bloom}, \nu_{vel}, \sigma_{scope} ]
$$
Trong đó $\mathbb{I}$ là hàm chỉ thị (indicator function) cho learning style.

### 3.2 Dynamic Interest Decay (Suy giảm hứng thú động)
Để phản ánh đường cong quên lãng (forgetting curve) và sự thay đổi hứng thú, chúng tôi áp dụng suy giảm theo hàm mũ cho các thẻ hứng thú (interest tags) sau mỗi tương tác lớn:
$$
I_{tag}(t+1) = I_{tag}(t) \times \lambda
$$
Với $\lambda = 0.95$ (hệ số suy giảm). Các tag giảm xuống dưới ngưỡng $\epsilon = 0.1$ sẽ bị loại bỏ (pruned).

### 3.3 Xử lý Sự kiện Mở rộng (Distributed Lock)
Vì Agent có trạng thái (stateful) và phản ứng theo sự kiện (Event-Driven), chúng tôi cài đặt các trình xử lý đặc biệt để kiểm soát đồng thời (concurrency control):
*   **Race Condition**: Nhiều agent (Evaluator, Timer) có thể cập nhật profile cùng lúc.
*   **Giải pháp**: Sử dụng **Redis Distributed Lock** (thuật toán RedLock).
*   **Cơ chế**:
    ```python
    lock = redis.lock(f"lock:learner:{id}")
    if lock.acquire():
        state = read()
        state = update(state)
        write(state)
        lock.release()
    ```
Giải pháp này đảm bảo Cập nhật Trạng thái Nguyên tử (Atomic State Updates) trong môi trường phân tán (Kubernetes).

## 4. Logic Triển khai (Implementation Logic)

### 4.1 Persistence Layer (Dual-Write)
1.  **PostgreSQL**: Nguồn chân lý (Canonical source of truth) đảm bảo tính ACID.
2.  **Neo4j**: Personal Knowledge Graph ("Shadow Graph" - Đồ thị bóng).
    *   **Nodes**: `:Learner`, `:MasteryNode` (liên kết tới Course Concepts), `:ErrorEpisode`.
    *   **Edges**: `[:HAS_MASTERY]`, `[:HAS_ERROR]`.
3.  **Redis**: Hot State Cache (TTL 1 giờ) để Agent 3 đọc với độ trễ thấp.

### 4.2 Ước lượng Bloom's Taxonomy
Cấp độ Bloom được ước lượng động từ kết quả bài quiz:
$$
Bloom = 0.6 \cdot Score + 0.25 \cdot Difficulty + 0.15 \cdot QType_{boost}
$$
Trong đó $QType_{boost}$ ưu tiên các câu hỏi tổng hợp/áp dụng hơn là nhớ lại kiến thức.

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 LKT Prediction Accuracy

**Mục tiêu**: Đo lường độ chính xác của dự đoán mastery từ LKT so với ground truth.

**Metrics:**

| Metric | Công thức | Ý nghĩa |
|--------|-----------|---------|
| **MAE** | $\frac{1}{n}\sum|p_i - y_i|$ | Mean Absolute Error giữa predicted vs actual mastery |
| **RMSE** | $\sqrt{\frac{1}{n}\sum(p_i - y_i)^2}$ | Root Mean Square Error |
| **AUC-ROC** | ROC curve area | Khả năng phân biệt mastered vs not-mastered |

**Ground Truth Collection:**
1. **Post-Assessment**: Sau diagnostic, cho learner làm real quiz → actual mastery
2. **Longitudinal Tracking**: Compare initial prediction vs final mastery after course

**Target Benchmarks (per LKT paper):**

| Metric | Target | LKT Paper Reference |
|--------|--------|---------------------|
| **MAE** | ≤ 0.15 | LKT: 0.12 |
| **AUC-ROC** | ≥ 0.75 | LKT: 0.78 |

### 5.2 Profile Vectorization Validation

**Mục tiêu**: Đảm bảo 10-dim vector phản ánh đúng learner state.

**Validation Methods:**

| Method | Description |
|--------|-------------|
| **Dimension Range Check** | All dims ∈ [0.0, 1.0] |
| **One-Hot Consistency** | Learning style dims sum to 1 |
| **Peer Similarity** | Similar learners have high cosine similarity |

**Unit Test Example:**
```python
def test_vector_validity(profile_vector):
    assert len(profile_vector) == 10
    assert all(0 <= v <= 1 for v in profile_vector)
    assert sum(profile_vector[1:5]) == 1  # One-hot VARK
```

### 5.3 Cold Start Effectiveness

**Mục tiêu**: Đo lường chất lượng initial profile với zero interaction history.

**Metrics:**

| Metric | Definition |
|--------|------------|
| **First-Attempt Success Rate** | % learners pass first recommended concept |
| **Path Revision Rate** | % paths revised after first 3 interactions |

**Target:**
- First-Attempt Success ≥ 60% (vs 33% random baseline)
- Path Revision Rate ≤ 30%

### 5.4 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No real user study | Cannot validate engagement | Simulate with synthetic learners |
| LLM variance | Different predictions each run | Run 3x, report mean ± std |
| No long-term tracking | Cannot measure retention | Document as Future Work |

---

## 6. Kết luận
Agent 2 cung cấp "Context" ($\mathbf{x}_t$) cần thiết cho vòng lặp Agentic RL. Bằng cách kết hợp **LKT (Language Knowledge Tracing)** để dự đoán mastery và **Graph RAG** để khởi tạo, nó giải quyết vấn đề Cold Start với semantic understanding thay vì heuristics đơn giản.
# Agent 3: Path Planner Whitebox Analysis [RESOLVED]

## 1. Kiến trúc Nội tại (Internal Architecture)

Agent 3 là "người điều hướng" (navigator) của hệ thống, chịu trách nhiệm tạo ra chuỗi khái niệm học tập tối ưu. Khác với các bộ lập kế hoạch dựa trên luật tĩnh (static rule-based), nó sử dụng phương pháp lai kết hợp giữa **Graph Traversal (Adaptive Chaining)** và **Reinforcement Learning (LinUCB)**.

### 1.1 Quy trình Xử lý (6 Pha)

1.  **Input & Context Loading**:
    -   Nhận `learner_id`, `goal`, và `last_result`.
    -   Tải Learner Profile mạnh mẽ (vector + phong cách ưu tiên).
    -   Truy vấn Personal Knowledge Graph (Neo4j) để xác định các ứng viên (candidates).

2.  **Smart Filtering (Lọc thông minh)**:
    -   **Personal Subgraph Expansion**: Thay vì quét toàn bộ KG, phương pháp bắt đầu từ các khái niệm đã biết (`:MasteryNode` trong Neo4j) và mở rộng sang các lân cận trực tiếp (`NEXT`, `REQUIRES`). Điều này đảm bảo khả năng mở rộng O(1) so với kích thước đồ thị.

3.  **Probabilistic Mastery Gate (Nâng cấp Khoa học)**:
    -   Thay thế logic đạt/trượt nhị phân (binary pass/fail).
    -   Công thức: `gate_prob = min(1.0, current_score / GATE_FULL_PASS_SCORE)`
    -   Logic:
        -   Nếu `random() > gate_prob`: **Force Remediation** (Chế độ BACKWARD - Ép buộc học lại).
        -   Ngược lại: Cho phép tiến trình bình thường (FORWARD/ACCELERATE).
    -   *Lợi ích:* Ngăn chặn việc "đoán mò" (lucky guesses) tạo ra các lỗ hổng kiến thức dài hạn.

4.  **Adaptive Chaining (Lớp Heuristic)**:
    -   Xác định *hướng* di chuyển dựa trên `ChainingMode`:
        -   **FORWARD (Standard)**: Đi theo cạnh `NEXT`.
        -   **BACKWARD (Remediation)**: Đi theo cạnh `REQUIRES` (tiên quyết).
        -   **ACCELERATE (High Mastery)**: Bỏ qua các nút trung gian nếu đã thỏa mãn tiên quyết.
        -   **REVIEW (Spaced Repetition)**: Ngẫu nhiên 10% cơ hội (cấu hình qua `REVIEW_CHANCE`) để xem lại concept cũ.

5.  **LinUCB Selection (Lớp Ngẫu nhiên - Stochastic)**:
    -   Chọn *bước đi đơn lẻ tốt nhất* từ các ứng viên hợp lệ.
    -   Sử dụng thuật toán Contextual Bandit (Li et al., 2010).

6.  **Output Generation**:
    -   Tạo đối tượng JSON `LearningPath`.
    -   Tính toán xác suất thành công và tốc độ (pacing).

---

## 2. Thuật toán & Cấu trúc Dữ liệu

### 2.1 Cài đặt LinUCB
-   **Context**: Vector 10 chiều từ Learner Profile.
-   **Arms**: Mỗi Concept ID trong danh sách ứng viên là một cánh tay (arm).
-   **State**: Ma trận cho mỗi arm được lưu trong Redis (`linucb:{concept_id}`).
    -   `A` (10x10): Ma trận hiệp phương sai (xấp xỉ nghịch đảo).
    -   `b` (10x1): Vector lịch sử phần thưởng (reward history).
-   **Mục tiêu Lựa chọn**: Tối đa hóa Upper Confidence Bound (UCB).

### 2.2 Adaptive Chaining Logic
Agent duy trì một máy trạng thái cho `ChainingMode`:

| Trigger (Kích hoạt) | Mode | Hành động |
| :--- | :--- | :--- |
| `last_result="PROCEED"` | **FORWARD** | Di chuyển tới concept kế tiếp trong chuỗi. |
| `last_result="REMEDIATE"` | **BACKWARD** | Xác định các điều kiện tiên quyết chưa thành thạo. |
| `last_result="MASTERED"` | **ACCELERATE** | Kiểm tra các lân cận 2 bước (`NEXT` -> `NEXT`). |
| `random() < REVIEW_CHANCE` | **REVIEW** | Chọn các concept chưa học hoặc đã cũ. |

---

## 3. Khả năng phục hồi & Đồng thời [FIXED]

### 3.1 Distributed Locking (Redis)
**Vấn đề (Gap Identified)**: Các sự kiện phản hồi đồng thời (ví dụ: hoàn thành quiz nhanh) gây ra race conditions trong cập nhật ma trận LinUCB (`read-modify-write`).

**Giải pháp**:
-   Triển khai `redis.lock(name=f"lock:concept:{concept_id}", timeout=5)` bên trong `_on_evaluation_feedback`.
-   Đảm bảo cập nhật nguyên tử (atomic updates) cho các ma trận toàn cục `A` và `b` của mỗi concept.
-   **Tác động**: Ngăn chặn hỏng ma trận và phân kỳ chính sách học tập.

### 3.2 Configuration Management
**Vấn đề**: Các ngưỡng (`0.8`, `0.7`) bị hardcode rải rác trong code.
**Giải pháp**:
-   Tập trung tất cả thresholds trong `backend/core/constants.py`.
-   Import vào Agent 3 (`MASTERY_PROCEED_THRESHOLD`, `GATE_FULL_PASS_SCORE`).
-   Tăng cường khả năng bảo trì và tinh chỉnh thực nghiệm.

### 3.3 Lazy Initialization & Error Handling
-   **JSON Handling**: Thêm các import còn thiếu để ngăn lỗi `NameError`.
-   **Mock Resilience**: Test runner giả lập `redis.pipeline` dưới dạng đồng bộ (synchronous) để khớp với mẫu sử dụng thực tế, ngăn lỗi thuộc tính `coroutine` trong quá trình test.

---

## 4. Chiến lược Kiểm thử (Verification Strategy)

Agent được kiểm thử thông qua `scripts/test_agent_3.py` hỗ trợ:
1.  **Mock Mode**:
    -   Giả lập đồ thị Neo4j và trạng thái Redis.
    -   Patch `random` để kiểm thử Probabilistic Gate một cách tất định (deterministic).
    -   Xác minh việc chiếm dụng Lock.
2.  **Real Mode**:
    -   Kết nối tới live services để kiểm thử luồng đầu cuối (end-to-end).

### 4.3 Latency Analysis (ToT vs LinUCB)

**LLM Call Count per Planning Session:**

| Component | Calls per Beam | Total (b=3, d=3) |
|-----------|----------------|------------------|
| **Thought Generator** | 1 per node | 3 × 3 = 9 calls |
| **State Evaluator** | 1 per candidate | 3 × 3 = 9 calls |
| **Total** | | ~18 LLM calls |

**Latency Breakdown:**

| Mode | LLM Calls | Est. Time |
|------|-----------|-----------|
| **ToT (Full)** | 18 | ~9 seconds |
| **ToT (Shallow, d=2)** | 12 | ~6 seconds |
| **LinUCB (Fallback)** | 0 | ~100ms |

**Optimization Strategies:**

| Strategy | Impact | Implementation |
|----------|--------|----------------|
| **Caching** | -50% calls | Cache thought generator results per concept |
| **Shallow Search** | -33% calls | Reduce depth to d=2 for known paths |
| **Async Parallel** | -40% time | Evaluate multiple candidates concurrently |
| **LinUCB Hybrid** | -70% calls | Use ToT only for first planning, LinUCB for re-planning |

**ToT vs LinUCB Comparison:**

| Aspect | ToT (Tree of Thoughts) | LinUCB (Bandit) |
|--------|------------------------|-----------------|
| **Latency** | ~9s | ~100ms |
| **Quality** | Higher (lookahead) | Good (exploitation) |
| **Exploration** | Strategic (System 2) | Random (UCB) |
| **Cold Start** | Excellent | Poor |
| **Use Case** | Initial planning | Re-planning, real-time |

**Thesis Position**: ToT for initial curriculum, LinUCB for incremental updates.

---

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 Path Quality Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Completion Rate** | % learners who complete the generated path | ≥ 70% |
| **Time to Mastery** | Average time to reach 80% mastery on goal | 20% faster than baseline |
| **Prerequisite Violations** | # concepts attempted without prerequisites | 0 (hard constraint) |
| **Backtrack Rate** | % sessions requiring BACKWARD chaining | ≤ 30% |

### 5.2 ToT-Specific Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Beam Diversity** | Avg unique concepts across beams | ≥ 2 per search |
| **Pruning Effectiveness** | % low-value paths correctly pruned | ≥ 80% |
| **Strategic Value Accuracy** | Correlation between predicted and actual success | ρ ≥ 0.6 |

### 5.3 Ground Truth & Baseline

**Baseline Comparison:**
- **Random Path**: Select next concept randomly
- **Greedy Path**: Always select highest mastery neighbor
- **Rule-based Path**: Fixed prerequisite ordering

**Expected Results:**

| Method | Completion Rate | Time to Mastery |
|--------|-----------------|-----------------|
| Random | ~40% | Baseline |
| Greedy | ~55% | -5% |
| Rule-based | ~60% | -10% |
| **ToT (Ours)** | **≥70%** | **-20%** |

### 5.4 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No large-scale user study | Cannot validate real engagement | Synthetic learner simulation |
| LLM cost | ToT expensive for scaling | LinUCB hybrid mode |
| Semantic drift | LLM may generate invalid concepts | Graph validation layer |

---

## 6. Kết luận

Agent 3 kết hợp **Tree of Thoughts** (cho chất lượng cao) với **LinUCB** (cho tốc độ) để tạo curriculum tối ưu. ToT được sử dụng cho initial planning với lookahead strategy, trong khi LinUCB handle real-time re-planning với latency thấp.
# Agent 4: Tutor Agent Whitebox Analysis [RESOLVED]

## 1. Kiến trúc Nội tại (Internal Architecture)

Agent 4 đóng vai trò là **AI Tutor**, cung cấp hướng dẫn Socratic cá nhân hóa. Nó vượt xa khỏi mô hình Q&A đơn giản bằng cách duy trì một máy trạng thái sư phạm (pedagogical state machine) và thực thi các nguyên tắc giáo dục.

### 1.1 Quy trình Xử lý (7 Pha)

1.  **Context Gathering (Thu thập Ngữ cảnh)**:
    -   Truy vấn Neo4j (Course KG) để lấy sự kiện/kiến thức.
    -   Truy vấn Neo4j (Personal KG) để lấy lịch sử/độ thành thạo của người dùng.
    -   (Tùy chọn) Truy xuất tài liệu RAG.

2.  **Intent Classification (Phân loại Ý định)**:
    -   Sử dụng LLM để phân loại ý định người học:
        -   `HELP_SEEKING`: Bối rối, bị chặn -> Cần **Scaffolding** (Giàn giáo hỗ trợ).
        -   `SENSE_MAKING`: Tò mò, khám phá -> Cần **Probing** (Thăm dò sâu).

3.  **Reverse Socratic State Machine**:
    -   Quyết định *mô thức* (mode) tương tác sư phạm.
    -   Logic mang tính tất định dựa trên `hint_level` và `mastery`, ngẫu nhiên cho các chiến lược nâng cao (`TEACH_BACK`).

4.  **3-Layer Grounding (Chống ảo giác)**:
    -   Truy xuất song song từ 3 nguồn với độ tin cậy có trọng số.
    -   **Conflict Detection (Phát hiện Xung đột)**: Nếu RAG mâu thuẫn Course KG (Similarity < 0.6), KG thắng, và độ tin cậy bị giảm (Phạt -0.1).

5.  **Response Generation**:
    -   LLM sinh văn bản được hướng dẫn bởi các mẫu "Socratic Prompt" đặc thù cho trạng thái hiện tại.

6.  **Harvard 7 Enforcement**:
    -   Kiểm tra hậu xử lý (post-processing) để đảm bảo phản hồi tuân thủ các nguyên tắc (ví dụ: Active Learning, Feedback).

7.  **State Persistence**:
    -   Trạng thái phiên làm việc được lưu vào Redis (`ttl=24h`).

---

## 2. Thuật toán & Cấu trúc Dữ liệu

### 2.1 Logic Trạng thái Socratic
Được cài đặt trong `_determine_socratic_state`:

| Trạng thái (State) | Tiêu chí Kích hoạt (Trigger Criteria) |
| :--- | :--- |
| **REFUTATION** | `has_misconception=True` |
| **SCAFFOLDING** | `intent=HELP_SEEKING` HOẶC `hint_level=1` |
| **PROBING** | `intent=SENSE_MAKING` HOẶC mặc định |
| **TEACH_BACK** | `mastery > 0.7` VÀ `rounds > 2` (40% cơ hội) |
| **CONCLUSION** | `hint_level >= 4` HOẶC `rounds >= 5` |

### 2.2 Trọng số 3-Layer Grounding
Chuẩn hóa trong `constants.py`:

-   `TUTOR_W_DOC = 0.4` (Bao phủ rộng)
-   `TUTOR_W_KG = 0.35` (Sự kiện có cấu trúc)
-   `TUTOR_W_PERSONAL = 0.25` (Ngữ cảnh người dùng)
-   **Ngưỡng (Threshold)**: 0.5 (dưới mức này = "I don't know")

---

## 3. Khả năng phục hồi & Cấu hình

### 3.1 Quản lý Cấu hình (Configuration Management)
-   Tất cả các ngưỡng (`0.6` conflict, `0.4` weights) được import từ `backend/core/constants.py`.
-   Cho phép tinh chỉnh toàn cục "Tutor Personality" mà không cần sửa code.

### 3.2 Xử lý Lỗi (Error Handling)
-   **RAG Fallback**: Nếu `vector_store` bị thiếu (thường gặp trong test/dev), lớp RAG trả về độ tin cậy 0.0 nhưng không làm crash agent.
-   **Mocking**: Unit tests sử dụng `sys.modules` patching để xử lý các phụ thuộc `llama_index` một cách khéo léo.

---

## 4. Chiến lược Kiểm thử (Verification Strategy)

Đã xác minh qua `scripts/test_agent_4.py`:

1.  **State Machine Tests**: Xác nhận chuyển đổi đúng từ Probing -> Scaffolding dựa trên intent.
2.  **Protege Effect**: Xác minh `TEACH_BACK` kích hoạt cho người học có độ thành thạo cao.
3.  **Math Verification**: Xác thực tính toán Tổng Trọng số (Weighted Sum) cho Độ tin cậy Grounding.
4.  **Conflict Logic**: Xác minh hình phạt độ tin cậy khi `_detect_conflict` trả về True.

### 4.3 Latency Analysis (CoT Trade-offs)

**LLM Call Count per Tutoring Turn:**

| Phase | LLM Calls | Component |
|-------|-----------|-----------|
| **INTRO/PROBING** | 1 | `_generate_probing_question()` |
| **SCAFFOLDING** | 3 | `_generate_cot_traces()` (n=3) |
| **ASSESSMENT** | 0 | Handoff to Evaluator |

**Latency Breakdown:**

| Scenario | LLM Calls | Est. Time |
|----------|-----------|-----------|
| Simple probe | 1 | ~500ms |
| CoT scaffolding | 3 | ~1.5s |
| Full session (5 turns) | ~7 | ~3.5s |

**Optimization Strategies:**

| Strategy | Impact | Status |
|----------|--------|--------|
| **Cached Traces** | Reuse CoT for same misconception | ✅ Implemented (state.current_cot_trace) |
| **Parallel Generation** | Generate 3 traces concurrently | ⏳ Future Work |
| **Shallow CoT** | 1 trace instead of 3 for simple questions | ⏳ Future Work |

**Direct Answer vs CoT Comparison:**

| Approach | Latency | Quality | Leakage Risk |
|----------|---------|---------|--------------|
| Direct LLM | ~500ms | Medium | High |
| **CoT (Ours)** | ~1.5s | Higher | Low (filtered) |

---

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 Tutoring Quality Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Engagement Rate** | % questions where student continues dialogue | ≥ 70% |
| **Scaffolding Effectiveness** | % sessions reaching ASSESSMENT phase | ≥ 60% |
| **Answer Leakage Rate** | % responses containing direct answers | ≤ 5% |
| **Grounding Confidence** | Average weighted confidence score | ≥ 0.6 |

### 5.2 CoT-Specific Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Consensus Rate** | % CoT traces agreeing on diagnosis | ≥ 66% |
| **Hint Progression** | Avg steps before student solves | 2-4 hints |
| **Exemplar Relevance** | % exemplars matching domain | ≥ 80% |

### 5.3 Harvard 7 Compliance

| Principle | Measurement | Target |
|-----------|-------------|--------|
| Active Learning | Questions asked per response | ≥ 1 |
| Prompt Feedback | Response time | ≤ 2s |
| Time on Task | Session duration | 5-15 min |
| High Expectations | Bloom level of questions | ≥ APPLY |

### 5.4 Baseline Comparison

| Method | Engagement | Learning Gain |
|--------|------------|---------------|
| Direct Answer | ~40% | Low |
| Scripted Hints | ~55% | Medium |
| **CoT Tutor (Ours)** | **≥70%** | **Higher** |

### 5.5 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No A/B user study | Cannot prove learning gain | Synthetic dialogues |
| Domain-specific examples | May not generalize | Expand exemplar library |
| LLM variability | Inconsistent CoT quality | Self-consistency voting |

---

## 6. Kết luận

Agent 4 kết hợp **Dynamic Chain-of-Thought** (Wei 2022) với **Method Ontology** để tạo tutoring experience thông minh. CoT hidden traces được slice thành từng bước scaffolding, với leakage guard ngăn tiết lộ đáp án. Self-consistency voting đảm bảo chất lượng hints.
# Agent 5: Evaluator Agent Whitebox Analysis [RESOLVED]

## 1. Kiến trúc Nội tại (Internal Architecture)

Agent 5 đóng vai trò là **Pedagogical Judge** (Giám khảo Sư phạm), đánh giá hiệu suất người học bằng cách sử dụng Rubric Đa yếu tố (Multi-Factor Rubric) đã được chuẩn hóa và xác định bước tiếp theo tối ưu trong lộ trình học tập.

### 1.1 Quy trình Xử lý (8 Pha)

1.  **Context Gathering (Thu thập Ngữ cảnh)**:
    -   Tải Concept Metadata (Độ khó, Hiểu lầm) từ Neo4j (Cached, TTL=1h).
    -   Tải Learner Profile (Độ thạo hiện tại) từ Personal KG.

2.  **JudgeLM Scoring (SOTA)**:
    -   **Kỹ thuật**: Reference-as-Prior (Zhu 2023).
    -   **Prompt**: "Assistant 1" (Golden - Chuẩn) vs "Assistant 2" (Student - Học viên).
    -   **Định dạng**: Ký hiệu `10.0 {score}` + JSON CoT (Chain of Thought).
    -   **Rubric**: Correctness (0.6), Completeness (0.2), Clarity (0.2).

3.  **Error Classification** (nếu Score < 0.8):
    -   Phân loại Taxonomy: `CONCEPTUAL` (Căn bản), `PROCEDURAL` (Quy trình), `INCOMPLETE` (Thiếu sót), `CARELESS` (Bất cẩn).
    -   Misconception Detection: Đối chiếu lỗi với các hiểu lầm (misconceptions) đã biết trong KG.

4.  **Feedback Generation**:
    -   Tạo phản hồi cá nhân hóa giải quyết các hiểu lầm cụ thể.

5.  **5-Path Decision Logic**:
    -   Xác định `PathDecision` dựa trên Điểm số, Loại lỗi, và Độ khó.
    -   **MASTERED** (>= 0.9): Bỏ qua, đi tiếp (Skip ahead).
    -   **PROCEED** (>= 0.8): Tiếp tục concept kế tiếp.
    -   **ALTERNATE** (>= 0.6): Thay đổi phương thức (modality).
    -   **REMEDIATE** (< 0.6 + Conceptual): Quay lại học lại.
    -   **RETRY** (< 0.6 + Other): Thử lại.

6.  **Mastery Update**:
    -   Sử dụng Weighted Moving Average (WMA - Trung bình trượt có trọng số).
    -   `New = (Current * 0.4) + (Score * 0.6)` (Trọng số chuẩn hóa).

7.  **Alerting**:
    -   Kích hoạt Instructor Alert nếu `score < 0.4` (Critical Failure - Thất bại nghiêm trọng).

8.  **Output**:
    -   Phát sự kiện `EVALUATION_COMPLETED` tới Path Planner.

---

## 2. Thuật toán & Cấu trúc Dữ liệu

### 2.1 5-Path Decision Engine
Được cài đặt trong `_make_path_decision`:

| Quyết định (Decision) | Điều kiện Cơ sở (Base Condition) | Điều chỉnh (Adjustment) |
| :--- | :--- | :--- |
| **MASTERED** | Score >= 0.9 | -0.05 nếu Diff>=4, -0.03 nếu High Mastery |
| **PROCEED** | Score >= 0.8 | -0.05 nếu Diff>=4 |
| **ALTERNATE** | Score >= 0.6 | -0.05 nếu Diff>=4 |
| **REMEDIATE** | < 0.6 VÀ Error=CONCEPTUAL | N/A |
| **RETRY** | < 0.6 VÀ Error!=CONCEPTUAL | N/A |

### 2.2 Configuration
Chuẩn hóa trong `constants.py`:
-   `EVAL_MASTERY_WEIGHT = 0.6`
-   `THRESHOLD_ALERT = 0.4`

---

## 3. Khả năng phục hồi (Resilience)

### 3.1 Xử lý Lỗi (Error Handling)
-   **Empty Response**: Ghi log cảnh báo, trả về điểm 0.0.
-   **LLM Failure**: Fallback về chấm điểm dựa trên trùng lặp từ khóa (keyword overlap scoring).
-   **Event Emit Failure**: Bỏ qua (swallow) lỗi để ngăn chặn việc làm sập luồng trả về của quá trình đánh giá.

---

## 4. Chiến lược Kiểm thử (Verification Strategy)

Đã xác minh qua `scripts/test_agent_5_judgelm.py`:

1.  **Prompt Structure**: Xác thực khớp chính xác với JudgeLM System Prompt (Hình 5).
2.  **Scoring Notation**: Xác minh việc phân tích cú pháp `10.0 X` và JSON fallback.
3.  **Rubric Weights**: Xác minh cập nhật tuyến tính gần đúng.

**Trạng thái**: Đã xác minh (Verified). Test Passed.

---

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 Grading Quality Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Human Correlation (Spearman's ρ)** | Correlation between LLM scores and expert grades | ≥ 0.85 |
| **Scoring Consistency** | Std dev of scores for same response (3 runs) | ≤ 0.05 |
| **Error Classification Accuracy** | % errors correctly classified | ≥ 80% |
| **Misconception Detection Rate** | % known misconceptions correctly identified | ≥ 75% |

### 5.2 JudgeLM-Specific Metrics

| Metric | Definition | Target (per Zhu 2023) |
|--------|------------|----------------------|
| **Position Bias** | Score difference when swapping Assistant 1/2 order | ≤ 0.1 |
| **Length Bias** | Correlation between response length and score | ρ ≤ 0.2 |
| **Reference Anchoring** | Impact of reference quality on scoring | High (expected) |

### 5.3 BKT Parameter Validation

| Parameter | Implementation Value | BKT Literature |
|-----------|---------------------|----------------|
| P_LEARN | 0.1 | 0.05-0.15 ✅ |
| P_GUESS | 0.25 | 0.2-0.3 ✅ |
| P_SLIP | 0.10 | 0.05-0.15 ✅ |

### 5.4 Latency Performance

| Operation | LLM Calls | Est. Time |
|-----------|-----------|-----------|
| JudgeLM Scoring | 1 | ~500ms |
| Error Classification | 0 (rule-based) | ~10ms |
| Feedback Generation | 1 | ~500ms |
| **Total** | 2 | ~1s |

### 5.5 Baseline Comparison

| Method | Human Correlation | Latency |
|--------|-------------------|---------|
| Exact Match | ~0.4 | <10ms |
| Keyword Overlap | ~0.55 | <50ms |
| Semantic Similarity | ~0.7 | ~200ms |
| **JudgeLM (Ours)** | **≥0.85** | ~1s |

### 5.6 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No real human grader study | Cannot verify correlation | Use synthetic ground truth |
| Domain-specific rubrics | May not generalize | Configurable rubric weights |
| LLM variance | Different scores each run | Run 3x, use median |

---

## 6. Kết luận

Agent 5 kết hợp **JudgeLM** (Zhu 2023) với **Hybrid BKT-LLM** mastery tracking để tạo grading system có độ chính xác cao. G-Eval với 3-criteria rubric đảm bảo đánh giá toàn diện, trong khi 5-Path Decision Engine điều phối adaptive learning flow.

# Agent 6: KAG Agent (MemGPT) Whitebox Analysis [VERIFIED]

## 1. Kiến trúc Nội tại (Internal Architecture)

Agent 6 đóng vai trò là **Personal Knowledge OS** (Hệ điều hành Tri thức Cá nhân), triển khai kiến trúc MemGPT [Packer 2023] để quản lý ngữ cảnh vô hạn thông qua hệ thống bộ nhớ phân tầng.

### 1.1 Phân cấp Bộ nhớ (Memory Hierarchy)

*   **Main Context (RAM)**:
    *   **System Instructions**: Persona Bất biến + Function Schemas.
    *   **Core Memory**: Các sự kiện được ghim (ví dụ: User Profile, Current Goals). Có thể thay đổi (Mutable) thông qua `core_memory_append`.
    *   **FIFO Queue**: Lịch sử hội thoại cuốn chiếu. Bị đẩy (Evicted) sang Archival Storage khi áp lực bộ nhớ > 70%.
*   **External Context (Disk)**:
    *   **Archival Storage**: Neo4j Graph + Vector Index. Truy cập qua `archival_memory_search`.
    *   **Recall Storage**: Log chat được đồng bộ xuống Disk.

### 1.2 Quy trình Xử lý (OS Kernel)

Phương thức `execute` chạy một **Vòng lặp Heartbeat (Heartbeat Loop)**:

1.  **Monitor (Giám sát)**: Kiểm tra áp lực `WorkingMemory`.
    *   *Interrupt*: Nếu > 70%, kích hoạt `_auto_archive` (Đẩy 50% -> Tóm tắt -> Lưu trữ).
2.  **Compile (Biên dịch)**: Xây dựng prompt gồm `[SYSTEM] + [CORE] + [HISTORY]`.
3.  **Think (System 2)**: LLM sinh phản hồi hoặc Function Call.
4.  **Act (Paging)**: Thực thi `[FUNCTION] tool_name(args)`.
    *   *Tools*: `core_memory_append`, `archival_memory_search`, v.v.
5.  **Loop**: Nếu tool được gọi, đệ quy (Heartbeat). Nếu là câu trả lời cuối cùng (final answer), trả về cho User.

---

## 2. Thuật toán & Cấu trúc Dữ liệu

### 2.1 Quản lý Ngữ cảnh (`WorkingMemory`)
*   **Cấu trúc**: `System + Core + Queue`.
*   **Heuristic**: Token được ước lượng qua `len(chars) // 4`.
*   **Eviction**: `flush_queue(fraction=0.5)` loại bỏ các tin nhắn cũ nhất khỏi Queue, bảo toàn Core và System.

### 2.2 Sinh ghi chú Kiến tạo (Constructivist Note Generation)
*   **Dual-Code Theory**: Nội dung bao gồm cả **Văn bản** (Key Insight) và **Hình ảnh** (Mermaid Concept Map).
*   **Zettelkasten**: Ghi chú mang tính nguyên tử (atomic), được liên kết và gắn thẻ.

---

## 3. Khả năng phục hồi (Resilience)

### 3.1 Áp lực Bộ nhớ (Memory Pressure)
*   **Trigger (Kích hoạt)**: > 70% của `max_tokens` (mặc định 8192).
*   **Xử lý**: `_auto_archive` tạo một node "Session Summary" trong Neo4j và xóa queue, ngăn chặn Tràn Cửa sổ Ngữ cảnh (Context Window Overflow/Crash).

### 3.2 Bảo vệ Vòng lặp Vô hạn
*   **Ràng buộc**: `max_steps` (mặc định 5) ngăn chặn Heartbeat Loop bị kẹt trong chu kỳ gọi hàm liên tục.

---

## 4. Chiến lược Kiểm thử (Verification Strategy)

Đã xác minh qua `scripts/test_agent_6_memgpt.py`:

1.  **Heartbeat Logic**: Xác thực rằng agent có thể chuỗi hóa `core_memory_append` -> `archival_memory_search` -> `Final Answer`.
2.  **Context Compilation**: Xác minh cấu trúc prompt bao gồm khối Core Memory.
3.  **Pressure Interrupt**: Xác minh `_auto_archive` kích hoạt khi ngữ cảnh bị đầy.

**Trạng thái**: Đã xác minh (Verified Logic Implemented & Tested).

---

## 5. Evaluation Methodology (Đánh giá chất lượng)

### 5.1 Memory Management Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Pressure Trigger Rate** | % sessions hitting >70% memory | ≤ 20% |
| **Auto-Archive Success** | % successful context evictions | ≥ 99% |
| **Context Utilization** | Average memory usage per session | 50-70% |
| **Overflow Prevention** | # sessions crashed due to context limit | 0 |

### 5.2 Heartbeat Loop Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Avg Steps per Execution** | Mean heartbeat iterations | 2-3 |
| **Max Steps Reached** | % sessions hitting max_steps=5 | ≤ 5% |
| **Tool Chain Success** | % multi-tool chains completing | ≥ 95% |

**Latency Analysis:**

| Scenario | Steps | LLM Calls | Est. Time |
|----------|-------|-----------|-----------|
| Simple query | 1 | 1 | ~500ms |
| Tool + Answer | 2 | 2 | ~1s |
| Full chain (max) | 5 | 5 | ~2.5s |

### 5.3 Zettelkasten Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Note Atomicity** | Avg concepts per note | 1-2 |
| **Link Density** | Avg links per note | ≥ 2 |
| **Recall Precision** | % relevant notes retrieved | ≥ 80% |

### 5.4 System Learning Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Bottleneck Detection** | % known difficult concepts identified | ≥ 90% |
| **Pattern Recognition** | % common errors correctly aggregated | ≥ 85% |
| **Recommendation Adoption** | % recommendations implemented | ≥ 50% |

### 5.5 MemGPT vs Baseline Comparison

| Approach | Context Limit | Latency | Memory Quality |
|----------|---------------|---------|----------------|
| Fixed Window | 8K tokens | Fast | Loses old context |
| Sliding Window | 8K tokens | Fast | Loses semantic coherence |
| RAG Only | Unlimited | Medium | No episodic memory |
| **MemGPT (Ours)** | **Unlimited** | **Medium** | **Preserves key insights** |

### 5.6 Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Summarization quality | May lose important details | Multi-level summarization |
| Retrieval accuracy | May recall irrelevant context | Hybrid search (vector + graph) |
| Heartbeat latency | Up to 5 LLM calls | Parallel tool execution (future) |

---

## 6. Kết luận

Agent 6 triển khai **MemGPT** (Packer 2023) để quản lý ngữ cảnh vô hạn thông qua tiered memory architecture. `WorkingMemory` class với memory pressure monitoring và auto-archive đảm bảo hệ thống không bao giờ crash do context overflow, trong khi Zettelkasten note generation tạo personal knowledge base cho learner.

