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

## E-24: CarSky/KUKSA/VHAL/APK correlation (Dân)
- [ ] **Hành động:** Đồng bộ clock, gửi known event qua platform thật. Thu thập log ở mọi boundary.
- [ ] **Kết quả mong đợi:** `carsky_trace_bundle.zip`, MP4 60s, `mapping.md`
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
