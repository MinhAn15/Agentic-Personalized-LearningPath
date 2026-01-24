# Binary Search: Core Concepts

## Concept 1: Định nghĩa bài toán
Cho một **mảng đã sắp xếp**, tìm xem một số target có tồn tại không.

### Cách làm không hiệu quả (Naive)
- Kiểm tra từng phần tử một
- Thời gian: O(n) - chậm với mảng lớn

### Cách làm hiệu quả (Binary Search)
- Loại bỏ một nửa không gian tìm kiếm mỗi lần
- Thời gian: O(log n) - nhanh hơn nhiều

## Concept 2: Các bước thuật toán
1. Bắt đầu với left=0, right=len(arr)-1
2. Trong khi left <= right:
   a. mid = (left + right) // 2
   b. Nếu arr[mid] == target: TÌM THẤY! Return mid
   c. Nếu arr[mid] < target: target ở bên phải, nên left = mid + 1
   d. Nếu arr[mid] > target: target ở bên trái, nên right = mid - 1
3. Nếu vòng lặp kết thúc: KHÔNG TÌM THẤY, return -1

## Concept 3: Tại sao nó hoạt động (Insight quan trọng)
Vì mảng đã SẮP XẾP, ta biết:
- Nếu arr[mid] < target, mọi thứ bên TRÁI cũng < target
- Nên ta có thể bỏ qua toàn bộ nửa bên trái!

Mỗi iteration cắt không gian tìm kiếm làm đôi → độ phức tạp O(log n)

## Concept 4: Implementation (Python)

```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid  # Tìm thấy!
        elif arr[mid] < target:
            left = mid + 1  # Tìm nửa bên phải
        else:
            right = mid - 1  # Tìm nửa bên trái
    
    return -1  # Không tìm thấy
```

## Concept 5: Ứng dụng thực tế
- Tìm kiếm danh bạ điện thoại (contacts được sắp xếp theo tên)
- Tìm sách trong thư viện (ISBN được sắp xếp)
- Phân tích thị trường tài chính (giá cổ phiếu theo thời gian)
- Tìm kiếm trong cơ sở dữ liệu lớn

## Concept 6: Các lỗi thường gặp
- Quên kiểm tra mảng rỗng: Phải kiểm tra len(arr) == 0
- Infinite loop: Phải dùng left = mid + 1 (không phải left = mid)
- Mảng chưa sắp xếp: Binary search CHỈ hoạt động với mảng đã sắp xếp
- Overflow mid: Với mảng rất lớn, dùng mid = left + (right - left) // 2
