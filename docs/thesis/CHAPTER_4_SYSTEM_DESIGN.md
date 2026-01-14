# CHƯƠNG 4: THIẾT KẾ VÀ HIỆN THỰC HỆ THỐNG (SYSTEM DESIGN AND IMPLEMENTATION)

## 4.1 Tổng quan Kiến trúc Hệ thống (System Architecture Overview)

Hệ thống Agentic Personalized Learning Path được thiết kế dựa trên kiến trúc Multi-Agent, bao gồm 6 Agent chuyên biệt phối hợp với nhau để tạo ra trải nghiệm học tập cá nhân hóa toàn diện. Mỗi Agent đảm nhiệm một vai trò cụ thể trong chu trình học tập, từ việc xử lý tài liệu thô đến việc hướng dẫn và đánh giá người học.

### 4.1.1 Sơ đồ Luồng dữ liệu Tổng quát (High-Level Data Flow)

Dữ liệu di chuyển qua hệ thống theo quy trình khép kín:
1.  **Ingestion**: Tài liệu học tập được **Agent 1** trích xuất thành Knowledge Graph.
2.  **Profiling**: Người học tương tác với hệ thống, **Agent 2** xây dựng hồ sơ năng lực 10 chiều.
3.  **Planning**: Dựa trên hồ sơ và mục tiêu, **Agent 3** lập lộ trình học tập tối ưu.
4.  **Learning**: **Agent 4** hướng dẫn người học qua từng khái niệm bằng phương pháp Socratic.
5.  **Evaluation**: **Agent 5** đánh giá câu trả lời và cập nhật mức độ thành thạo.
6.  **Memory**: **Agent 6** lưu trữ tri thức cá nhân và quản lý ngữ cảnh dài hạn.

### 4.1.2 Các thành phần cốt lõi (Core Components)

| Agent | Vai trò (Role) | Công nghệ nền tảng (Base Technology) | Đóng góp mới (Novelty) |
|-------|----------------|--------------------------------------|-----------------------|
| 1 | **The Librarian** (Knowledge Extraction) | LightRAG (Guo 2024) | Global Theme Injection, 3-Layer Pipeline |
| 2 | **The Profiler** (State Manager) | Semantic LKT (Lee 2024) | Zero-shot LKT, 10-Dim Vector |
| 3 | **The Navigator** (Path Planner) | Tree of Thoughts (Yao 2023) | Hybrid ToT + LinUCB, Adaptive Chaining |
| 4 | **The Tutor** (Socratic Guide) | Chain-of-Thought (Wei 2022) | Dynamic CoT Scaffolding, Leakage Guard |
| 5 | **The Judge** (Evaluator) | JudgeLM (Zhu 2023) | Reference-as-Prior, 5-Path Decision |
| 6 | **The OS** (Personal Memory) | MemGPT (Packer 2023) | Pressure-Triggered Archive, Zettelkasten |

---

## 4.2 Agent 1: Knowledge Extraction Agent

Agent 1 đóng vai trò là "Thủ thư" (The Librarian), chịu trách nhiệm chuyển đổi tài liệu học tập thô (PDF, Text) thành cấu trúc Knowledge Graph có ngữ nghĩa phong phú.

### 4.2.1 Thiết kế Cấp cao (High-Level Design)

**Mẫu kiến trúc (Pattern):** Pipeline + Parallel Fan-Out
**Cơ sở khoa học:** LightRAG (Guo 2024) - Sử dụng Global Theme Injection để định hướng trích xuất.

**Quy trình xử lý (Data Flow):**
1.  **Chunking**: Phân đoạn văn bản (Sử dụng MultiDocFusion cho văn bản dài >10k tokens).
2.  **Parallel Extraction**: Trích xuất song song 3 lớp thông tin: Concepts (Khái niệm), Relationships (Quan hệ), Metadata (Metadata).
3.  **Entity Resolution**: Hợp nhất các thực thể trùng lặp sử dụng thuật toán 3-Way Similarity.
4.  **Persistence**: Lưu trữ vào Neo4j (Graph) và Redis (Registry).

**Điểm mới (New Contribution):**
*   **Global Theme Injection**: Tiêm ngữ cảnh toàn cục ("Domain") vào mọi prompt trích xuất, thay vì chỉ dùng khi truy vấn như LightRAG gốc.
*   **3-Layer Extraction**: Tách biệt trích xuất Concept (L1), Relationship (L2) và Metadata (L3) để tối ưu hóa độ chính xác.

