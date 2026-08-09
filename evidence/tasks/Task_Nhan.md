# Task Ticket: Nhân (Technical Lead / Product)
**Thư mục lưu kết quả:** `evidence/04_event_trace/`, `evidence/12_business_and_market/`, v.v.

## Hướng dẫn chung
Các bằng chứng mang tính chất quyết định nghiệp vụ, kinh doanh và hệ thống cốt lõi. Hãy ghi nhận trung thực trạng thái.

## E-04: Golden event trace (Nhân/Team)
- [ ] **Hành động:** Họp đồng bộ đồng hồ, chọn trip_id, thời điểm chạy chung.
- [ ] **Kết quả mong đợi:** `golden_event.jsonl`, MP4 60-90s, screenshots, `trace_index.md`
- **Ghi chú của Owner:**

## E-17: Intervention chỉ là human workflow (Nhân)
- [ ] **Hành động:** Xác nhận API không có actuator path (không tự động can thiệp vào xe).
- [ ] **Kết quả mong đợi:** `intervention_trace.jsonl`, scope statement.
- **Ghi chú của Owner:**

## E-24: CarSky/KUKSA/VHAL/APK correlation (Nhân)
- [ ] **Hành động:** Đồng bộ clock, gửi known event qua platform thật. Thu thập log ở mọi boundary.
- [ ] **Kết quả mong đợi:** `carsky_trace_bundle.zip`, MP4 60s, `mapping.md`
- **Ghi chú của Owner:**

## E-34: Safety/privacy gates (Nhân/Dân)
- [ ] **Hành động:** Tabletop review, gán approver, test camera-offline state.
- [ ] **Kết quả mong đợi:** `safety_privacy_checklist.pdf`, `tabletop_minutes.md`.
- **Ghi chú của Owner:**

## E-02: AS-IS architecture khớp code (Nhân)
Supporting: Hùng
- [ ] **Hành động:** Vẽ/xác nhận sơ đồ kiến trúc AS-IS; ký xác nhận (sign-off) từng arrow trong sơ đồ khớp code thật.
- [ ] **Kết quả mong đợi:** `as_is_architecture.pdf`, `source_map.csv`
- **Ghi chú của Owner:**

## E-03: DecisionEvent schema thống nhất (Nhân)
Supporting: Hùng
- [ ] **Hành động:** Review case malformed có đúng behavior mong đợi không.
- [ ] **Kết quả mong đợi:** `decision_event.schema.json`, `golden_payloads/`, `api_trace.log`
- **Ghi chú của Owner:**

## E-14: Backend reliability giới hạn đúng thực tế (Nhân)
- [ ] **Hành động:** Xác nhận báo cáo trung thực (không giấu việc mất data khi restart).
- [ ] **Kết quả mong đợi:** `backend_contract.log`, `restart_test.md`, `websocket_trace.jsonl`
- **Ghi chú của Owner:**

## E-15: Automated test claims traceable (Nhân)
Supporting: Hùng
- [ ] **Hành động:** Chạy full test suite AI/BE/FE/HMI ở đúng commit.
- [ ] **Kết quả mong đợi:** `junit/`, `coverage/`, `test_command.log`
- **Ghi chú của Owner:**

## E-16: Failure handling demonstrated (Nhân)
Supporting: Tất cả technical owner
- [ ] **Hành động:** Capture expected safe state, error code, recovery — cảnh báo nếu phát hiện dữ liệu bị fabricate.
- [ ] **Kết quả mong đợi:** `fault_matrix.csv`, logs, MP4
- **Ghi chú của Owner:**

## E-18: Release packet immutable (Nhân)
- [ ] **Hành động:** Xác nhận packet đã freeze đúng thời điểm release.
- [ ] **Kết quả mong đợi:** `release_manifest.json`, `evidence_index.md`, access-check screenshot
- **Ghi chú của Owner:**

## E-19: Copilot grounded, không bịa (Nhân)
Supporting: Thiện
- [ ] **Hành động:** Gán nhãn (label) reviewer cho từng câu trả lời (numeric consistency, unsupported claim...).
- [ ] **Kết quả mong đợi:** `copilot_golden.jsonl`, `factuality_summary.csv`
- **Ghi chú của Owner:**

## E-20: Copilot latency/cost/failure (Nhân)
- [ ] **Hành động:** Chạy fixed prompt set 3+ lần, đo p50/p95, log token/cost, test timeout/provider-down.
- [ ] **Kết quả mong đợi:** `copilot_benchmark.csv`, `provider_failure.log`
- **Ghi chú của Owner:**

## E-26: Clean-room build (Nhân)
Supporting: Tất cả technical owner
- [ ] **Hành động:** Tạo container/máy mới, build BE/FE/AI từ đầu, log mọi lệnh.
- [ ] **Kết quả mong đợi:** `clean_room_run.log`, `environment.lock`, MP4
- **Ghi chú của Owner:**

## E-35: Evidence index (Nhân)
Supporting: Thiện
- [ ] **Hành động:** Build `evidence_index.md` tự động từ toàn bộ file đã có trong `evidence/`.
- [ ] **Kết quả mong đợi:** `evidence_index.md`, `access_test.csv`
- **Ghi chú của Owner:**

## E-36: Long-run load test (Nhân)
- [ ] **Hành động:** Replay controlled stream 4-8h, log memory/drops/reconnect.
- [ ] **Kết quả mong đợi:** Logs load test.
- **Ghi chú của Owner:**

## E-41: Multi-instance readiness (Nhân)
- [ ] **Hành động:** (Chỉ làm SAU khi có durable architecture - điều kiện tiên quyết chưa đủ, để tạm).
- [ ] **Kết quả mong đợi:** Khác
- **Ghi chú của Owner:**
