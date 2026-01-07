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

**Trạng thái**: Đã xác minh (Verified). Tất cả mock tests đã thông qua.
