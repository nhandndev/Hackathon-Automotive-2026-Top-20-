# Phase 04 — WebSocket Replay 20 FPS

## Mục tiêu

Replay nguyên gốc từng frame AI (`ego`, `driver`, TTC/headway, behavior flags và risk), kèm namespace Backend enrichment ở 20 FPS.

Đây là phase chịu trách nhiệm trực tiếp cho yêu cầu **20 frame/giây**. External AI API được tích hợp ở Phase 02; Phase 04 tiêu thụ output đã cache hoặc từ async inference buffer.

## Protocol

Endpoint: `WS /ws/replay/{trip_id}`.

### Client → Server

```json
{"action":"play"}
{"action":"pause"}
{"action":"seek","frame_id":450}
{"action":"speed","speed":0.5}
```

Speed hợp lệ: `0.25`, `0.5`, `1`, `2`, `4` hoặc giá trị được clamp trong khoảng 0,25–4.

### Server → Client

- `frame`: dữ liệu frame hoàn chỉnh.
- `state`: playing/paused, current frame, speed.
- `ended`: hết trip nếu loop tắt.
- `error`: lỗi protocol/dataset có code rõ ràng.

Mọi message có discriminator `type`:

```json
{"type":"state","trip_id":"T01d","state":"playing","frame_id":0,"speed":1.0,"loop":true}
{"type":"buffering","trip_id":"T01d","frame_id":450,"reason":"ai_pending"}
{"type":"ended","trip_id":"T01d","last_frame_id":1799,"looped":false}
{"type":"error","code":"INVALID_CONTROL","message":"Unsupported action","recoverable":true}
```

Connection policy v1:

- Mỗi client có playback state riêng; không share seek/pause/speed với client khác.
- Kết nối thành công bắt đầu `playing`, frame đầu là frame nhỏ nhất của trip, speed 1x, loop mặc định true.
- `pause` gửi acknowledgement; không phát frame định kỳ khi paused.
- `seek` luôn gửi ngay target frame rồi giữ nguyên trạng thái playing/paused trước đó.
- Action không hợp lệ trả recoverable error; lỗi trip/cache đóng socket với code 1011 sau error message.

## Công việc

### 1. Điều khiển

- [ ] Seek theo `frame_id`, không giả định frame ID bằng list index.
- [ ] Validate JSON/action/speed/frame ID.
- [ ] Trả state acknowledgement sau mỗi control.
- [ ] Quy định rõ cuối trip: mặc định loop cho demo, có metadata `looped=true`.

### 2. Timing

- [ ] Dùng monotonic clock và deadline của frame kế tiếp.
- [ ] Tính thời gian xử lý rồi chỉ sleep phần còn lại.
- [ ] Không polling receive với timeout 1 ms trên mỗi frame; tách receive/control task và send task.
- [ ] Thu thập actual FPS và timing drift cho test/debug.
- [ ] Không đặt lệnh gọi external AI HTTP bên trong send loop 50 ms.
- [ ] MVP recorded replay chỉ bắt đầu sau pre-ingest. `buffering/ai_pending` được giữ trong protocol cho phiên bản live sau, không cần implement live worker trong v1.

### 3. Payload enrichment

- [ ] Đưa `trip_id`, `metadata` và toàn bộ frame AI nguyên gốc vào payload.
- [ ] Không đổi tên `ego/driver/min_ttc/headway_sec/behavior_flags/risk` thành schema khác trên WebSocket.
- [ ] Không tính lại risk khi stream; dùng `risk.final_risk_score` của AI.
- [ ] Đặt images, display severity, reasoning, active episode IDs và CarSky status trong `backend_enrichment`.
- [ ] Sinh reasoning cho warning/critical; normal frame bắt buộc trả `reasoning: null` để schema ổn định.
- [ ] Thêm CarSky delivery status mà không chờ blocking request.

### 4. Connection lifecycle

- [ ] Cleanup connection trong `finally` cho mọi loại disconnect.
- [ ] Không nuốt exception; log trip ID, connection ID và error.
- [ ] Một client lỗi không ảnh hưởng client khác.
- [ ] Hỗ trợ nhiều client cùng xem một trip và 10 trip song song.
- [ ] Áp dụng queue/backpressure hợp lý; client chậm không làm server tích lũy vô hạn.

Backpressure policy v1: mỗi connection chỉ giữ tối đa một pending frame; khi client chậm, drop frame cũ và giữ frame mới nhất, tăng `dropped_frames`. Không drop state/error/control acknowledgement. Nếu không gửi thành công trong 5 giây, đóng connection.

## Frame payload mẫu

```json
{
  "trip_id": "T01d",
  "metadata": {"duration_sec": 90, "fps": 20, "map": "Town01", "speed_limit_kmh": 80},
  "frame": {
    "frame_id": 450,
    "timestamp": 22.5,
    "ego": {"speed_kmh": 41.0, "longitudinal_accel": -3.8, "lateral_accel": 0.8, "geolocation": {}},
    "driver": {"state": "microsleep", "alertness_score": 0.15, "eye_state": "closed", "head_pose": "normal", "mouth_state": "normal", "nthu_subject_id": "14"},
    "min_ttc": 1.0,
    "headway_sec": "Infinity",
    "behavior_flags": {"harsh_brake": true, "harsh_accel": false, "harsh_corner": false, "speeding": false, "tailgating": true},
    "risk": {"base_risk": 40.0, "driver_factor": 2.2, "final_risk_score": 88.0}
  },
  "backend_enrichment": {
    "images": {"road_cam_url": "/static/kitti/image_2/000450.jpg", "driver_cam_url": "/static/driver/frame_000450.jpg"},
    "reasoning": {"severity": "CRITICAL", "summary": "Phát hiện vi ngủ kết hợp TTC nguy hiểm.", "recommended_action": "Yêu cầu tài xế dừng nghỉ an toàn."}
  }
}
```

## Kiểm thử

- Nhận frame đầu tiên sau khi connect.
- Pause dừng tăng frame; play tiếp tục từ frame hiện tại.
- Seek đến frame 450 và payload trả đúng `frame_id=450`.
- Speed 2x đạt khoảng 40 FPS và 0,5x đạt khoảng 10 FPS.
- JSON/action lỗi trả protocol error nhưng không crash server.
- Disconnect/reconnect không để connection rác.
- 10 trip đồng thời chạy qua smoke test.
- Mock external AI chậm không làm WebSocket event loop treo; replay recorded dùng cache vẫn giữ nhịp.
- Timing 1x đạt 19–21 FPS trên cửa sổ đo 10 giây.
- Acceptance timing: 1x đạt 19–21 FPS đo trên cửa sổ 10 giây; drift timestamp so với wall clock không quá 250 ms/90 giây khi không có client backpressure.

## Definition of Done

- [ ] Protocol được ghi rõ và có WebSocket integration tests.
- [ ] Không còn bare/silent exception trong replay path.
- [ ] Seek/play/pause/speed hoạt động ổn định.
- [ ] Frame 450 hiển thị đúng ảnh, risk, event và reasoning.
- [ ] 10 concurrent trip streams không làm process crash.
