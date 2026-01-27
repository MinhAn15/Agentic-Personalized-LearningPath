# 00. CẨM NANG TOÀN TẬP: HỆ THỐNG AGENTIC PERSONALIZED LEARNING

> **Lời tựa:** Đây không phải là tài liệu kỹ thuật khô khan. Đây là câu chuyện về cách chúng ta dạy máy tính không chỉ "trả lời câu hỏi", mà là "dạy học".

---

## CHƯƠNG 1: KHỞI NGUỒN & TƯ DUY (PHILOSOPHY)

### 1.1 Tại sao chúng ta cần Graph (Đồ thị)?
Hãy tưởng tượng bạn bước vào một thư viện khổng lồ (Vector Database). Bạn tìm cuốn sách về "Đạo hàm". Người thủ thư (Vector Search) rất nhanh nhảu, ông ta chạy đi và gắp về cho bạn 10 cuốn sách có chữ "Đạo hàm" bìa.
Nhưng ông ta **mù tịt về logic**. Ông ta không biết rằng để hiểu Đạo hàm, bạn phải biết về "Giới hạn" (Limits) trước.
Đây chính là **"Vector Blind Spot" (Điểm mù của Vector)**. Các hệ thống RAG hiện nay chỉ tìm kiếm dựa trên sự "tương đồng câu từ" (Semantic Similarity), chứ không hiểu "quan hệ phụ thuộc" (Dependency).

**Giải pháp của chúng ta:**
Chúng ta trang bị cho người thủ thư một tấm bản đồ (Knowledge Graph - Neo4j). Trên tấm bản đồ đó, có một mũi tên đỏ nối từ `Giới hạn` -> `Đạo hàm`.
Khi bạn hỏi về Đạo hàm, hệ thống sẽ nhìn bản đồ và nói: *"Khoan đã, anh bạn này chưa học Giới hạn. Đừng dạy Đạo hàm vội, hãy dạy Giới hạn trước."*
Đó là sự khác biệt giữa một cái máy tìm kiếm (Search Engine) và một người gia sư (Tutor).

### 1.2 Sự khác biệt so với ChatGPT
*   **ChatGPT (LLM thuần túy):** Giống như một giáo sư thiên tài nhưng... đãng trí. Ông ta biết tất cả, nhưng không nhớ bạn là ai, bạn đã học gì hôm qua, và ông ta hay "chém gió" (hallucinate) nếu không biết câu trả lời.
*   **Hệ thống Agentic:** Là một **"Hội đồng Giáo dục"**. Chúng ta không để ông giáo sư LLM làm việc một mình. Chúng ta có người kiểm tra sách (Reader), người quản lý hồ sơ học sinh (Profiler), và người lên kế hoạch (Planner). LLM chỉ là *một phần* của bộ não, không phải là toàn bộ.

---

## CHƯƠNG 2: ĐỘI NGŨ AI (THE 6 AGENTS)

Hãy hình dung hệ thống của chúng ta như một trường Đại học số, nơi có 6 nhân viên mẫn cán đang làm việc ngày đêm:

### 1. Agent 1: Thủ Thư Khó Tính (Knowledge Extraction Agent)
*   **Nhiệm vụ:** Đọc sách (PDF/Docs) và sắp xếp tri thức.
*   **Tính cách:** Cực kỳ ngăn nắp. Khi đọc một đoạn văn, ông ta không chỉ copy paste. Ông ta xé nhỏ nó ra (Semantic Chunking) và vẽ các đường nối (Triples Extraction) để đưa vào kho lưu trữ.
*   **Vũ khí:** `Semantic Chunking` (cắt theo ý nghĩa, không cắt theo số từ) và `Relation Extraction`.

### 2. Agent 2: Giáo Viên Chủ Nhiệm (Profiler Agent)
*   **Nhiệm vụ:** Hiểu học sinh.
*   **Hoạt động:** Ông ta cầm một cuốn sổ học bạ (User Profile). Mọi câu bạn nói, mọi bài bạn làm đều được ghi lại.
*   **Siêu năng lực:** "Đọc tâm trí" (Latent Vitals). Dựa vào cách bạn chat, ông ta đoán được bạn đang Chán (Boredom) hay đang Bực bội (Frustration) để báo cho các Agent khác điều chỉnh.
*   **Công nghệ:** Language Knowledge Tracing (LKT) - Dùng xác suất thống kê để đoán xem bạn đã "ngộ" ra kiến thức chưa.

### 3. Agent 3: Chiến Lược Gia (Path Planner Agent)
*   **Nhiệm vụ:** Vẽ đường đi nước bước. Đây là "Bộ não" thực sự của hệ thống.
*   **Tư duy:** Không bao giờ chọn bừa. Ông ta dùng thuật toán **Tree of Thoughts (Cây Suy Ngẫm)**. Trước khi đưa ra một bài học, ông ta tưởng tượng ra 3 viễn cảnh tương lai.
    *   *Viễn cảnh A:* Dạy cái này, học sinh sẽ chán.
    *   *Viễn cảnh B:* Dạy cái kia, học sinh sẽ sốc vì khó.
    *   *Viễn cảnh C:* Ôn lại bài cũ một chút, rồi dạy cái mới. -> **Chọn C.**
