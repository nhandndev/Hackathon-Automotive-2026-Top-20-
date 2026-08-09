# Task Ticket: Dân (Edge/Hardware/Simulation)
**Thư mục lưu kết quả:** `evidence/06_edge_performance/`, `evidence/07_simulation/`, v.v.

## Hướng dẫn chung
Ghi lại trung thực số liệu đo đạc thực tế từ phần cứng hoặc môi trường giả lập.

## E-09: Edge performance đo trên target thật (Dân)
- [ ] **Hành động:** Chuẩn bị Jetson Orin Nano, fix power mode/clocks. Đo FPS/latency/drop rate/CPU-GPU-RAM.
- [ ] **Kết quả mong đợi:** `benchmark.csv`, `tegrastats.log`, `environment.json`, MP4
- **Ghi chú của Owner:**

## E-10: Edge thermal/power/stability (Dân)
- [ ] **Hành động:** Chạy soak test ≥60 phút, tự tay ngắt camera/mạng giữa chừng.
- [ ] **Kết quả mong đợi:** `soak_test.csv`, `power_thermal.log`, `failure_notes.md`
- **Ghi chú của Owner:**

## E-12: CARLA collection tái lập được (Dân)
- [ ] **Hành động:** Ghi version CARLA/Python API/map/seed/GPU-OS, chạy collector, thu 1 trip mẫu.
- [ ] **Kết quả mong đợi:** `collector_environment.json`, `command.sh`, sample trip, MP4
- **Ghi chú của Owner:**

## Business & Market (E-28, E-29, E-30, E-31, E-32, E-33)
- [ ] **E-28 (Market stats):** Tìm nguồn thị trường thật, lưu PDF/page/table.
- [ ] **E-29 (Competitive gap):** Thu thập vendor docs/demo/quote thật.
- [ ] **E-30 (Pricing/BOM):** Lấy báo giá thật, tính low/base/high case.
- [ ] **E-31 (Hypotheses tested):** Phỏng vấn 5-8 người, tổng hợp insight (không tự động hoá).
- [ ] **E-32 (Pilot value):** Pre-register KPI/threshold trước khi chạy pilot.
- [ ] **E-33 (ROI not invented):** Đo before/after thật trong pilot.
- **Ghi chú của Owner:**

## E-25: Audio path (Dân)
- [ ] **Hành động:** Record audio route/TTS init/logcat + video ngoài, che ID Bluetooth nếu có.
- [ ] **Kết quả mong đợi:** `audio_route.log`, MP4
- **Ghi chú của Owner:**

## E-38: CARLA scenario matrix (Dân/Hùng)
- [ ] **Hành động:** Chạy fresh runs với collector log.
- [ ] **Kết quả mong đợi:** `scenario_matrix.csv`
- **Ghi chú của Owner:**

## E-11: CARLA dataset manifest đầy đủ (Dân)
Supporting: Hùng
- [ ] **Hành động:** Review `invalid_trip_report.csv`, không xóa trip lỗi trước khi lưu báo cáo.
- [ ] **Kết quả mong đợi:** `dataset_manifest.json`, `validation_report.json`, `dataset_summary.csv`, `invalid_trip_report.csv`
- **Ghi chú của Owner:**
