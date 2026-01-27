# 03. LUỒNG ĐI CỦA DỮ LIỆU (THE DATA FLOW)

> **Mục tiêu:** "Giải ảo" sự ma thuật. Khi bạn bấm nút "Start Learning" trên màn hình, điều gì thực sự diễn ra bên dưới nắp ca-pô? Chúng ta sẽ lần theo dấu vết của một request.

---

## KỊCH BẢN: HỌC SINH BẤM NÚT "BẮT ĐẦU HỌC"

Giả sử người dùng (User A) đăng nhập và nói: *"Tôi muốn học Python cơ bản"*.

### BƯỚC 1: CỔNG GIAO TIẾP (API LAYER)
*   **File:** `backend/main.py` & `backend/api/agent_routes.py`
*   **Hành động:** Frontend gửi một request `POST /api/v1/agent/chat` với nội dung JSON: `{"message": "Tôi muốn học Python cơ bản", "learner_id": "UserA"}`.

*   **Tại sao quan trọng?** FastAPI nhận request này. Nó không xử lý ngay. Nó ném request này vào một **Hàng đợi sự kiện (Event Bus)** hoặc gọi trực tiếp Agent (tùy cấu hình). Trong thiết kế của chúng ta, nó gọi `orchestrator` (thường là Tutor hoặc Dispatcher).

### BƯỚC 2: BỘ NÃO THỨC GIẤC (AGENT DISPATCH & STATE CHECK)
*   **File:** `backend/agents/tutor_agent.py`
*   **Hoạt động:**
    1.  **Check State (Kiểm tra trạng thái):** Tutor Agent hỏi `CentralStateManager`: *"User A này là ai? Có đang học dở bài nào không?"*
    2.  **Redis Lookup:** State Manager tra trong Redis.
        *   Nếu là người mới -> Trả về `State: COLD_START`.
        *   Nếu là người cũ -> Trả về `State: LEARNING (Lesson 3)`.

### BƯỚC 3: LẬP KẾ HOẠCH (PATH PLANNER INTERVENTION)
Nếu là người mới hoặc vừa học xong một bài, Tutor sẽ không tự quyết. Nó gọi **Agent 3 (Path Planner)**.

*   **File:** `backend/agents/path_planner_agent.py`
*   **Luồng xử lý:**
    1.  **Retrieve Graph:** Agent 3 kéo bản đồ các khái niệm liên quan đến "Python" từ Neo4j.
    2.  **Run ToT (Tree of Thoughts):** Nó chạy mô phỏng 3 phương án.
    3.  **Decision:** Nó chọn phương án tốt nhất (ví dụ: "Dạy khái niệm `Variables` trước").
    4.  **Emit Event:** Nó bắn ra sự kiện `PATH_PLANNED` với payload: `{"next_concept": "Variables"}`.

### BƯỚC 4: SOẠN BÀI GIẢNG (RAG & CONTENT GENERATION)
Tutor Agent nhận được lệnh "Dạy `Variables`". Giờ nó cần nội dung.

*   **Hoạt động (Hybrid Retrieval):**
    1.  Nó gọi **Agent 6 (KAG/Knowledge Extraction)**.
    2.  Agent 6 tìm trong Vector DB: *"Định nghĩa biến trong Python là gì?"*.
    3.  Agent 6 tìm trong Neo4j: *"Biến có liên quan gì đến Bộ nhớ không?"*.
    4.  **Tổng hợp:** Agent 6 trộn 2 nguồn này lại thành một đoạn văn bản ngữ cảnh (Context).

### BƯỚC 5: PHẢN HỒI (FINAL RESPONSE)
Tutor Agent dùng GPT-4 để "xào nấu" ngữ cảnh trên thành một lời giảng dễ hiểu, mang phong cách Socratic (Hỏi gợi mở).

*   **Ví dụ:** Thay vì in ra định nghĩa, nó hỏi: *"Trong toán học bạn dùng x = 5. Vậy trong lập trình, bạn nghĩ làm sao để máy tính nhớ số 5 này?"*
*   **Return:** Gửi text này về cho Frontend hiển thị.

### BƯỚC 6: LƯU VẾT (DATA PERSISTENCE)
Sau khi tin nhắn được gửi đi, hệ thống không quên ngay.
1.  **LKT Update:** Agent 2 cập nhật vào Redis: *User A đang tương tác với Concept 'Variables'. Độ tập trung: Cao.*
2.  **Log:** Lưu lịch sử chat vào PostgreSQL để audit sau này.

---

## SƠ ĐỒ TỔNG QUÁT (TEXT VERSION)

```text
CLIENT (Frontend)
   |
   | (1. HTTP Request)
   v
API GATEWAY (FastAPI)
   |
   | (2. Dispatch)
   v
TUTOR AGENT <-----> (3. Check State) <-----> REDIS
   |
   | (4. Need Plan?)
   v
PATH PLANNER (Agent 3) <---> NEO4J (Graph)
   |
   | (5. Plan: "Teach Variables")
   v
TUTOR AGENT
   |
   | (6. Get Content)
   v
KAG AGENT <----> VECTOR DB + NEO4J
   |
   | (7. Context)
   v
LLM (GPT-4) ---> (8. Response Generation)
   |
   v
CLIENT (Display Message)
```