*   **Mục tiêu:** Tối đa hóa niềm vui và kiến thức (Reward Function $r_t$).

### 4. Agent 4: Gia Sư Socratic (Tutor Agent)
*   **Nhiệm vụ:** Trò chuyện trực tiếp.
*   **Phương pháp:** Không bao giờ giảng bài thao thao bất tuyệt. Ông ta luôn hỏi ngược lại (Maieutics).
    *   *Học sinh:* "1 + 1 bằng mấy?"
    *   *Gia sư:* "Nếu bạn có 1 quả táo và thêm 1 quả nữa, bạn có gì?"
*   **Mục đích:** Kích thích tư duy phản biện (Critical Thinking).

### 5. Agent 5: Giám Khảo Nghiêm Minh (Evaluator Agent)
*   **Nhiệm vụ:** Chấm điểm.
*   **Tính cách:** Lạnh lùng, chính xác. Ông ta so sánh câu trả lời của bạn với "Đáp án chuẩn" (Ground Truth) trong kho dữ liệu.
*   **Bảo mật:** Ông ta cũng là người bảo vệ (Gatekeeper), chặn đứng các nỗ lực "hack" Prompt của người dùng.

### 6. Agent 6: Bộ Não Học Thuật (KAG Agent)
*   **Nhiệm vụ:** Cung cấp tài liệu tham khảo.
*   **Cơ chế:** **Hybrid Retrieval**. Ông ta dùng cả mắt thường (Vector Search - tìm chữ giống nhau) và não bộ (Graph Traversal - tìm ý nghĩa liên quan) để tổng hợp ra một bộ tài liệu hoàn chỉnh nhất cho Agent 4 sử dụng.

---

## CHƯƠNG 3: TRÁI TIM KỸ THUẬT (THE CORE TECH)

### 3.1 Graph RAG hoạt động ra sao?
Bình thường, RAG chỉ là: `Câu hỏi -> Vector DB -> Tài liệu`.
Của chúng ta là:
1.  **Nhìn:** Tìm các đoạn văn chứa từ khóa trong Vector DB.
2.  **Nghĩ:** Từ các từ khóa đó, tra trên bản đồ Neo4j xem chúng liên quan đến khái niệm nào khác (Prerequisite, Related_to).
3.  **Tổng hợp:** Gộp cả đoạn văn tìm được và các khái niệm liên quan lại thành một "Ngữ cảnh" (Context) phong phú.

### 3.2 Tree of Thoughts & Reward Function ($r_t$)
Làm sao Agent 3 biết đường nào là tốt nhất? Nó dùng một công thức điểm số $r_t$:
$$ Điểm = (0.6 \times \text{Độ hiểu bài}) + (0.4 \times \text{Hoàn thành bài}) - (Hình phạt nếu học sinh bỏ cuộc) $$
Nó "chạy thử" trong đầu (Mental Simulation) xem con đường nào cho điểm cao nhất thì mới thực hiện ngoài đời.

---

## CHƯƠNG 4: HƯỚNG DẪN VẬN HÀNH (USER MANUAL)

### 4.1 Quy trình trải nghiệm (Happy Path)
1.  **Đăng nhập:** Truy cập `localhost:3000`. Hệ thống nhận diện bạn là ai.
2.  **Đặt vấn đề:** Chat một câu, ví dụ: "Dạy tôi Python".
3.  **Quan sát:**
    *   Thấy **Agent 3** hiện lên "Đang suy nghĩ..." (Thinking...).
    *   Thấy **Graph** bên phải màn hình sáng lên các node liên quan (Variable, Data Type...).
4.  **Học:** Trả lời các câu hỏi gợi mở của **Agent 4**.
5.  **Kết thúc:** Khi bạn trả lời đúng đủ số câu, thanh Mastery (Độ tinh thông) sẽ đầy và Agent chuyển sang bài mới.

### 4.2 Khi hệ thống "ngáo" (Debugging)
Nếu Agent trả lời sai hoặc bị kẹt:
1.  **Kiểm tra Log:** Mở terminal chạy `docker-compose logs -f backend`. Tìm dòng `ERROR` hoặc `WARNING`.
2.  **Soi Graph:** Vào `localhost:7474`, gõ `MATCH (n) RETURN n` để xem kiến thức đã được nạp vào Neo4j chưa. Nếu đồ thị trống trơn -> Lỗi ở Agent 1 (Reader).
3.  **Kiểm tra Vector:** Nếu Agent tìm không ra tài liệu dù đồ thị có -> Lỗi ở Vector DB hoặc Embedding Model.

---
> **Lời kết:** Hệ thống này không hoàn hảo, nhưng nó là bước tiến từ "Máy trả lời" sang "Máy dạy học". Hãy kiên nhẫn và tiếp tục tối ưu nó.
