# 02. TRÁI TIM ĐỒ THỊ KIẾN THỨC (THE HEART OF KNOWLEDGE GRAPH)

> **Mục tiêu:** Giải thích tại sao chúng ta dùng Neo4j thay vì chỉ dùng Vector DB (như 99% các dự án RAG khác). Đây là sự khác biệt khoa học cốt lõi.

---

## 1. VẤN ĐỀ CỦA VECTOR DB: "ĐIỂM MÙ NGỮ NGHĨA" (THE VECTOR BLIND SPOT)

### 1.1 Vector DB hoạt động thế nào?
Vector DB (như Chroma/Pinecone) hoạt động dựa trên việc so sánh độ tương đồng của từ ngữ (Semantic Similarity).
*   Ví dụ: Bạn tìm "Java". Nó trả về cả "Java (ngôn ngữ lập trình)" và "Java (hòn đảo ở Indo)".
*   **Điểm yếu:** Nó **không có logic**. Nó không biết rằng "Java" là *biến thể* của "C++" hay là *tiền đề* của "Spring Boot".

### 1.2 "Vector Blind Spot" là gì?
Hãy tưởng tượng bạn vào thư viện tìm sách về "Đạo hàm".
*   **Vector DB:** Sẽ đưa cho bạn cuốn sách giáo khoa Toán 12 (vì nó có chữ "Đạo hàm").
*   **Vấn đề:** Nó không biết rằng để học Đạo hàm, bạn **BẮT BUỘC** phải học "Giới hạn" (Limits) trước. Nếu bạn chưa biết Giới hạn mà đọc Đạo hàm -> Bạn sẽ tẩu hỏa nhập ma.
-> Đây là lý do các chatbot RAG thông thường thất bại trong việc dạy học.

---

## 2. GIẢI PHÁP: NEO4J (KIẾN TRÚC GRAPH-RAG HYBRID)

Chúng ta không bỏ Vector DB, mà dùng **Kết hợp (Hybrid)**.
*   **Vector DB:** Đôi mắt (Nhìn thấy từ khóa).
*   **Neo4j:** Bộ não (Hiểu mối quan hệ).

### 2.1 Cấu trúc dữ liệu trong Neo4j
Neo4j không lưu bảng (Table) như SQL, nó lưu các **Node** và **Relationship**.

**Ví dụ JSON Node thực tế (Code reference: `neo4j_client.py`)**:

```json
// Một Concept (Khái niệm)
{
  "labels": ["CourseConcept"],
  "properties": {
    "concept_id": "concept_python_recursion",
    "name": "Recursion in Python",
    "difficulty": 3,
    "time_estimate": 45
  }
}
```

**Mối quan hệ (Quyền năng thực sự):**
```cypher
(c:CourseConcept {name: "Recursion"})-[:REQUIRES]->(p:CourseConcept {name: "Functions"})
```
*   Dòng lệnh trên (Cypher) định nghĩa luật bất di bất dịch: *Muốn học Đệ quy, phải học Hàm trước.*

### 2.2 Quy trình truy vấn hỗn hợp (Hybrid Query Flow)
Khi người dùng hỏi: *"Dạy tôi Đệ quy"*. Hệ thống sẽ làm gì? (Code: `kag_agent.py -> _sync_dual_kg`)

1.  **Bước 1: Vector Search**
    *   Tìm các đoạn văn (Chunks) nói về "Recursion" trong Vector DB.
    *   *Kết quả:* Được một đống văn bản thô.

2.  **Bước 2: Graph Traversal (Truy vết đồ thị)**
    *   Hệ thống hỏi Neo4j: *"Recursion có yêu cầu gì không (Prerequisites)?"*
    *   Neo4j trả lời: *"Có, yêu cầu 'Functions' và 'Stack Memory'."*

3.  **Bước 3: Hợp nhất (Synthesis)**
    *   Hệ thống kiểm tra Profile học sinh (trong Redis).
    *   Nếu học sinh chưa học 'Functions' -> **Chặn lại**. Không dạy Đệ quy nữa. Chuyển sang dạy Functions.
    *   *Đây là điểm khác biệt:* ChatGPT sẽ dạy luôn Đệ quy (và học sinh không hiểu gì). Chúng ta sẽ dạy cái *cần thiết* trước.

---

## 3. CÁC CÂU LỆNH CYPHER QUAN TRỌNG (`neo4j_client.py`)

Đây là các "câu thần chú" chúng ta dùng để giao tiếp với bộ não Neo4j:

### 3.1 Tìm bài học tiếp theo (The Learning Path Query)
Làm sao biết bài gì tiếp theo?
```cypher
MATCH (c:CourseConcept {concept_id: $current_id})
MATCH (c)-[:NEXT|IS_PREREQUISITE_OF]->(next_concept:CourseConcept)
RETURN next_concept
```
*   Tìm tất cả các bài nằm sau bài hiện tại (NEXT) hoặc là bài nâng cao của bài hiện tại (IS_PREREQUISITE_OF).

### 3.2 Tìm bài thay thế (Khi học sinh bị kẹt)
Khi học sinh học mãi không hiểu (Stuck), chúng ta tìm đường khác:
```cypher
MATCH (c:CourseConcept {concept_id: $stuck_id})
MATCH (c)-[:SIMILAR_TO]-(alt:CourseConcept)
RETURN alt
```
*   Tìm các bài "Tương tự" (SIMILAR_TO) để dạy theo cách tiếp cận khác.

### 3.3 Lưu trữ Ghi chú (Archival Memory)
Khi KAG lưu ký ức dài hạn:
```cypher
CREATE (n:PersonalNote {
    content: $content,
    created_at: datetime(),
    learner_id: $learner_id
})
```

---

## TỔNG KẾT
Neo4j không chỉ là nơi chứa dữ liệu. Nó là **Bản đồ Tư duy (Cognitive Map)**.
Nếu không có Neo4j, hệ thống này chỉ là một con vẹt biết nói (Stochastic Parrot). Với Neo4j, nó trở thành một người thầy biết tư duy logic.
