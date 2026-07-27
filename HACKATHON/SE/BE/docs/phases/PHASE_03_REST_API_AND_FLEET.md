# Phase 03 — REST API, Fleet Ranking và Comparison

## Mục tiêu

Cung cấp đầy đủ dữ liệu để Frontend dựng leaderboard, bản đồ, radar comparison, event timeline và business report mà không cần tự suy diễn nghiệp vụ.

## API cần triển khai

### `GET /api/v1/fleet/leaderboard`

Response:

```json
{
  "total_vehicles": 10,
  "rankings": [
    {
      "rank": 1,
      "trip_id": "T08d",
      "driver_name": "Driver 08",
      "vehicle_id": "VH-08",
      "safe_score": 96.0,
      "avg_risk_score": 4.2,
      "total_violations": 1,
      "status": "SAFE"
    }
  ]
}
```

- [ ] Sort safe score giảm dần; tie-break bằng trip ID.
- [ ] Rank được tính sau sort.
- [ ] Trả đủ 10 trip theo mặc định.
- [ ] Không hard-code rank #12 khi chỉ có 10 xe.

### `GET /api/v1/fleet/compare`

Query: `trip_a=T01d&trip_b=T02d`.

- [ ] Trả raw value và normalized 0–100 cho hai trip.
- [ ] Năm chiều chính thức: alertness, fatigue control, TTC safety, speed compliance, braking smoothness.
- [ ] Ghi rõ unit và hướng tốt/xấu của từng metric.
- [ ] Hai trip giống nhau hoặc trip không tồn tại trả validation error rõ ràng.

Contract response:

```json
{
  "trip_a":"T01d",
  "trip_b":"T02d",
  "metrics":[
    {"key":"alertness","label":"Alertness","unit":"score","higher_is_better":true,"a":{"raw":0.82,"normalized":82.0},"b":{"raw":0.91,"normalized":91.0}},
    {"key":"fatigue_control","label":"Fatigue control","unit":"percent","higher_is_better":true,"a":{"raw":88.0,"normalized":88.0},"b":{"raw":95.0,"normalized":95.0}},
    {"key":"ttc_safety","label":"TTC safety","unit":"score","higher_is_better":true,"a":{"raw":74.0,"normalized":74.0},"b":{"raw":90.0,"normalized":90.0}},
    {"key":"speed_compliance","label":"Speed compliance","unit":"percent","higher_is_better":true,"a":{"raw":96.0,"normalized":96.0},"b":{"raw":99.0,"normalized":99.0}},
    {"key":"braking_smoothness","label":"Braking smoothness","unit":"percent","higher_is_better":true,"a":{"raw":92.0,"normalized":92.0},"b":{"raw":97.0,"normalized":97.0}}
  ]
}
```

Exact formulas, làm tròn một chữ số:

```text
alertness = mean(driver.alertness_score) * 100
fatigue_control = 100 * count(state not in {drowsy,yawning,microsleep}) / total_frames
ttc_frame_score = 100 nếu min_ttc là Infinity; ngược lại clamp(min_ttc / 3.0 * 100, 0, 100)
ttc_safety = mean(ttc_frame_score)
speed_compliance = 100 * count(ego.speed_kmh <= metadata.speed_limit_kmh) / total_frames
braking_smoothness = 100 * count(behavior_flags.harsh_brake == false) / total_frames
```

Nếu trip rỗng thì ingest invalid, không trả compare. `MAR` không có trong output AI chính thức nên metric được đổi tên thành `fatigue_control`, không tự dựng MAR proxy.

### Trip APIs

- [ ] `GET /api/v1/trips/{trip_id}/trajectory`: frame, timestamp, lat, lon, speed, heading.
- [ ] `GET /api/v1/trips/{trip_id}/events`: filter theo type/severity, trả episodes.
- [ ] `GET /api/v1/trips/{trip_id}/risk`: trả AI risk aggregate gồm max/avg/safe score, nguồn `ai`; không chạy thuật toán risk khác.
- [ ] `GET /api/v1/trips/{trip_id}/insurance-report`: driver-state distribution và risk contribution.

Response conventions:

- Mọi response có `trip_id` và `generated_at` ISO-8601 UTC.
- Trajectory trả `{trip_id,total_points,points:[{frame_id,timestamp,lat,lon,alt,speed_kmh,heading_deg?}]}`; `heading_deg` nullable vì output tối thiểu không bắt buộc.
- Events trả `{trip_id,total_events,events:[{episode_id,type,severity,start_frame,end_frame,start_sec,end_sec,duration_sec,peak_value}]}`.
- Risk trả `{trip_id,risk_source,max_risk_score,avg_risk_score,safe_score,status}`; `status` theo critical rules Phase 02, score làm tròn một chữ số.
- Insurance report trả distribution theo driver state/behavior flags và `risk_contribution_breakdown` chỉ từ số liệu thật; không gắn nhãn SHAP.
- Query event: `type?`, `severity?`, `limit=100` (1–500), `offset=0`; response thêm `limit`, `offset`.

### Compatibility

- [ ] Giữ endpoint cũ làm alias tạm thời nếu FE đã gọi.
- [ ] Thêm deprecation flag trong OpenAPI.
- [ ] Không nhân đôi business logic giữa router cũ và mới.

## Quy tắc report

- Không gọi giá trị tự tạo cố định là SHAP nếu không được mô hình SHAP tính thật; dùng tên `risk_contribution_breakdown`.
- Trip detail API phải trả nguyên gốc `metadata` của AI để Frontend hiển thị description, duration, FPS, map, profile, CARLA version, seed và speed limit.
- Compare metrics dùng đúng năm công thức đã khóa ở trên; không đọc hoặc tự dựng EAR/MAR.
- Các phần trăm distribution phải tổng xấp xỉ 100% sau rounding.
- Driver/vehicle demo mapping nằm trong config hoặc metadata, không nằm rải rác trong service.
- Mapping MVP cố định trong một file config: `T01d→Driver 01/VH-01` đến `T10d→Driver 10/VH-10`; có thể override nhưng không thay contract.
- Leaderboard `status` lấy từ max AI risk/critical rules, không suy ngược tùy ý từ safe score.

## File dự kiến ảnh hưởng

- `app/modules/fleet/router.py`, `fleet_service.py`
- Router/service của event, risk và insurance
- Pydantic response schemas

## Kiểm thử

- Leaderboard có đúng 10 ranking và rank liên tục 1–10.
- Sort/tie-break ổn định.
- Compare trả đúng 5 metrics và range normalized.
- Filters event hoạt động với type/severity.
- Distribution report tổng khoảng 100%.
- Invalid trip/query trả 404/422, không trả 500.
- API dùng cache; test không gọi adapter lại cho mỗi request.

## Definition of Done

- [ ] Swagger có request/response mẫu cho toàn bộ `/api/v1`.
- [ ] Frontend có thể dựng bốn view chỉ từ API response.
- [ ] Không còn contract khác nhau giữa code và SRS.
- [ ] API integration tests pass.
- [ ] Leaderboard p95 < 200 ms và compare p95 < 300 ms trên máy demo theo Phase 06.
