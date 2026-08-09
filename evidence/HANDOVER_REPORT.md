# Handover Report — FPTU DMS Vision Evidence Framework

**Ngày bàn giao:** 2026-08-09
**Người setup:** Agent (dưới sự giám sát của Trương Tô Dân/Người quản lý)

## Trạng thái tổng quan
- Tổng số Evidence ID: 42
- Đã có ticket phân công: 42/42 (verified bằng diff, xem evidence/_verify/)
- Trạng thái thực tế:
  - Verified: 0/42
  - Draft/Scaffolding: 3/42 (E-01, E-02, E-03)
  - Not Started: 39/42

## Điều quan trọng nhất mỗi Owner cần biết
Framework này là BỘ KHUNG (scaffolding), KHÔNG PHẢI bằng chứng đã thu thập.
Mọi file trong evidence/ hiện tại (trừ 2 script đã Verified) đều là DRAFT
hoặc TEMPLATE — cần Owner tự chạy trên dữ liệu/phần cứng/quy trình thật.

## Việc từng Owner cần làm ngay
- Hùng & Tâm: xem evidence/tasks/Task_Hung_Tam.md — đặc biệt đọc cảnh báo
  ⚠️ ở đầu E-01 trước khi chạy run_eval_bundle.py
- Nhân: xem evidence/tasks/Task_Nhan.md — 21 ID, ưu tiên P0 trước
  (E-02, E-03, E-14, E-15, E-16, E-18)
- Dân: xem evidence/tasks/Task_Dan.md
- Thiện: xem evidence/tasks/Task_Thien.md

## Công cụ đã sẵn sàng dùng ngay
- evidence/scripts/rename_evidence.py — chuẩn hóa tên file (Verified)
- evidence/scripts/redact_evidence.py — che secret trước khi nộp (Verified)
- evidence/scripts/export_real_schema.py — cần chạy trong venv Backend
  (đã test thành công khi có fastapi/pydantic/httpx)

## Rủi ro đã biết, chưa xử lý
- map_architecture.py dùng regex cho Frontend (không phải AST thật) —
  có thể sót case phức tạp, cần Nhân/Thiện review thủ công phần FE
  trong source_map.csv
- decision_event schema thật (E-03) mới export được ở môi trường có
  fastapi cài sẵn — cần verify lại trong đúng venv chính thức của BE

## Không được làm
- KHÔNG tự đánh dấu bất kỳ ID nào là "Verified" chỉ vì đã có file —
  P0 cần chạy evidence/scripts thật + reviewer sign-off theo đúng
  Evidence_Checklist.md gốc
- KHÔNG xóa file bằng wildcard trong evidence/ (xem scripts/README.md)