### 4.2.2 Phân rã Kỹ thuật (Technical Decomposition)

Module chính `KnowledgeExtractionAgent` bao gồm các phương thức:
*   `execute()`: Orchestration pipeline chính, quản lý concurrency với `asyncio.Semaphore`.
*   `_extract_concepts_from_chunk()`: Trích xuất tên, mô tả mô đun học tập.
*   `_extract_relationships_from_chunk()`: Xác định quan hệ tiên quyết (PREREQUISITE_OF), liên quan (RELATED_TO).
*   `_entity_resolution()`: Giải quyết trùng lặp thực thể dựa trên tên (fuzzy), ngữ nghĩa (embedding) và ngữ cảnh.

### 4.2.3 Thiết kế Chi tiết (Low-Level Design)

**Thuật toán Entity Resolution (3-Way Similarity):**
Kết hợp 3 chỉ số với trọng số:
*   Semantic Similarity (Embedding Cosine): 60%
*   Structural Similarity (Jaccard Neighbors): 30%
*   Lexical Similarity (Fuzzywuzzy): 10%
Ngưỡng (Threshold): 0.85 để gộp node.

**Cơ chế Fail-Safe:**
*   Idempotency Check: Sử dụng SHA-256 hash của tài liệu để tránh xử lý lặp.
*   Partial Success: Cho phép pipeline tiếp tục ngay cả khi một số chunk bị lỗi (ghi nhận trạng thái PARTIAL_SUCCESS).

---

## 4.3 Agent 2: Profiler Agent

Agent 2 đóng vai trò là "Nhà quản lý trạng thái" (State Manager), xây dựng và duy trì hồ sơ năng lực của người học theo thời gian thực.

### 4.3.1 Thiết kế Cấp cao (High-Level Design)

**Mẫu kiến trúc (Pattern):** Event-Driven State Manager
**Cơ sở khoa học:** Semantic LKT (Lee 2024) - Sử dụng LLM để dự đoán mức độ thành thạo dựa trên ngữ nghĩa thay vì chỉ dựa vào ID câu hỏi.

**Quy trình xử lý (Data Flow):**
1.  **Intent Parsing**: Phân tích ý định người dùng (Học mới, Ôn tập, v.v.).
2.  **Hybrid Retrieval**: Tìm kiếm Goal Node trong KG sử dụng kết hợp Vector Search và Graph Traversal.
3.  **Diagnostic (Cold Start)**: Chạy bài kiểm tra chẩn đoán nếu chưa có dữ liệu (Sử dụng LKT để suy luận mastery).
4.  **Vectorization**: Tạo vector 10 chiều đại diện cho người học.
5.  **Dual-Write Persistence**: Ghi đồng thời vào PostgreSQL (Canonical), Neo4j (Graph), Redis (Cache).

**Điểm mới (New Contribution):**
*   **Zero-shot LKT**: Áp dụng LKT mà không cần fine-tuning model, sử dụng khả năng suy luận của LLM (Gemini).
*   **10-Dimensional Vector**: Mô hình hóa người học qua 10 chiều: [Mastery, V, A, R, K, Skill, Time, Bloom, Velocity, Scope] để phục vụ cho Agent 3 (LinUCB).

### 4.3.2 Phân rã Kỹ thuật (Technical Decomposition)

Module chính `ProfilerAgent` bao gồm:
*   `_parse_goal_with_intent()`: Trích xuất Topic, Level, Purpose từ ngôn ngữ tự nhiên.
*   `_predict_mastery_lkt()`: Lõi của LKT, dự đoán xác suất thành thạo các concept liên quan.
*   `_vectorize_profile()`: Chuyển đổi dữ liệu profile thành vector số học chuẩn hóa [0, 1].

### 4.3.3 Thiết kế Chi tiết (Low-Level Design)

**Quản lý Trạng thái Phân tán:**
*   **Redis Distributed Lock**: `lock:learner:{id}` để đảm bảo tính nhất quán khi có nhiều request đồng thời.
*   **Optimistic Locking**: Sử dụng `version` column trong PostgreSQL đ tránh ghi đè dữ liệu cũ.

