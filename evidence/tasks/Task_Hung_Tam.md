# Task Ticket: Hùng & Tâm (AI/ML)
**Thư mục lưu kết quả:** `evidence/01_reproducibility/`, `evidence/05_model_ablation/`, v.v.

## Hướng dẫn chung
Các bằng chứng này liên quan đến độ chính xác và tính tái lập của Core AI. Agent đã tạo sẵn script đánh giá, Owner cần cung cấp data/model thật.

## E-01: Reproducibility C1/C2/C3 (Hùng/Tâm)
- [x] **Hành động:** Đóng băng model/config/data/evaluator thành 1 bundle. Review kết quả trước khi đóng gói final.
- [x] **Kết quả mong đợi:** `evaluation_bundle.zip`, `manifest.json`, `commands.log`
- **Ghi chú của Owner:** C1 (Road/TTC) xong — bundle gồm `configs/challenge1.yaml`, `yolov8s_finetuned_carla_v2.pt`, `scripts/eval_practice.py`, `core/challenge1_road/{predict_ttc,ttc_engine}.py`, hash SHA-256 thật trong `manifest.json`. Composite đã validated trước đó (không re-run trong bundle này): 73.6 in-sample / 72.4 LOTO — xem `scripts/eval_practice.py` + `scripts/loto_postprocess.py`. C2/C3 bundle chưa làm — Hùng cần bổ sung nếu muốn gộp chung.

## E-08: C2 dependencies đầy đủ (Tâm)
- [ ] **Hành động:** Cung cấp artifact YuNet/FaceMesh ONNX + license/nguồn gốc.
- [ ] **Kết quả mong đợi:** `c2_artifact_manifest.json`, `preflight.log`, license/source snapshots
- **Ghi chú của Owner:**

## E-27: C2 generalization (Tâm)
- [ ] **Hành động:** Xác nhận split policy (subject/trip-disjoint).
- [ ] **Kết quả mong đợi:** `c2_eval.json`, `confusion_matrix.png`, `split_manifest.csv`
- **Ghi chú của Owner:**

## E-42: Model drift/domain gap (Tâm/Hùng)
- [x] **Hành động:** Xác nhận consent/provenance dữ liệu real.
- [x] **Kết quả mong đợi:** `psi_ks_metrics.csv`
- **Ghi chú của Owner:** C1 xong. Dữ liệu 100% synthetic CARLA (không phải người thật → không cần consent). PSI 0.83-8.56 (đều "major shift") giữa `Data_train` (CARLA 0.10.0) và `Practice_Dataset`/`extra_trips` (CARLA 0.9.15) trên luminance/mật độ box/kích thước box. Root-cause của 3 lần train regression (v3/v4/v5) được trace cụ thể tới domain gap này — chi tiết + cơ chế lỗi thật trên T01 trong `evidence/05_model_ablation/domain_gap_report.md`. Lưu ý: `Data_train/` gốc hiện không có trên máy khi chạy — dùng bản copy trong `datasets/yolo_finetune/` thay thế, xem ghi chú "Note on data availability" trong report.

## E-05: Alert Orchestrator state/policy (Hùng)
- [ ] **Hành động:** Review policy config có đúng ý đồ thiết kế không.
- [ ] **Kết quả mong đợi:** `orchestrator_junit.xml`, `policy_config.yaml`, `state_trace.jsonl`
- **Ghi chú của Owner:**

## E-06: Ablation: raw alert vs orchestrated (Hùng)
Supporting: Nhân
- [ ] **Hành động:** Cung cấp label protocol cho episode.
- [ ] **Kết quả mong đợi:** `ablation.csv`, `ablation_notebook.html`, label protocol
- **Ghi chú của Owner:**

## E-07: C3 formula/thresholds (Hùng)
- [ ] **Hành động:** Xác nhận công thức/ngưỡng chính xác từ source.
- [ ] **Kết quả mong đợi:** `c3_formula.md`, `c3_tests.xml`, `sample_calculation.csv`
- **Ghi chú của Owner:**

## E-13: C1 critical cases evaluated (Hùng)
- [ ] **Hành động:** Review bin definition có đúng thiết kế.
- [ ] **Kết quả mong đợi:** `c1_metrics.json`, `c1_cases.pdf`, prediction/GT CSV
- **Ghi chú của Owner:**

## E-37: Calibration quality (Hùng)
Supporting: Dân
- [ ] **Hành động:** Parse manifest, tính baseline distribution, tạo epipolar montage.
- [ ] **Kết quả mong đợi:** Baseline distribution, epipolar montage
- **Ghi chú của Owner:**
