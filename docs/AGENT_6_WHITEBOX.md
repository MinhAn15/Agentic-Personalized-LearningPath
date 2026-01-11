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

