# Output #001 - Output challenge 1

| | |
|---|---|
| **Claim / outcome** | Model dự đoán Time-To-Collision (TTC) cho từng frame từ ảnh stereo (YOLO detector + SGBM depth + TTC engine), dùng để cảnh báo nguy hiểm khi TTC < 2s ("danger zone"). |
| **Điều kiện xác định đạt** | Predicted TTC phải sát ground-truth TTC trong vùng nguy hiểm (critical zone, TTC<3s — metric MAE-critical); đồng thời phân loại đúng frame nguy hiểm (TTC<2s) so với an toàn (metric Precision/Recall/F1 trên bài toán binary danger-vs-safe). |
| **Kết quả quan sát** | Composite score = **73.6/100** (in-sample, 6 trip Practice) / **72.4/100** (LOTO — leave-one-trip-out cross-validation).<br>Precision = **73.0%**<br>Recall = **74.6%**<br>F1 = **0.731**<br>False Alarm Rate = **1.8%**<br>Miss Alarm Rate = **25.4%**<br>(trung bình cộng 6 trip, tính từ `predictions/FPTU_DMS_Vision/*.csv` qua `team_kit/evaluation.py`) |
| **Trạng thái** | Real. Chạy trên dữ liệu CARLA thật (`Practice_Dataset`, 6 trip x 600 frame). Model production: `yolov8s_finetuned_carla_v2.pt`. Đã chạy lại 2 lần (trước và sau khi nâng cấp torch 2.6→2.12) cho kết quả **giống hệt nhau** — pipeline ổn định. |
| **Evidence locator** | `evidence/01_reproducibility/evaluation_bundle.zip` + `manifest.json` (E-01, hash SHA-256 thật)<br>`predictions/FPTU_DMS_Vision/T01-Sample.csv` … `T06-Sample.csv`<br>`HACKATHON/AI/scripts/eval_practice.py` (lệnh chạy lại) |
| **Video timestamp** | (không áp dụng — input là ảnh stereo theo frame_id, không có video liên tục) |
| **Caveat / giới hạn** | **T01 yếu nhất** (composite 56.3, Precision chỉ 63.6%) — lỗi ước lượng độ sâu (depth) cho người đi bộ.<br>**T05 cũng yếu** (F1=0.42, False Alarm Rate 6.4% — cao nhất 6 trip).<br>LOTO (72.4) thấp hơn in-sample (73.6) ~1.2 điểm — dấu hiệu overfit nhẹ vào 6 trip Practice, chưa test rộng ngoài domain này.<br>Domain gap: train thêm với `Data_train` (CARLA 0.10.0, khác domain với `Practice_Dataset` CARLA 0.9.15) đã thử 3 lần (v3/v4/v5) đều làm **giảm** điểm — xem `evidence/05_model_ablation/domain_gap_report.md` (E-42) để biết cơ chế lỗi cụ thể. |

---
*Per-trip breakdown (nguồn cho dòng "Kết quả quan sát" ở trên):*

| Trip | Precision | Recall | F1 | FPR | Composite |
|---|---|---|---|---|---|
| T01-Sample | 63.6% | 70.0% | 0.667 | 0.7% | 56.3 |
| T02-Sample | 78.9% | 83.3% | 0.811 | 0.7% | 77.8 |
| T03-Sample | 84.8% | 96.6% | 0.903 | 0.9% | 82.4 |
| T04-Sample | 88.9% | 76.9% | 0.825 | 0.9% | 86.1 |
| T05-Sample | 34.5% | 54.3% | 0.422 | 6.4% | 68.6 |
| T06-Sample | 87.0% | 66.7% | 0.755 | 1.1% | 70.4 |

*Sinh ngày 2026-08-10 từ `HACKATHON/AI/scripts/eval_practice.py` + `team_kit/evaluation.py`, chưa commit/push — chờ xác nhận.*