**Cấu trúc Vector 10 chiều:**
1.  `dim_0`: Knowledge State (Average Mastery)
2-5. `dim_1-4`: Learning Style (VARK - Visual, Aural, Read/Write, Kinesthetic)
6.  `dim_5`: Skill Level (Beginner/Inter/Adv)
7.  `dim_6`: Time Constraint
8.  `dim_7`: Bloom Taxonomy Level Capability
9.  `dim_8`: Learning Velocity
10. `dim_9`: Topic Scope

---

## 4.4 Agent 3: Path Planner Agent

Agent 3 đóng vai trò là "Nhà điều hướng" (The Navigator), lập kế hoạch học tập tối ưu cho từng cá nhân.

### 4.4.1 Thiết kế Cấp cao (High-Level Design)

**Mẫu kiến trúc (Pattern):** Hybrid Decision Engine (ToT + LinUCB)
**Cơ sở khoa học:** Tree of Thoughts (Yao 2023) cho lập kế hoạch chiến lược và LinUCB (Li 2010) cho tối ưu hóa thích nghi.

**Quy trình xử lý (Data Flow):**
1.  **Context Loading**: Tải Profile Vector từ Agent 2 và Personal Subgraph từ Neo4j.
2.  **Smart Filtering**: Lọc các concept khả thi (Next Possible Concepts).
3.  **Algorithm Selection**:
    *   *First Planning*: Dùng **Tree of Thoughts (ToT)** với Beam Search (width=3, depth=3) để tìm lộ trình tối ưu toàn cục.
    *   *Re-planning*: Dùng **LinUCB** (Contextual Bandit) để chọn concept tiếp theo nhanh chóng dựa trên phản hồi.
4.  **Adaptive Chaining**: Chuỗi hóa các concept theo các chế độ: FORWARD, BACKWARD (Remediation), REVIEW, v.v.

**Điểm mới (New Contribution):**
*   **Hybrid ToT + LinUCB**: Kết hợp khả năng suy luận sâu của ToT với tốc độ của RL, giải quyết vấn đề độ trễ cao của ToT thuần túy.
*   **Probabilistic Mastery Gate**: Cơ chế cổng xác suất ngăn chặn việc "đoán mò" (lucky guess) để qua bài.

### 4.4.2 Phân rã Kỹ thuật (Technical Decomposition)

Module chính `PathPlannerAgent` bao gồm:
*   `_beam_search()`: Thực hiện tìm kiếm chùm cho ToT.
*   `_thought_generator()`: Sinh các bước tiếp theo khả thi (Thought Generation).
*   `_evaluate_path_viability()`: Đánh giá trng thái (State Evaluation).
*   `_on_evaluation_feedback()`: Cập nhật ma trận A, b của thuật toán LinUCB dựa trên kết quả học tập.

### 4.4.3 Thiết kế Chi tiết (Low-Level Design)

**Thuật toán ToT (Beam Search):**
*   **Thought Decomposition**: Sinh 3 concept tiếp theo khác nhau.
*   **State Evaluator**: "Mô phỏng mental" xem người học có khả năng thành công với lộ trình này không.
*   **Pruning**: Cắt bỏ các nhánh có điểm khả thi thấp.

**LinUCB State:**
Lưu trữ ma trận nghịch đảo $A^{-1}$ và vector $b$ trong Redis để cập nhật Online Learning w/o retrain.

---

## 4.5 Agent 4: Tutor Agent

Agent 4 đóng vai trò là "Gia sư Socratic" (The Tutor), hướng dẫn người học qua từng bước giải quyết vấn đề.

### 4.5.1 Thiết kế Cấp cao (High-Level Design)

**Mẫu kiến trúc (Pattern):** Pedagogical State Machine + Dynamic CoT
**Cơ sở khoa học:** Chain-of-Thought (Wei 2022) và Phương pháp Nghịch đảo Socratic.

**Quy trình xử lý (Data Flow):**
1.  **Context Gathering**: Thu thập ngữ cảnh từ 3 nguồn (3-Layer Grounding): RAG (Tài liệu), Course KG (Vị trí bài học), Personal KG (Lịch sử học).
2.  **Intent Classification**: Phân loại ý định (Help Seeking vs Sense Making).
3.  **Socratic State Machine**: Xác định trạng thái hội thoại: PROBING, SCAFFOLDING, REFUTATION...
4.  **CoT Generation**: Sinh chuỗi suy luận (Chain-of-Thought) nội bộ (n=3 traces).
5.  **Leakage Guard**: Cắt nhỏ CoT thành các gợi ý (scaffolding hints) và lọc bỏ câu trả lời trực tiếp.

