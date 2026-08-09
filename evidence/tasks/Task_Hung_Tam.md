# Task Ticket: Hùng & Tâm (AI/ML)
**Thư mục lưu kết quả:** `evidence/01_release/E-01_challenge_evaluation_bundle/`, `evidence/05_orchestrator/E-06_frame_alert_vs_event_ablation/`, v.v.

## Hướng dẫn chung
Các bằng chứng này liên quan đến độ chính xác và tính tái lập của Core AI. Agent đã tạo sẵn script đánh giá, Owner cần cung cấp data/model thật.


## E-27: C2 generalization (Hùng)
- [ ] **Hành động:** Xác nhận split policy (subject/trip-disjoint).
- [ ] **Kết quả mong đợi:** `c2_eval.json`, `confusion_matrix.png`, `split_manifest.csv`
- **Ghi chú của Owner:** Split policy hiện tại: random 70/30; với crawled/Kaggle data giữ đúng form `train/valid` của YOLO dataset gốc. Kaggle source owner cung cấp: `https://www.kaggle.com/datasets/habbas11/dms-driver-monitoring-system`. Đã tạo evidence tại `evidence/03_ai_c2/E-27_c2_generalization_evaluation/`: `reports/split_policy.md`, `derived/split_manifest.csv`, `reports/c2_eval_sources.md`, `reports/source_report.md`. Chưa audit subject-disjoint vì cần subject IDs/provenance.

## E-42: Model drift/domain gap (Tâm/Hùng)
- [ ] **Hành động:** Xác nhận consent/provenance dữ liệu real.
- [ ] **Kết quả mong đợi:** `psi_ks_metrics.csv`
- **Ghi chú của Owner:** Bỏ qua theo quyết định hiện tại. Không tự sinh PSI/KS nếu chưa có dữ liệu real + consent/provenance + baseline/target domain rõ ràng.

## E-05: Alert Orchestrator state/policy (Tâm)
- [ ] **Hành động:** Review policy config có đúng ý đồ thiết kế không.
- [ ] **Kết quả mong đợi:** `orchestrator_junit.xml`, `policy_config.yaml`, `state_trace.jsonl`
- **Ghi chú của Owner:** E05 là bằng chứng cho Decision Engine/Alert Orchestrator: tầng lọc khi nào prediction/risk được gửi thành cảnh báo thật. Đã tạo evidence tại `evidence/05_orchestrator/E-05_state_policy_lifecycle/`: `reports/alert_orchestrator_explainer.md`, `derived/policy_config.yaml`, `derived/state_trace.jsonl`, `derived/orchestrator_junit.xml`, `reports/source_report.md`. Vẫn cần Tâm/owner review policy config có đúng ý đồ thiết kế không.

## E-06: Ablation: raw alert vs orchestrated (Tâm)
Supporting: Nhân
- [ ] **Hành động:** Cung cấp label protocol cho episode.
- [ ] **Kết quả mong đợi:** `ablation.csv`, `ablation_notebook.html`, label protocol
- **Ghi chú của Owner:** Với C2, nguồn label/protocol nằm ở `experiment/dataset-v2`. Đã tạo `evidence/05_orchestrator/E-06_frame_alert_vs_event_ablation/reports/label_protocol.md` và `reports/source_report.md` để mô tả label source. Chưa tạo `ablation.csv`/notebook vì cần chốt episode-level protocol cho raw alert vs orchestrated alert.

## E-13: C1 critical cases evaluated (Tâm)
- [ ] **Hành động:** Review bin definition có đúng thiết kế.
- [ ] **Kết quả mong đợi:** `c1_metrics.json`, `c1_cases.pdf`, prediction/GT CSV
- **Ghi chú của Owner:** File `HACKATHON/AI/artifacts/predictions_6_samples/evaluation.json` dùng được cho C1 metrics: C1 metrics nằm ở root/per_trip; C2 nằm trong `challenge2`; C3 nằm trong `challenge3`. Đã cập nhật `evidence/02_ai_c1/E-13_c1_critical_case_evaluation/derived/c1_metrics.json` và `reports/source_report.md`. Chưa tạo `c1_cases.pdf`; cần Tâm review bin definition và chốt case selection.

