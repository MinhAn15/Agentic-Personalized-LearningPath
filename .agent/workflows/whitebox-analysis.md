---
description: Format chuẩn cho Whitebox Analysis của mỗi Phase trong Agent
---

# Whitebox Analysis Format Guide

## Mục tiêu
Tạo tài liệu kỹ thuật chi tiết cho mỗi Phase của Agent, dành cho:
- Người am hiểu kỹ thuật nhưng chưa biết dự án
- Người cần hiểu sâu cách hoạt động của từng component

## Structure chuẩn

```markdown
# 🕵️ Whitebox Analysis: Agent [N] ([Tên Agent]) - Phase [N]: [Tên Phase]

**File**: `path/to/main/file.py`

---

## Bối cảnh
[2-3 câu giải thích:]
- Phase này làm gì trong toàn bộ pipeline?
- Vấn đề nào nó giải quyết?
- Tại sao cần phase này?

---

## 1. Input (Đầu vào)

| Đầu vào | Type | Source | Mô tả |
|---------|------|--------|-------|
| `param_1` | String | Phase trước | Giải thích ngắn |
| `param_2` | Dict | User input | Giải thích ngắn |

**Code minh họa:**
```python
# Trích dẫn code thực tế cho thấy cách nhận input
result = await self.method(param_1, param_2)
```

---

## 2. Cấu hình & Constants

| Constant | Giá trị | Ý nghĩa |
|----------|---------|---------|
| `THRESHOLD_A` | 0.85 | Ngưỡng để... |
| `MAX_SIZE` | 4000 | Giới hạn tối đa cho... |

**Cơ sở thiết kế:**
- Giải thích TẠI SAO chọn giá trị này (research, best practice, experiment)

---

## 3. Process (Cách hoạt động)

### 3.1 Tổng quan
[Mô tả pipeline/flow ở mức high-level]

| Bước | Thành phần | Mục đích |
|------|------------|----------|
| 1 | Tên method/module | Làm gì |
| 2 | Tên method/module | Làm gì |

### 3.2 Chi tiết từng bước

#### Bước 1: [Tên bước]
**Mục tiêu**: [1 câu]

**Cách hoạt động**:
1. Bước con 1
2. Bước con 2

**Code minh họa:**
```python
# Trích dẫn code thực tế (có chú thích tiếng Việt nếu cần)
async def method_name(self, param):
    # Làm gì đó
    result = await self.sub_method(param)
    return result
```

**Xử lý lỗi/Fallback**: [Nếu thất bại thì sao?]

#### Bước 2: [Tên bước]
[Lặp lại format trên]

---

## 4. Output (Đầu ra)

### 4.1 Cấu trúc output

| Trường | Type | Mô tả | Ví dụ |
|--------|------|-------|-------|
| `field_1` | String | ... | "abc123" |
| `field_2` | List | ... | ["a", "b"] |

### 4.2 Ví dụ output thực tế
```python
{
    "success": True,
    "data": {...}
}
```

---

## 5. Liên kết với các Phase/Agent khác

### Trong cùng Agent (Internal)
| Phase | Dữ liệu | Hướng |
|-------|---------|-------|
| Phase N-1 | ... | ← Nhận từ |
| Phase N+1 | ... | → Gửi đến |

### Với Agent khác (External)
| Agent | Event | Dữ liệu | Hướng |
|-------|-------|---------|-------|
| Agent X | EVENT_NAME | payload | ← Nhận |
| Agent Y | EVENT_NAME | payload | → Gửi |

### Sơ đồ Data Flow
```
[Phase N-1] → [Phase N] → [Phase N+1]
                 ↑
           [Agent X: EVENT_Y]
```

---

## 6. Kỹ thuật & Thuật toán đặc biệt

[Nếu Phase sử dụng thuật toán/kỹ thuật đặc biệt, giải thích ở đây:]

### [Tên kỹ thuật]
**Nguồn gốc**: [Paper/Library/Custom]

**Cách hoạt động**:
[Giải thích đơn giản với ví dụ]

**Code minh họa:**
```python
# Pseudocode hoặc code thực tế
```
```

## Nguyên tắc viết

1. **Dễ hiểu cho người mới**: Giải thích TẠI SAO, không chỉ WHAT/HOW
2. **Có code chứng minh**: Mỗi claim phải có code snippet thực tế
3. **Có ví dụ cụ thể**: Input/Output với dữ liệu thực tế
4. **Liên kết rõ ràng**: Chỉ rõ data flow giữa các phases/agents
5. **Không dùng mermaid**: Dùng tables và bullet points thay thế
6. **Tiếng Việt**: Toàn bộ nội dung bằng tiếng Việt, chỉ giữ nguyên code/tên biến tiếng Anh

---

## Tính linh hoạt theo loại Phase

Format trên là **template gợi ý**, không bắt buộc đầy đủ. Tùy loại phase mà nhấn mạnh sections khác nhau:

### Phase loại "Input/Validation"
- **Nhấn mạnh**: Section 1 (Input), Section 2 (Constants)
- **Có thể bỏ qua**: Section 6 (Kỹ thuật đặc biệt)
- **Thêm**: Các validation rules, error handling

### Phase loại "Processing/Transformation"
- **Nhấn mạnh**: Section 3 (Process), Section 6 (Kỹ thuật)
- **Chi tiết**: Từng bước trong pipeline, thuật toán sử dụng
- **Thêm**: Performance considerations, tradeoffs

### Phase loại "AI/LLM Integration"
- **Nhấn mạnh**: Prompt structure, LLM response handling
- **Thêm**: Fallback strategies, retry logic
- **Chi tiết**: Cách parse output từ LLM

### Phase loại "Event Handler"
- **Nhấn mạnh**: Section 5 (Liên kết), Event payload structure
- **Thêm**: Subscription logic, event routing
- **Chi tiết**: Inter-agent communication

### Phase loại "Database/Persistence"
- **Nhấn mạnh**: Data schema, queries
- **Thêm**: Transaction handling, consistency guarantees
- **Chi tiết**: Connection management, error recovery

---

## Sections tùy chọn (thêm khi cần)

| Section | Khi nào dùng |
|---------|--------------|
| **Error Handling** | Phase có nhiều failure cases |
| **Performance** | Phase có bottleneck potential |
| **Security** | Phase xử lý sensitive data |
| **Concurrency** | Phase có parallel operations |
| **Caching** | Phase có cache layer |
| **Testing** | Phase có unit tests quan trọng |

---

## Cách gọi workflow này

Khi cần viết Whitebox Analysis, gõ:
```
/whitebox-analysis cho Agent [N] Phase [N]
```

Có thể thêm context:
```
/whitebox-analysis cho Agent 1 Phase 3 (focus vào LLM integration)
```
