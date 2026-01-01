# 🕵️ Whitebox Analysis: Agent 1 (Knowledge Extraction)

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

## 3. Process (Luồng xử lý chi tiết)

Pipeline của Agent 1 hoạt động theo mô hình **Parallel Semantic Processing**.

### 3.1 Giai đoạn 1: Semantic Chunking (Phân đoạn ngữ nghĩa)
*   **Mục tiêu**: Chia nhỏ văn bản dài thành các đoạn nhỏ có ý nghĩa trọn vẹn (không cắt giữa chừng câu hoặc ý).
*   **Phương pháp**: Sử dụng LLM để xác định ranh giới (Boundaries).
*   **Kết quả**: List các `SemanticChunk`.

### 3.2 Giai đoạn 2: Information Extraction (Trích xuất song song)
Đây là trái tim của Agent. Thay vì chạy tuần tự (Sequential), Agent sử dụng `asyncio.gather` để bắn nhiều request lên LLM cùng lúc.

**Code minh họa kiến trúc Semaphore:**
```python
# Semaphore giới hạn số lượng concurrent tasks
semaphore = asyncio.Semaphore(self.MAX_CONCURRENCY)

async def _process_with_limit(chunk):
    async with semaphore:
        return await self._process_single_chunk(chunk)

# Chạy song song tất cả các chunks
tasks = [_process_with_limit(chunk) for chunk in chunks]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Trong mỗi Chunk, quy trình 3 lớp (3-Layer Extraction) diễn ra:**
1.  **Layer 1 (Concepts)**: Tìm các thực thể chính (VD: "Polymorphism", "Foreign Key").
    *   *Kỹ thuật Stable ID*: Concept ID được tạo theo công thức `{domain}.{clean_name}`. VD: `sql.joins.inner`. Không còn phụ thuộc vào ngữ cảnh ngẫu nhiên của LLM.
2.  **Layer 2 (Relationships)**: Tìm quan hệ giữa các thực thể vừa tìm được (VD: `A IS_PREREQUISITE_OF B`).
3.  **Layer 3 (Metadata)**: Gán nhãn Bloom's Taxonomy (Understand, Apply) để phục vụ cho việc gợi ý bài tập sau này.

### 3.3 Giai đoạn 3: Entity Resolution (Hợp nhất thực thể)
*   **Vấn đề**: File A nói về "Inner Join", File B nói về "INNER JOIN". Nếu không xử lý, Graph sẽ có 2 nút riêng biệt.
*   **Giải pháp (Refined)**: Sử dụng **Fulltext Search** + **Vector Search**.
    1.  Agent query Neo4j Index để tìm các candidate có tên *gần giống* (`~0.8`).
    2.  So sánh Embedding vector của định nghĩa (Definition).
    3.  Nếu trùng khớp -> Merge vào node cũ (Canonical). Nếu mới -> Tạo node mới.

**Tối ưu hóa**: Thay vì load toàn bộ Graph vào RAM (O(N)), kỹ thuật Candidate Retrieval chỉ lấy 10-20 node liên quan (O(1)), giúp hệ thống scale lên hàng triệu concept vẫn mượt mà.

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

---

## 6. Kết luận (Dành cho phản biện luận văn)

Agent 1 không chỉ là một script gọi GPT-4. Nó là một **Engineering Pipeline** hoàn chỉnh giải quyết các vấn đề thực tế của ứng dụng LLM:
1.  **Chi phí & Tốc độ**: Nhờ Parallel Processing.
2.  **Chất lượng dữ liệu**: Nhờ Entity Resolution & Stable IDs.
3.  **Độ tin cậy**: Nhờ Idempotency & Partial Success handling.

Hệ thống sẵn sàng để scale cho khối lượng dữ liệu của một trường đại học.
