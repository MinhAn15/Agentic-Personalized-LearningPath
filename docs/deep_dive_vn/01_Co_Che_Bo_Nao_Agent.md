# 01. CƠ CHẾ BỘ NÃO AGENT (THE BRAIN MECHANISM)

> **Mục tiêu:** Tài liệu này giải thích *tại sao* và *như thế nào* các Agent đưa ra quyết định. Không nói chung chung, chúng ta sẽ đi sâu vào từng dòng code (Logic).

---

## 1. AGENT 3 (PATH PLANNER) - "VỊ CHIẾN LƯỢC GIA KHẮC KHIỂT"

Đây là Agent quan trọng nhất, nơi diễn ra các quyết định "dạy cái gì tiếp theo".

### 1.1 Tại sao nó thông minh hơn thuật toán "If-Else"?
Bình thường, các hệ thống cũ dùng luật cứng: *Nếu học xong A -> Thì học B*.
Agent 3 dùng **Reinforcement Learning (Học tăng cường)**. Nó coi việc dạy học như một ván cờ vây.

**Cấu trúc não bộ (Code: `path_planner_agent.py`)**:
Nó có 2 hệ thống tư duy:
1.  **System 1 (Phản xạ nhanh):** Dùng thuật toán **LinUCB (Multi-Armed Bandit)**.
    *   *Khi nào dùng?* Khi hệ thống cần quyết định nhanh hoặc khi "bí" ý tưởng.
    *   *Cơ chế:* Nó lưu một bảng điểm `mab_stats` trong Redis. Concept nào từng giúp học sinh đạt điểm cao sẽ được ưu tiên chọn lại.
2.  **System 2 (Suy nghĩ sâu):** Dùng thuật toán **Tree of Thoughts (ToT)**.
    *   *Khi nào dùng?* Mặc định cho mọi bước đi quan trọng.

### 1.2 "Tree of Thoughts" hoạt động thế nào? (Chi tiết kỹ thuật)
Chúng ta không chọn bừa bài tiếp theo. Agent 3 thực hiện một quy trình **"Giả lập tương lai"** (Mental Simulation) gồm 3 bước:

1.  **Bước 1: Tạo ý tưởng (Thought Generation)**
    *   Nó hỏi LLM: *"Học sinh đang ở bài A. Hãy nghĩ ra 3 nước đi tiếp theo."*
    *   Kết quả trả về thường là:
        *   *Nước 1:* Ôn tập lại (Review).
        *   *Nước 2:* Học bài mới khó hơn (Challenge).
        *   *Nước 3:* Học bài bổ trợ (Scaffold).

2.  **Bước 2: Tìm kiếm chùm (Beam Search)**
    *   *Tham số:* `Beam Width = 3`, `Depth = 3`.
    *   Nghĩa là nó sẽ tưởng tượng xa 3 bước chân. Ví dụ: *Nếu dạy bài này -> Học sinh sẽ chán -> Bỏ học*. Nếu viễn cảnh này xấu, nó sẽ cắt bỏ nhánh đó ngay (Pruning).

3.  **Bước 3: Hàm thưởng (Reward Function $r_t$)**
    *   Đây là "la bàn" của Agent. Nó chấm điểm từng viễn cảnh dựa trên công thức toán học (Dòng 376 `path_planner_agent.py`):
    $$ Reward = (0.6 \times Score) + (0.4 \times Completion) - Penalty $$
    *   **Score:** Điểm số dự kiến học sinh đạt được (để tránh dạy quá khó).
    *   **Completion:** Khả năng học sinh học hết bài (để tránh dạy quá chán).
    *   **Penalty:** Hình phạt nếu dự đoán học sinh sẽ bỏ cuộc (Dropout).

---

## 2. AGENT 6 (KAG) - "BỘ NÃO CỦA HỆ ĐIỀU HÀNH"

KAG không chỉ là một con bot chat RAG. Nó được thiết kế theo kiến trúc **MemGPT**.

### 2.1 Tại sao cần MemGPT?
LLM (như GPT-4) có giới hạn bộ nhớ (Context Window). Nếu bạn chat 1000 câu, nó sẽ quên câu số 1.
KAG giải quyết việc này bằng cơ chế **"Phân tầng bộ nhớ"** (Memory Hierarchy), giống như RAM và Ổ cứng của máy tính.

### 2.2 Kiến trúc bộ nhớ (Code: `kag_agent.py`)

1.  **Working Memory (RAM):**
    *   Những gì đang diễn ra ngay lúc này.
    *   *Cơ chế:* Khi bộ nhớ đầy (Memory Pressure > 70%), KAG sẽ tự động kích hoạt hàm `_auto_archive`.

2.  **Archival Memory (Ổ cứng - Neo4j):**
    *   Nơi lưu trữ vĩnh viễn (Long-term storage).
    *   *Cơ chế:* KAG tóm tắt (Summarize) đoạn chat cũ và lưu vào Neo4j dưới dạng `NoteNode`.
    *   *Truy xuất:* Khi cần nhớ lại, nó chạy lệnh `_archival_memory_search` để tìm trong Neo4j.

### 2.3 Nhịp tim (Heartbeat Loop)
KAG không chỉ trả lời rồi ngủ. Nó có một vòng lặp sự sống (Heartbeat) trong hàm `execute`:
1.  **Check Interrupt:** "Bộ nhớ có đầy chưa?" -> Nếu đầy, dọn dẹp ngay.
2.  **Compile Context:** Gom tin nhắn mới + Ký ức cũ quan trọng.
3.  **Think:** Gọi LLM để suy nghĩ.
4.  **Act:** LLM có thể gọi hàm (Function Call) như `search_wiki` hoặc `save_note` trước khi trả lời người dùng.

---

## 3. AGENT 2 (PROFILER) - "BÁC SĨ TÂM LÝ"

### 3.1 Dò tìm trạng thái ẩn (Latent Vitals)
Làm sao biết học sinh đang "Chán" hay "Bối rối" mà không cần hỏi?
Agent 2 dùng mô hình **LKT (Language Knowledge Tracing)**.
*   Nó phân tích **thời gian phản hồi**: Trả lời quá nhanh -> Đoán mò (Guessing). Trả lời quá chậm -> Bế tắc (Stuck).
*   Nó phân tích **từ ngữ**: Dùng từ tiêu cực, câu ngắn cộc lốc -> Frustration.

### 3.2 Cập nhật hồ sơ
Mỗi khi học sinh làm xong một bài, Agent 2 sẽ cập nhật vector `mastery_level` trong Redis. Vector này chính là "tấm bản đồ năng lực" của học sinh, giúp Agent 3 biết đường mà đi.
