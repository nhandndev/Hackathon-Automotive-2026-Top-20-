# Phase 06 — Automated Tests, Submission và Demo Readiness

## Mục tiêu

Chứng minh Backend đúng contract, chạy ổn định trong kịch bản demo và tạo đủ 10 file CSV hợp lệ để nộp.

## 1. Test suite

### Unit tests

- [ ] CSV/JSON adapter và data normalization.
- [ ] TTC/headway validation và JSON round-trip cho Infinity, 10 s, 3 s, 1,5 s và 1 s; không tính lại TTC.
- [ ] Driver state được bảo toàn; episode hysteresis 10 frame không thay state AI.
- [ ] Event episode grouping/deduplication.
- [ ] Round-trip AI payload không mất/đổi `metadata`, `ego`, `driver`, TTC/headway, flags hoặc risk.
- [ ] AI risk ownership và safe-score aggregate; xác nhận Backend không tính lại frame risk.
- [ ] Reasoning templates và coaching fallback intents.
- [ ] CarSky payload/dedup/retry rules.

### API tests

- [ ] Health/readiness.
- [ ] Leaderboard đủ 10 ranking.
- [ ] Fleet compare đủ 5 metrics.
- [ ] Trajectory/events/risk/insurance report.
- [ ] Coaching online mocked và offline fallback.
- [ ] 404/422/503 error schema.
- [ ] External AI provider: success, timeout, 401, 422, 500, retry và file fallback.

### WebSocket tests

- [ ] Connect và frame payload.
- [ ] Play/pause/seek/speed.
- [ ] Critical frame/reasoning.
- [ ] Invalid control message.
- [ ] Disconnect cleanup.

## 2. Submission pipeline

- [ ] Export đúng `T01d.csv`–`T10d.csv`.
- [ ] Mỗi file có đúng 1.800 data rows và 5 columns theo thứ tự:
  `frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score`.
- [ ] Frame ID liên tục 0–1799.
- [ ] Timestamp bắt đầu 0 và tăng 0,05 giây.
- [ ] Không có NaN/null.
- [ ] Driver state chỉ thuộc enum hợp lệ.
- [ ] TTC là số không âm hoặc `inf`.
- [ ] Risk nằm trong 0–100.
- [ ] Export mapping rõ ràng: `min_ttc → predicted_ttc`, `driver.state → predicted_driver_state`, `risk.final_risk_score → predicted_risk_score`; exporter không tái tính ba cột AI này.
- [ ] Validator thất bại nếu thiếu hoặc thừa file; không chỉ kiểm tra các file tình cờ tồn tại.
- [ ] Exporter/validator trả exit code khác 0 khi lỗi để dùng trong CI.

Lệnh mục tiêu:

```bash
cd SE/BE
python -m pytest
python scripts/export_submission_csv.py
python scripts/validate_submission.py
```

## 3. Performance smoke test

- [ ] Leaderboard/compare đọc từ cache.
- [ ] Một replay 1x đạt 19–21 FPS trong cửa sổ đo 10 giây.
- [ ] 10 WebSocket trip chạy đồng thời mà không crash.
- [ ] Copilot fallback phản hồi dưới 3 giây.
- [ ] CarSky timeout không gây tụt nhịp replay đáng kể.
- [ ] External AI latency được hấp thụ ở pre-ingest/buffer; không có synchronous AI HTTP call trong send loop 20 FPS.

Ngưỡng pass/fail:

- Unit/API/WebSocket test: 100% pass; không dùng coverage làm điều kiện hackathon.
- Health/leaderboard/risk API từ cache: p95 dưới 200 ms trên máy demo.
- Compare API từ cache: p95 dưới 300 ms.
- WebSocket 1x: 19–21 FPS trong 10 giây; drift không quá 250 ms trên full trip khi client theo kịp.
- 10 connection chạy đồng thời tối thiểu 30 giây, không unhandled exception và không tăng connection count sau disconnect.
- Copilot fallback dưới 500 ms; online/fallback tổng không quá 3 giây.
- CarSky failure không làm WebSocket rơi dưới 19 FPS.
- External AI pre-ingest thất bại phải làm readiness degraded hoặc dùng đúng-trip file fallback; không silently ready.

## 4. Kịch bản demo end-to-end

1. Chạy Backend và xác nhận `/ready` trả `ready` với 10 cached trips.
2. Mở Frontend, tải leaderboard đủ 10 xe.
3. Chọn `T01d`, kết nối replay.
4. Seek frame 450.
5. Kiểm tra metadata và frame AI nguyên gốc (`ego`, `driver`, TTC/headway, flags, risk) cùng ảnh/reasoning Backend đồng bộ.
6. Kiểm tra critical alert được enqueue sang CarSky hoặc hiện offline status rõ ràng.
7. Hỏi Copilot “Tài xế nào rủi ro cao nhất?” và nhận câu trả lời dưới 3 giây.
8. Mở compare T01d/T02d và insurance report.
9. Chạy validator, trình bày kết quả `10/10 PASSED`.

## 5. Checklist trước khi trình bày

- [ ] Dataset path đúng và đủ dung lượng đọc.
- [ ] Không có secret trong Git/log/screenshot.
- [ ] Port 8000 trống; Swagger mở được.
- [ ] Frontend contract trùng `/api/v1`.
- [ ] Ảnh frame 450 tồn tại.
- [ ] Loa/cảnh báo 880 Hz được test ở phía UI/HMI.
- [ ] CarSky credential hoạt động hoặc offline mode đã bật.
- [ ] VSS artifact có đủ năm path và Workbench `/signals/{roomId}/{nodeKey}` liệt kê được chúng.
- [ ] Có bản submission backup đã validate.
- [ ] Có phương án demo fallback khi mạng ngoài bị mất.

## Definition of Done

- [ ] Toàn bộ automated tests pass.
- [ ] Validator báo chính xác `10/10 PASSED`.
- [ ] Demo end-to-end chạy lại được từ môi trường sạch.
- [ ] Không có lỗi 500 hoặc disconnect không giải thích trong happy path.
- [ ] README chứa lệnh chạy đúng với code thực tế.
- [ ] Chỉ sau các điều kiện trên mới đánh dấu các phase hoàn thành.

## Readiness matrix cuối

| Phase | Điều kiện được coi là sẵn sàng triển khai |
|---|---|
| 01 | Python/config/schema/error contract đã khóa |
| 02 | Provider framework implement được; live AI chỉ cần deployment values hoặc adapter mapper nếu service khác contract v1 |
| 03 | Công thức và response conventions không còn quyết định mở |
| 04 | Message protocol, per-client state, backpressure và timing đã khóa |
| 05 | Fallback Copilot implement được; CarSky Signals API implement được sau khi có credential/room/node/VSS artifact |
| 06 | Có test stack và pass/fail thresholds định lượng |
