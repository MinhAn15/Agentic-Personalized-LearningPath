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

**Trạng thái**: Đã xác minh (Verified). Tất cả test cục bộ đã thông qua.