**Điểm mới (New Contribution):**
*   **Dynamic CoT for Tutoring**: Sử dụng CoT để sinh ra quy trình giải, nhưng *không* hiển thị cho người học mà cắt nhỏ thành các câu hỏi gợi mở.
*   **Leakage Guard**: Bộ lọc Regex/Keyword đảm bảo Agent không bao giờ cho đáp án trực tiếp, tuân thủ nguyên tắc sư phạm.

### 4.5.2 Phân rã Kỹ thuật (Technical Decomposition)

Module chính `TutorAgent` bao gồm:
*   `_generate_cot_traces()`: Sinh nhiều luồng suy nghĩ cùng lúc.
*   `_check_consensus()`: Chọn luồng suy nghĩ tốt nhất (Self-Consistency).
*   `_slice_cot_trace()`: Chia luồng suy nghĩ thành các bước nhỏ.
*   `_extract_scaffold()`: Chuyển đổi bước giải thành câu hỏi gợi ý.

### 4.5.3 Thiết kế Chi tiết (Low-Level Design)

**Socratic State Machine:**
Duy trì trạng thái hội thoại trong Redis:
*   `hint_level`: Mức độ gợi ý hiện tại (1-5).
*   `current_cot_trace`: Luồng suy nghĩ đang theo đuổi.

**Harvard 7 Principles Enforcement:**
Một lớp hậu xử lý kiểm tra output của LLM xem có tuân thủ các nguyên tắc như "Encourage Active Learning" hay không (ví dụ: output phải chứa câu hỏi).

---

## 4.6 Agent 5: Evaluator Agent

Agent 5 đóng vai trò là "Thẩm phán" (The Judge), đánh giá chính xác mức độ hiểu bài của người học.

### 4.6.1 Thiết kế Cấp cao (High-Level Design)

**Mẫu kiến trúc (Pattern):** Pedagogical Judge w/ JudgeLM
**Cơ sở khoa học:** JudgeLM (Zhu 2023) - Mô hình tham chiếu (Reference-as-Prior).

**Quy trình xử lý (Data Flow):**
1.  **JudgeLM Scoring**: So sánh câu trả lời của học viên với "Golden Answer" từ KG.
2.  **Error Classification**: Phân loại lỗi: CONCEPTUAL (Sai kiến thức), PROCEDURAL (Sai quy trình), INCOMPLETE (Thiếu sót), CARELESS (Bất cẩn).
3.  **5-Path Decision**: Ra quyết định điều hướng: MASTERED, PROCEED, ALTERNATE (đổi cách giải thích), REMEDIATE (học lại), RETRY (thử lại).
4.  **Mastery Update**: Cập nhật điểm thành thạo sử dụng Weighted Moving Average.

**Điểm mới (New Contribution):**
*   **JudgeLM for Education**: Áp dụng kỹ thuật LLM-as-a-Judge vào chấm điểm bài tập tự luận/code.
*   **5-Path Decision Engine**: Thay vì chỉ Pass/Fail, hệ thống đưa ra 5 hướng đi khác nhau tùy thuộc vào loại lỗi và mức độ nghiêm trọng.

### 4.6.2 Phân rã Kỹ thuật (Technical Decomposition)

Module chính `EvaluatorAgent` bao gồm:
*   `_score_response()`: Chấm điểm thang 0-10.
*   `_classify_error()`: Gán nhãn loại lỗi.
*   `_make_path_decision()`: Logic cây quyết định.
*   `_update_learner_mastery()`: Tính toán lại mastery score.

### 4.6.3 Thiết kế Chi tiết (Low-Level Design)

**Mastery Update Algorithm (WMA):**
$$NewMastery = CurrentMastery \times (1 - \alpha) + Score \times \alpha$$
Với $\alpha = 0.6$ (Ưu tiên kết quả mới nhất nhưng vẫn giữ quán tính).

**Alert System:**
Nếu điểm số < 0.4 (Critical Failure), kích hoạt cảnh báo cho Instructor (hoặc hệ thống giám sát).

---

## 4.7 Agent 6: KAG Agent (PersonalOS)

Agent 6 đóng vai trò là "Hệ điều hành Tri thức Cá nhân" (Personal Knowledge OS), quản lý bộ nhớ dài hạn và tổng hợp tri thức.

### 4.7.1 Thiết kế Cấp cao (High-Level Design)

