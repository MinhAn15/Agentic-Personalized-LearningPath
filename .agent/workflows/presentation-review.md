---
description: Format ôn tập Agent theo phong cách thuyết trình PowerPoint
---

# Presentation Review Format

## Mục tiêu
Tạo nội dung ôn tập cho từng Phase của Agent, dành cho:
- Thuyết trình PowerPoint
- Người cần hiểu nhanh lý thuyết và ý nghĩa kỹ thuật
- Dễ copy-paste vào slide

## Structure chuẩn

```markdown
# 📚 Ôn tập Agent [N]: [Tên Agent] - Phase [N]: [Tên Phase]

---

## 🌍 BỐI CẢNH

[2-3 câu giải thích Phase này nằm ở đâu trong toàn bộ hệ thống, tại sao cần Phase này, và hậu quả nếu Phase này lỗi]

---

## 🎯 MỤC TIÊU

[Liệt kê 2-3 mục tiêu chính của Phase, ngắn gọn, dễ nhớ]

---

## 🔧 CHI TIẾT KỸ THUẬT

### 1. Đầu vào (Input)

[Bảng hoặc list các input chính với mô tả ngắn]

### 2. Quy trình xử lý (Processing)

[Mô tả từng bước với giải thích TẠI SAO làm vậy, kèm code snippet nếu cần]

### 3. Đầu ra (Output)

[JSON hoặc object mẫu thể hiện kết quả của Phase]

---

## 💡 ĐIỂM QUAN TRỌNG

[Các insight quan trọng, bao gồm:]
- Tại sao chọn kỹ thuật này thay vì kỹ thuật khác?
- Trường hợp đặc biệt nào cần chú ý?
- Thiết kế này giải quyết vấn đề gì?

---

## 🔗 LIÊN KẾT

[Phase này nhận dữ liệu từ đâu và gửi dữ liệu đi đâu]

---

## 🚀 TIẾP THEO

[1 câu giới thiệu Phase tiếp theo]
```

## Nguyên tắc viết

1. **Ngắn gọn**: Mỗi bullet point ≤ 2 dòng
2. **Có ví dụ**: JSON, code snippet minh họa
3. **Giải thích TẠI SAO**: Không chỉ mô tả WHAT/HOW
4. **Tiếng Việt**: Nội dung chính bằng tiếng Việt, giữ nguyên tên kỹ thuật tiếng Anh
5. **Dễ paste**: Format sạch, không cần chỉnh sửa khi copy vào PowerPoint

## Cách gọi workflow này

```
/presentation-review Agent [N] Phase [N]
```

Ví dụ:
```
/presentation-review Agent 1 Phase 1
/presentation-review Agent 2 Phase 2
```
