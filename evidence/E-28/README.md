# E-28 - Market sources

**Status:** COMPLETE / VERIFIED FOR MARKET-CONTEXT USE  
**Locked date:** 2026-08-10 (Asia/Saigon)

## 1. Scope

Gói này chứng minh các số liệu bối cảnh thị trường, vận tải, an toàn giao thông và quy định ADDW được lấy từ nguồn chính thức, có ngày công bố, kỳ dữ liệu, định nghĩa và giới hạn sử dụng.

Gói này **không** chứng minh:

- FPTU DMS Vision đã có pilot hoặc khách hàng;
- willingness-to-pay hoặc mức giá đã được thị trường xác nhận;
- TAM/SAM/SOM của sản phẩm;
- doanh thu, mức tiết kiệm, ROI hoặc payback thực tế;
- sản phẩm đã được chứng nhận hoặc homologation theo quy định EU.

## 2. Inventory

| File | Nội dung |
|---|---|
| `E28_market_sources_and_calculation.xlsx` | Sheet `Summary`, `Source Register` và `Calculation`; các ô kết quả là công thức có thể kiểm tra |
| `snapshots/S01_BCA_TNGT_2025_snapshot_2026-08-10.pdf` | Bộ Công an: tai nạn giao thông năm 2025 |
| `snapshots/S02_NSO_KTXH_2025_snapshot_2026-08-10.pdf` | Cục Thống kê: vận tải hàng hóa năm 2025 |
| `snapshots/S03_MOIT_Logistics_Forum_2025_snapshot_2026-08-10.pdf` | Bộ Công Thương: quy mô và tăng trưởng ngành logistics |
| `snapshots/S04_EURLEX_ADDW_2023_2590_snapshot_2026-08-10.pdf` | EUR-Lex: bối cảnh quy định ADDW |
| `citation_text.md` | Nội dung nguồn có thể chèn vào báo cáo và slide |
| `source_urls.md` | URL chính thức và phạm vi sử dụng |
| `SHA256SUMS.txt` | Mã băm kiểm tra tính toàn vẹn của các file evidence |

## 3. Kết luận kiểm chứng

| Source | Kết luận |
|---|---|
| S01 | Được phép dùng `18.615 vụ`, `10.527 người chết`, `12.294 người bị thương`; phải giữ kỳ dữ liệu 15/12/2024-14/12/2025 |
| S02 | Được phép dùng `3.027,7 triệu tấn`, tăng `14,1%`; không được đổi thành số xe hoặc quy mô thị trường DMS |
| S03 | Được phép dùng `45-50 tỷ USD`, tăng `14-16%/năm` như bối cảnh toàn ngành logistics; không phải TAM/SAM/SOM của sản phẩm |
| S04 | Được phép dùng làm regulatory context; không được tuyên bố sản phẩm đã đạt chứng nhận EU |

## 4. Các sửa đổi cần áp dụng vào hồ sơ

1. Slide 8: nguồn của `3.027,7 triệu tấn, tăng 14,1%` phải là **Cục Thống kê - Báo cáo tình hình kinh tế - xã hội quý IV và năm 2025**.
2. Slide 8: nguồn của `45-50 tỷ USD, tăng 14-16%/năm` phải là **Bộ Công Thương - Vietnam Logistics Forum 2025**.
3. Báo cáo trang 75: thay R11 đang yêu cầu bổ sung nguồn bằng nguồn Bộ Công Thương S03 trong `citation_text.md`.
4. Sau khi đưa nguyên gói này vào evidence repository, có thể đổi E-28 thành `VERIFIED` nhưng phải giữ qualifier `MARKET-CONTEXT ONLY`.
5. Không dùng E-28 để thay đổi trạng thái E-30, E-31 hoặc E-33.

## 5. Ghi chú về snapshot

Bốn PDF trong thư mục `snapshots/` là **auditable source snapshot** do nhóm lưu cho E-28: mỗi file ghi cơ quan phát hành, URL chính thức, ngày công bố, ngày truy cập, kỳ dữ liệu, số liệu được phép dùng và giới hạn diễn giải. Chúng không tự nhận là bản sao toàn văn hoặc PDF gốc do cơ quan phát hành.

