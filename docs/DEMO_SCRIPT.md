# 🎬 APLO Defense Demo Script

**Total Duration:** 12-15 Minutes
**Target Audience:** Thesis Defense Committee & Supervisor
**Key Goal:** Demonstrate the "Dynamic Intelligence" of APLO (it's not just a chat app).

---

## 🎭 Scenario 1: The "Happy Path" (10 Minutes)
*Showcasing the ideal learner journey from zero to mastery.*

| Time | Screen / Action | Voiceover (Script) |
| :--- | :--- | :--- |
| **0:00** | **Landing Page** <br> Show clean UI. | "Chào thầy và hội đồng. Đây là giao diện chính của hệ thống APLO." |
| **0:30** | **Signup Form** <br> Create user: `demo_defense`. | "Bước 1, ta tạo một học viên mới. Thay vì nhập học ngay, Agent 2 sẽ yêu cầu làm bài Pre-test." |
| **1:30** | **Pre-test UI** <br> Answer: <br> - Arrays: Correct <br> - Recursion: **Incorrect** (Intentional Gap). | "Em sẽ giả lập một học viên giỏi về Mảng (Arrays) nhưng hoàn toàn chưa biết gì về Đệ quy (Recursion). Điều này tạo ra một 'Knowledge Gap' cụ thể." |
| **3:00** | **Neo4j Browser** (Switch Tab) <br> Run: `MATCH (n:Learner {username:'demo_defense'})-[r]->(m) RETURN *` | "Ngay lập tức, hệ thống không lưu profile vào bảng SQL tĩnh, mà tạo ra một đồ thị. <br> Thầy có thể thấy: Nút `Arrays` có Mastery=0.8 (Màu xanh), còn `Recursion` có Mastery=0.2 (Màu đỏ)." |
| **4:30** | **Dashboard** (Switch back) <br> Click "Start Learning". <br> **Show**: Loading spinner "Agent 3 is planning..." | "Bây giờ, Agent 3 (Path Planner) sẽ quét đồ thị. Nó thấy mục tiêu là 'Binary Search', nhưng phát hiện Gap ở 'Recursion'. <br> Thay vì dạy Binary Search ngay (sẽ thất bại), nó tự động chèn Recursion vào lộ trình." |
| **6:00** | **Tutor Chat Interface** <br> Agent greets user. | "Đây là Agent 4 - Tutor. Nó không giảng bài kiểu 'Wikipedia'. Nó thực hiện nguyên tắc số 1 của Harvard: *Kết nối kiến thức cũ*." |
| **6:30** | **Chat Interaction** <br> **User:** "Why do I need recursion?" <br> **Bot:** Explains using the "Arrays" analogy (from profile). | "Thầy thấy đấy, nó giải thích Đệ quy bằng cách so sánh với Vòng lặp trên Mảng - thứ mà học viên ĐÃ biết. Đây là cá nhân hóa thực sự." |
| **8:00** | **Assessment** <br> Tutor asks a check question. <br> **User:** Answers correctly. | "Sau khi giảng, Agent 5 (Evaluator) sẽ nhảy vào kiểm tra. Nếu đúng, nó cập nhật lại Knowledge Graph ngay lập tức." |
| **9:30** | **Neo4j Browser** (Refresh) <br> Show `Recursion` mastery changed to > 0.7. | "Quay lại đồ thị: Nút Recursion đã chuyển xanh. Hệ thống tự động mở khóa bài tiếp theo: Binary Search." |

---

## 🛠️ Scenario 2: The "Whitebox" Deep Dive (3 Minutes)
*Proving the technology works as claimed.*

| Time | Screen / Action | Voiceover (Script) |
| :--- | :--- | :--- |
| **10:00**| **Terminal / VS Code** <br> Show `docker-compose logs backend`. | "Để chứng minh đây không phải là kịch bản dựng sẵn (hardcoded), em xin mở log của Server." |
| **11:00**| **Scroll Log** <br> Highlight `[PLANNER] Running Tree-of-Thoughts...`. | "Đây là lúc Agent 3 suy nghĩ. Nó giả lập 3 lộ trình khác nhau và chọn lộ trình có xác suất thành công cao nhất (High Pedagogical Score)." |
| **12:00**| **Vector Store** <br> Show `backend/storage/vector_store` folder. | "Dữ liệu bài giảng được lấy từ file PDF giáo trình 'Modern MIS', được chunking và lưu tại đây để đảm bảo tính chính xác (RAG)." |

---

## ⚠️ Scenario 3: Edge Case / Risk Management (Backup)
*Use only if asked about failures or robustness.*

| Trigger | Response |
| :--- | :--- |
| **"What if user spams nonsense?"** | **Demo:** Type "Blah blah blah" to Tutor. <br> **Result:** Tutor politely steers back: "I see you're distracted. Let's focus back on Recursion." (Pedagogical Guardrail). |
| **"What if Neo4j dies?"** | **Explanation:** "Hệ thống có cơ chế 'Circuit Breaker'. Nếu Graph DB mất kết nối, nó sẽ chuyển sang chế độ 'Stateless Mode' dùng Context tạm thời trog Redis để không gián đoạn trải nghiệm học." |

---

## ✅ Preparation Checklist

- [ ] **Reset DB**: Run `python scripts/reset_demo_env.py` before demo starts.
- [ ] **Tab Order**: 
    1. APLO Landing Page (localhost:3000)
    2. Neo4j Browser (localhost:7474) - Query pre-filled.
    3. Admin Dashboard (localhost:3000/admin).
- [ ] **Zoom**: Set Browser Zoom to 125% for projector visibility.
