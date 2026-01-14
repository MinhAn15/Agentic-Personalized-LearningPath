# KỊCH BẢN DEMO BẢO VỆ LUẬN VĂN (THESIS DEFENSE DEMO SCRIPT)

**Chủ đề:** Agentic Personalized Learning Path
**Kịch bản:** "Hành trình từ Zero đến Master: Chinh phục SQL Joins"
**Người trình bày:** Lý Minh An
**Thời lượng dự kiến:** 10-15 phút

---

## Mở đầu (Introduction)

**Presenter:**
"Kính thưa Hội đồng, để chứng minh tính thực tiễn và hiệu quả của hệ thống, tôi xin phép trình bày một demo luồng chạy end-to-end.
Kịch bản của chúng ta là: Một sinh viên tên **Alice**, muốn học về **SQL Joins** để phân tích dữ liệu, nhưng chưa biết bắt đầu từ đâu. Hệ thống sẽ đóng vai trò người gia sư thông minh dẫn dắt Alice."

---

## SCENE 1: THE LIBRARIAN (AGENT 1) - Ingestion
**Mục tiêu:** Chứng minh khả năng xây dựng Knowledge Graph tự động từ tài liệu thô.

**Hành động (Action):**
1.  Người dùng upload file `Introduction_to_SQL.pdf`.
2.  Hệ thống chạy Agent 1.

**Hiển thị (Visuals):**
*   **Terminal/Log:**
    ```text
    [Agent 1] Processing: Introduction_to_SQL.pdf (25k tokens)
    [Agent 1] Strategy: MultiDocFusion Chunking...
    [Agent 1] Extracting Concepts (Layer 1)... Found 15 concepts.
    [Agent 1] Extracting Relationships (Layer 2)... Found PREREQUISITE_OF between 'SELECT' and 'JOIN'.
    [Agent 1] Entity Resolution: Merging 'Inner Join' and 'Simple Join' (Sim=0.92).
    [Agent 1] Neo4j Persist: Success.
    ```
*   **Neo4j Browser:** Show graph visualization của các node vừa tạo (SELECT -> JOIN).

**Lời thoại (Voiceover):**
"Đầu tiên, Agent 1 đọc tài liệu giáo trình. Thay vì chỉ cắt nhỏ văn bản như RAG thông thường, nó trích xuất ra một bản đồ tri thức. Ở đây, quý vị thấy nó đã tự động phát hiện ra rằng 'SELECT' là điều kiện tiên quyết để học 'JOIN'."

---

## SCENE 2: THE PROFILER (AGENT 2) - Cold Start
**Mục tiêu:** Chứng minh khả năng hiểu ý định và đánh giá năng lực ban đầu (Zero-shot LKT).

**Hành động (Action):**
Alice chat: *"I want to learn about SQL Joins for my data analysis project. I have 30 mins."*

**Hiển thị (Visuals):**
*   **Agent 2 Analysis:**
    ```json
    {
      "intent": "LEARN_NEW",
      "topic": "SQL Joins",
      "purpose": "data analysis",
      "time_constraint": "30 mins",
      "current_level": "UNKNOWN"
    }
    ```
*   **Diagnostic Question:**
    "Before we look at Joins, let's check your basics. What does `SELECT *` do?"
    *Alice replies:* "It selects all columns."
*   **LKT Prediction:**
    ```text
    [Agent 2] LKT Inference:
    - User knows 'SELECT' (Mastery: 0.8)
    - Likely knows 'FROM' (Mastery: 0.7 - inferred)
    - Profile Vector: [0.2, 0, 0, 1, 0...] (Visual Learner suspected)
    ```

**Lời thoại (Voiceover):**
"Agent 2 phân tích yêu cầu của Alice. Vì là người mới, nó kích hoạt bài kiểm tra chẩn đoán nhanh. Dựa trên câu trả lời đúng về lệnh SELECT, mô hình LKT suy luận rằng Alice đã sẵn sàng để học JOIN."

---

## SCENE 3: THE NAVIGATOR (AGENT 3) - Path Planning
**Mục tiêu:** Chứng minh khả năng lập kế hoạch chiến lược (ToT) và cá nhân hóa.

**Hành động (Action):**
Agent 3 nhận Vector Profile từ Agent 2 và lập lộ trình.

**Hiển thị (Visuals):**
*   **Tree of Thoughts Visualization (Log):**
    ```text
    [Agent 3] Generating Thoughts (Beam Width=3)...
    - Path A: Inner Join -> Left Join (Score: 0.85) -> Safe, Standard
    - Path B: Cross Join -> Inner Join (Score: 0.40) -> Too complex/Rare
    - Path C: Set Theory -> Venn Diagrams (Score: 0.75) -> Good for Visual learner
    [Agent 3] Selected Path: C (Venn Diagrams) -> A (Inner Join)
    ```
