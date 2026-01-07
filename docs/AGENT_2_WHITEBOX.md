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

### 2.2 Vấn đề Cold Start & Graph RAG
Để khởi tạo $\mathbf{x}_0$ mà không có dữ liệu lịch sử, chúng tôi sử dụng **Diagnostic Assessment** (Đánh giá chẩn đoán) kết hợp **Graph RAG**:
1.  **Retrieval**: Với một mục tiêu (VD: "Learn SQL"), hệ thống truy vấn Knowledge Graph để tìm "Topographic Anchors" - các concept có độ trung tâm (PageRank) cao.
2.  **Generation**: LLM sinh ra 5 câu hỏi chẩn đoán dựa trên các anchor này.
3.  **Estimation**: Câu trả lời của người dùng được chấm điểm để ước lượng mức độ thành thạo và kỹ năng ban đầu.

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

## 5. Kết luận
Agent 2 cung cấp "Context" ($\mathbf{x}_t$) cần thiết cho vòng lặp Agentic RL. Bằng cách kết hợp Graph RAG để khởi tạo và cập nhật theo sự kiện (Event-Driven) để tiến hóa, nó giải quyết vấn đề Cold Start trong khi vẫn duy trì khả năng phản hồi cao.
