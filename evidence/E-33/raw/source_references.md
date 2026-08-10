# E-33 — Danh sách nguồn tham chiếu đã dùng để xây dựng ROI Model

Tài liệu này liệt kê các nguồn đã sử dụng làm input cho mô hình ROI (E-33).
ROI Model dựa trên 2 loại nguồn: (1) BOM từ E-30, và (2) benchmark ngành công khai.

## 1. Liên kết tới E-30 (BOM — chi phí phần cứng)

| Hạng mục | Giá trị dùng trong mô hình ROI | Nguồn |
|---|---|---|
| Hardware/xe (làm tròn cho mô hình) | $400/xe (buffer lên từ khoảng $335–$440 để tính lắp đặt/vận chuyển) | E-30 — `evidence/E-30/reports/source_report.md` và `evidence/E-30/derived/bom_pricing_table.csv` |

## 2. Benchmark ngành công khai (FMCSA / NSC / ATRI)

| Nguồn | Số liệu sử dụng | URL / Tham chiếu | Lưu ý |
|---|---|---|---|
| FMCSA (Federal Motor Carrier Safety Administration) | Chi phí tai nạn xe tải trung bình — khoảng $91,000–$148,000/vụ | https://www.fmcsa.dot.gov | Benchmark thị trường Mỹ — cần lưu ý khi áp dụng cho thị trường VN |
| NSC (National Safety Council) | Chi phí tai nạn giao thông có thương vong | https://www.nsc.org | Benchmark thị trường Mỹ |
| ATRI (American Transportation Research Institute) | Chi phí vận hành fleet thương mại | https://truckingresearch.org | Benchmark thị trường Mỹ |

]
