# FPTU DMS Vision — Evidence Workspace Template

Bộ khung này tổ chức 42 evidence từ `E-01` đến `E-42` theo một vị trí chuẩn duy nhất. Khi bắt đầu thu thập evidence, không tạo thêm một bản sao ở thư mục khác; hãy dẫn đường dẫn đến artifact gốc trong `00_index/evidence_index.md`.

## Cách sử dụng

1. Mở đúng thư mục `E-XX_*` tương ứng.
2. Sao chép `00_index/templates/README_template.md` và `metadata_template.json` vào thư mục evidence đó.
3. Đặt dữ liệu gốc vào `raw/`; không chỉnh sửa hoặc ghi đè dữ liệu gốc.
4. Đặt kết quả tính toán, CSV tổng hợp và metrics vào `derived/`.
5. Đặt ảnh, video và montage vào `visual/`; báo cáo kiểm thử vào `reports/`.
6. Lưu câu lệnh, stdout, stderr và exit code trong `commands/`.
7. Cập nhật `00_index/evidence_register.csv` và `00_index/evidence_index.md`.
8. Trước khi nộp, tạo `checksums.sha256` và chạy kiểm tra quyền truy cập.

## Quy ước tên file

```text
E-XX_yyyy-mm-dd_commit7_short-description.ext
```

Ví dụ:

```text
E-04_2026-08-10_abcdef1_golden-event-backend.jsonl
E-09_2026-08-10_abcdef1_jetson-benchmark.csv
```

Không dùng các tên mơ hồ như `final`, `final2`, `new`, `latest` hoặc `ok`.

## Cấu trúc chuẩn của một Evidence ID

```text
E-XX_short_description/
├── README.md
├── metadata.json
├── commands/
│   ├── command.txt
│   ├── stdout.log
│   ├── stderr.log
│   └── exit_code.txt
├── raw/
├── derived/
├── visual/
├── reports/
└── checksums.sha256
```

Các thư mục trống trong bộ khung là chủ ý. Không điền dữ liệu mẫu giả vào evidence. Evidence chưa thu thập phải giữ trạng thái `PENDING_CAPTURE`.

## Trạng thái được phép

- `PENDING_CAPTURE`: chưa có artifact thực tế.
- `IN_PROGRESS`: đang chạy hoặc đang thu thập.
- `CAPTURED_UNVERIFIED`: đã có artifact nhưng chưa kiểm tra độc lập.
- `VERIFIED_PASS`: artifact đầy đủ và chứng minh được claim.
- `VERIFIED_FAIL`: phép thử hoàn tất nhưng claim không đạt.
- `NOT_APPLICABLE`: claim đã bị loại khỏi phạm vi; phải ghi rõ lý do.

## Nguyên tắc trung thực

- Source code đã tồn tại không đồng nghĩa evidence đã hoàn thành.
- Screenshot đơn lẻ không thay thế log, command, exit code và hash.
- Không chuyển dữ liệu đã xử lý vào `raw/`.
- Không xóa kết quả fail; lưu nguyên trạng và giải thích trong README.
- Không đưa credentials, token, khuôn mặt chưa có consent hoặc thông tin cá nhân vào gói nộp.

## Script đi kèm

- `scripts/create_evidence_structure.ps1`: tạo lại cây thư mục trên Windows PowerShell.
- `scripts/create_evidence_structure.sh`: tạo lại cây thư mục trên Linux, Ubuntu hoặc Jetson.

