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
