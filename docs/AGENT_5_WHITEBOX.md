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