**Mẫu kiến trúc (Pattern):** Personal Knowledge OS with Tiered Memory
**Cơ sở khoa học:** MemGPT (Packer 2023) - Quản lý ngữ cảnh vô hạn và Zettelkasten.

**Quy trình xử lý (Data Flow):**
1.  **Heartbeat Loop**: Vòng lặp suy nghĩ đệ quy để quản lý bộ nhớ và công cụ.
2.  **Tiered Memory**:
    *   *Main Context (RAM)*: System Instruct + Core Memory (Pinned) + FIFO Queue.
    *   *External Context (Disk)*: Archival Storage (Neo4j) + Recall Storage.
3.  **Memory Pressure Check**: Nếu RAM > 70% → Kích hoạt **Auto-Archive**.
4.  **Zettelkasten Generation**: Tự động sinh ghi chú nguyên tử (Atomic Notes) và Concept Map từ phiên học.

**Điểm mới (New Contribution):**
*   **MemGPT for Education**: Áp dụng cơ chế phân tầng bộ nhớ cho ngữ cảnh học tập kéo dài (longitudinal learning).
*   **Pressure-Triggered Archive**: Tự động tóm tắt và đẩy kiến thức cũ xuống kho lưu trữ khi bộ nhớ đầy, thay vì cắt bỏ thô bạo.

### 4.7.2 Phân rã Kỹ thuật (Technical Decomposition)

Module chính `KAGAgent` bao gồm:
*   `execute()`: Heartbeat loop chính.
*   `_auto_archive()`: Xử lý tràn bộ nhớ.
*   `_generate_artifact()`: Tạo ghi chú Zettelkasten.
*   `WorkingMemory` Wrapper: Quản lý token count và cấu trúc prompt.

### 4.7.3 Thiết kế Chi tiết (Low-Level Design)

**Zettelkasten Note Structure:**
Mỗi ghi chú bao gồm:
*   Definition (Định nghĩa súc tích)
*   Personal Example (Ví dụ liên hệ bản thân)
*   Key Insight (điểm cốt lõi)
*   Links (Liên kết đến concept khác)
*   Mermaid Concept Map (Biểu đồ khái niệm)

**Heartbeat Logic:**
Sử dụng [FUNCTION] tags để Agent tự gọi hàm `core_memory_append` hoặc `archival_memory_search` trong quá trình suy nghĩ trước khi trả lời người dùng.

---

## 4.8 Tổng kết Hiệu năng và Khả năng Mở rộng (Scalability & Performance Summary)

### 4.8.1 Phân tích Độ trễ (Latency Analysis)

| Operation | Agent | Method | LLM Calls | Est. Latency |
|-----------|-------|--------|-----------|--------------|
| **Document Ingest** (20K tokens) | Agent 1 | Pipeline | ~30 | ~15s |
| **Profile Cold Start** | Agent 2 | LKT | 2-3 | ~2s |
| **Path Planning (First)** | Agent 3 | ToT | 18 | ~9s |
| **Path Re-planning** | Agent 3 | LinUCB | 0 | ~100ms |
| **Tutoring Response** | Agent 4 | CoT | 2-3 | ~1.5s |
| **Evaluation** | Agent 5 | JudgeLM | 2 | ~1s |
| **Memory Heartbeat** | Agent 6 | MemGPT | 2-5 | ~1-2.5s |

### 4.8.2 Chiến lược Mở rộng (Scalability Strategy)

1.  **Read Heavy (Agent 4, 2)**: Sử dụng Redis Caching và Neo4j Read Replicas.
2.  **Compute Heavy (Agent 1, 3)**: Sử dụng Asynchronous Processing (Celery/Kafka) cho tác vụ Ingest và Planning dài hơi.
3.  **Stateful Ops (Agent 6)**: Giới hạn độ dài FIFO queue và tối ưu hóa Auto-Archive frequency.

### 4.8.3 Kết luận

Hệ thống đạt được sự cân bằng giữa **Chất lượng Sư phạm** (thông qua các kỹ thuật suy luận sâu như ToT, CoT, LKT) và **Hiệu năng Hệ thống** (thông qua Caching, LinUCB, Vectorization). Các đóng góp mới về mặt kỹ thuật (Global Theme, 10-Dim Vector, Leakage Guard...) đã giải quyết được các thách thức đặc thù của miền giáo dục cá nhân hóa.