*   **Final Plan:**
    1. Concept: **Set Theory & Venn Diagrams** (Visual foundation)
    2. Concept: **Inner Join Syntax**
    3. Practice: **Simple Query**

**Lời thoại (Voiceover):**
"Vì Agent 2 phát hiện Alice là người học thiên về trực quan (Visual Learner), Agent 3 sử dụng Tree of Thoughts để tìm ra lộ trình tối ưu. Nó chọn cách tiếp cận qua 'Biểu đồ Venn' trước, thay vì đi thẳng vào cú pháp code như cách thông thường. Đây là sự cá nhân hóa sâu sắc."

---

## SCENE 4: THE TUTOR (AGENT 4) - Socratic Guidance
**Mục tiêu:** Chứng minh phương pháp Socratic và Leakage Guard.

**Hành động (Action):**
Alice hỏi: *"How do I write an Inner Join?"*

**Hiển thị (Visuals):**
*   **Agent 4 Internal Thought (CoT):**
    ```text
    [CoT] User asks for syntax. 
    Constraint: Do NOT give code template immediately.
    Strategy: Connect back to Venn Diagrams.
    Step 1: Ask about the intersection area.
    ```
*   **Agent 4 Response:**
    "Think back to the Venn diagram we just saw. If Table A is the left circle and Table B is the right circle, which part represents the 'Inner Join'?"

**Hành động (Action 2):**
Alice trả lời: *"The intersection in the middle."*

**Hiển thị (Visuals 2):**
*   **Agent 4 Response:**
    "Exactly! To get that intersection in SQL, we use the `ON` keyword. Can you try to write the condition that links the two tables?"

**Lời thoại (Voiceover):**
"Thay vì đưa ngay đáp án code, Agent 4 sử dụng phương pháp Socratic. Nó đặt câu hỏi để Alice tự liên hệ kiến thức cũ. Lưu ý rằng Agent không hề tiết lộ cú pháp cho đến khi Alice hiểu bản chất."

---

## SCENE 5: THE JUDGE (AGENT 5) - Evaluation
**Mục tiêu:** Chứng minh khả năng chấm điểm chính xác và phân loại lỗi.

**Hành động (Action):**
Alice nộp bài tập code:
```sql
SELECT * FROM Users
INNER JOIN Orders
-- Missing ON clause
```

**Hiển thị (Visuals):**
*   **JudgeLM Scoring:**
    ```json
    {
      "score": 0.5,
      "error_type": "INCOMPLETE",
      "reasoning": "Correct intent and keywords, but missing the join condition (ON clause). result will be a syntax error."
    }
    ```
*   **5-Path Decision:**
    `Decision: REMEDIATE (Procedural)`
*   **Feedback:**
    "You identified the right tables and join type, but how does the database know *which* rows match? You forgot the `ON` clause."

**Lời thoại (Voiceover):**
"Agent 5 phát hiện lỗi cú pháp. Nó không đánh rớt Alice hoàn toàn mà phân loại là lỗi 'Thiếu sót' (Incomplete). Hệ thống quyết định đưa ra gợi ý sửa lỗi (Remediate) thay vì bắt học lại từ đầu."

---

## SCENE 6: THE PERSONAL OS (AGENT 6) - Memory
**Mục tiêu:** Chứng minh khả năng ghi nhớ dài hạn qua nhiều phiên.

**Hành động (Action):**
3 ngày sau, Alice quay lại: *"What was that join type we learned last time?"*

**Hiển thị (Visuals):**
*   **MemGPT Heartbeat:**
    ```text
    [Function] archival_memory_search("last lesson join type")
    [Result] Found Zettelkasten Note: "Inner Join - represented by Venn intersection."
    ```
*   **Agent 6 Response:**
    "We learned about **Inner Join**, which you successfully described as the intersection of two circles in a Venn diagram. Do you want to review the `ON` clause syntax?"

**Lời thoại (Voiceover):**
"Agent 6 truy xuất lại ký ức từ bộ nhớ dài hạn (Neo4j). Nó không chỉ nhớ tên bài học mà còn nhớ cả ví dụ 'Venn diagram' mà Alice đã tâm đắc. Điều này tạo ra cảm giác liên tục và thấu hiểu người học."

---

## Kết luận (Conclusion)

**Presenter:**
"Qua demo này, quý vị đã thấy 6 Agent không hoạt động rời rạc mà phối hợp nhịp nhàng như một đội ngũ giáo dục thực thụ: Từ biên soạn (A1), thấu hiểu (A2), lập kế hoạch (A3), giảng dạy (A4), chấm thi (A5) đến ghi nhớ (A6).
Xin cảm ơn!"
