# Evidence Scripts

Thư mục này chứa các tiện ích tự động hóa để hỗ trợ quá trình thu thập và đóng gói bằng chứng (evidence).

## ⚠️ CẢNH BÁO QUAN TRỌNG VỀ DỌN DẸP FILE (CLEANUP)

TUYỆT ĐỐI KHÔNG dùng wildcard diện rộng (ví dụ: `Remove-Item *.json`, `rm *.csv`, `rm -rf *`) để dọn dẹp trong thư mục `evidence/` hoặc các thư mục con của nó.

Trong quá khứ, việc dùng lệnh xoá bằng wildcard đã vô tình xoá mất các file bằng chứng quan trọng đang ở dạng nháp. Để tránh tái diễn, vui lòng tuân thủ quy tắc sau:

Các file/thư mục **KHÔNG BAO GIỜ** được xoá bằng wildcard:
1. Mọi file có chứa hậu tố `DRAFT-UNVERIFIED` (Ví dụ: `decision_event.schema.DRAFT-UNVERIFIED.json`). Đây là các file bằng chứng quan trọng đang chờ duyệt.
2. Thư mục `_test_fixtures/` và nội dung bên trong.
3. File cấu trúc chính: `evidence_index.md`.
4. Mọi file nằm trong thư mục `tasks/` (ví dụ `Task_Nhan.md`).

**Quy tắc mới:** Từ giờ trở đi, mọi lệnh dọn dẹp phải xoá theo tên file cụ thể (explicit filename) hoặc chỉ giới hạn ở các file do script vừa sinh ra trong một session rõ ràng. Không dọn dẹp mù quáng.
