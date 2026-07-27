# AI realtime → CarSky HMI: Memory/runbook cho lần làm sau

File này dùng để AI Agent hoặc thành viên SE đọc trước khi nối AI realtime thật vào demo CarSky HMI. Mục tiêu là không phải điều tra lại từ đầu các lỗi đã gặp: KUKSA đã nhận signal nhưng Android custom VHAL không expose đủ property, nên app HMI đọc CarProperty không đổi.

## 1. Kết luận kiến trúc đã chốt

Khi AI đã có realtime output, Backend xử lý theo pipeline này:

```text
AI realtime frame
  ↓
Validate/canonicalize theo AI contract
  ↓
Normalize thành DMS signal state
  ↓
Publish vào CarSky KUKSA signal node
  ↓
HMI Android đọc trực tiếp từ CarSky REST/Backend WebSocket
  ↓
Render Safe / Warning / Critical + voice
```

Không ưu tiên đường:

```text
KUKSA → Script Node → custom Android VHAL property → CarPropertyService → HMI
```

Lý do: đã kiểm tra trên Android node bằng:

```sh
dumpsys car_service | grep -iE "557843456|559940617|559940618|555746306|555746307|555746308|555746309|291504647"
```

Kết quả chỉ expose:

```text
291504647 = PERF_VEHICLE_SPEED
```

Các custom DMS property như Risk, AIStatus, Alertness, DriverState không xuất hiện trong Android CarPropertyService. Vì vậy APK đọc `CarPropertyManager.getProperty(customId, 0)` sẽ fallback về `AI OFFLINE / Risk 0`.

## 2. Contract AI realtime đầu vào

AI có thể trả về frame gần giống:

```json
{
  "trip_id": "T01d",
  "metadata": {
    "trip_id": "T01d",
    "duration_sec": 90,
    "fps": 20,
    "speed_limit_kmh": 80
  },
  "frame_id": 0,
  "timestamp": 0.0,
  "ego": {
    "speed_kmh": 0.0,
    "longitudinal_accel": 0.0,
    "lateral_accel": 0.0,
    "geolocation": {
      "lat": -0.00123,
      "lon": -0.000485,
      "alt": 0.16
    }
  },
  "driver": {
    "state": "distracted",
    "alertness_score": 0.45,
    "eye_state": "open",
    "head_pose": "side",
    "mouth_state": "normal",
    "nthu_subject_id": "14"
  },
  "min_ttc": "Infinity",
  "headway_sec": "Infinity",
  "behavior_flags": {
    "harsh_brake": false,
    "harsh_accel": false,
    "harsh_corner": false,
    "speeding": false,
    "tailgating": false
  },
  "risk": {
    "base_risk": 0.0,
    "driver_factor": 2.2,
    "final_risk_score": 0.0
  }
}
```

Backend phải giữ nguyên các field AI gửi nếu cần trả lại/debug. Không rename field đã thống nhất. Nếu AI thêm field mới thì giữ trong `extra/raw`; nếu thiếu field quan trọng thì dùng fallback có ghi warning, không crash toàn stream.

## 3. Chuẩn normalize sang DMS HMI state

Backend không đưa nguyên toàn bộ AI frame lên HMI. HMI chỉ cần state tối giản:

| HMI signal | Nguồn từ AI | Ghi chú |
|---|---|---|
| `Vehicle.Speed` | `ego.speed_kmh` | float km/h |
| `Vehicle.SpeedLimit` | `metadata.speed_limit_kmh` | float km/h |
| `Vehicle.Driver.State` | `driver.state` | `alert/drowsy/yawning/distracted/microsleep` |
| `Vehicle.Driver.AlertnessScore` | `driver.alertness_score` | float `0..1` |
| `Vehicle.ADAS.MinTTC` | `min_ttc` | nếu Infinity thì không gửi hoặc gửi giá trị lớn như `99.0` cho HMI |
| `Vehicle.ADAS.Headway` | `headway_sec` | nếu Infinity thì không gửi hoặc `99.0` |
| `Vehicle.ADAS.FinalRiskScore` | `risk.final_risk_score` | giữ nguyên từ AI, không tính đè |
| `Vehicle.ADAS.DisplaySeverity` | Backend derive | `SAFE/WARNING/CRITICAL/RECOVERY` |
| `Vehicle.ADAS.CriticalAlert` | Backend derive | boolean |
| `Vehicle.ADAS.AlertReasonCode` | Backend derive | ví dụ `NONE/DISTRACTED/TTC_CRITICAL/MICROSLEEP` |
| `Vehicle.ADAS.RecommendedActionCode` | Backend derive | `NONE/FOCUS_FORWARD/TAKE_BREAK/BRAKE_SAFE/REDUCE_SPEED` |
| `Vehicle.ADAS.EventTransition` | Backend lifecycle | `START/UPDATE/END` |
| `Vehicle.ADAS.AIStatus` | Backend health | `ONLINE/DEGRADED/OFFLINE` |
| `Vehicle.ADAS.DataAgeMs` | Backend realtime monitor | tuổi frame mới nhất |

Rule gợi ý cho demo:

```text
CRITICAL nếu:
- risk.final_risk_score >= 80
- hoặc min_ttc <= 1.5
- hoặc driver.state == microsleep

WARNING nếu:
- risk.final_risk_score >= 45
- hoặc driver.state == distracted/drowsy/yawning
- hoặc headway_sec <= 2.0

SAFE nếu không có điều kiện trên.
```

Recommended action:

```text
microsleep + critical      → BRAKE_SAFE
min_ttc <= 1.5            → BRAKE_SAFE
speeding/high speed risk  → REDUCE_SPEED
distracted                → FOCUS_FORWARD
drowsy/yawning            → TAKE_BREAK
safe                      → NONE
```

## 4. Cách Backend xử lý khi AI realtime đã có

### 4.1 Nhận AI realtime

Backend nên hỗ trợ ít nhất một trong hai cách:

1. AI gọi vào Backend:

```http
POST /api/v1/ai/realtime/frame
```

2. Backend gọi AI external API theo timer/source:

```text
AI_SOURCE_MODE=external_api
AI_EXTERNAL_URL=<url>
AI_EXTERNAL_API_KEY=<secret>
STREAM_FPS=20
```

Khuyến nghị cho demo: dùng WebSocket/SSE hoặc polling 20 FPS nếu AI chưa ổn định. Backend không cần gửi đủ 20 FPS lên CarSky; chỉ cần throttle HMI state khoảng `2–5 FPS`, vì HMI cảnh báo không cần update 20 lần/giây.

### 4.2 Validate/canonicalize

Checklist:

- `trip_id` root phải khớp `metadata.trip_id`.
- `timestamp`, `frame_id`, speed, duration không âm.
- `driver.alertness_score` trong `0..1`.
- `risk.final_risk_score` trong `0..100`.
- `driver.state` chỉ nhận `alert/drowsy/yawning/distracted/microsleep`.
- `Infinity`, `"Infinity"`, `"inf"` được normalize nội bộ; không biến thành `0`.
- `NaN`, `-Infinity` bị reject.
- Extra field AI giữ lại trong raw/debug.

### 4.3 Debounce/lifecycle cảnh báo

Không bật/tắt critical theo từng frame đơn lẻ vì sẽ nhấp nháy. Dùng state machine:

```text
SAFE
  → WARNING nếu warning >= 300ms
  → CRITICAL nếu critical >= 200ms

WARNING
  → CRITICAL nếu critical >= 200ms
  → RECOVERY nếu safe >= 1000ms

CRITICAL
  → RECOVERY nếu không còn critical >= 1500ms

RECOVERY
  → SAFE sau 1500ms
```

Mỗi lần đổi state gửi `EventTransition`:

- `START`: từ SAFE/WARNING sang WARNING/CRITICAL.
- `UPDATE`: vẫn đang warning/critical nhưng evidence thay đổi.
- `END`: từ RECOVERY về SAFE.

### 4.4 Publish CarSky

Lệnh hiện đang dùng:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
.venv/bin/python scripts/carsky_phase05.py send-critical
```

Khi nối thật, thay `send-critical` bằng hàm gửi từ realtime loop:

```text
POST {CARSKY_BASE_URL}/api/v1/signals/{CARSKY_ROOM_ID}/{CARSKY_NODE_KEY}/actuate
Authorization: Bearer <CARSKY_API_KEY>
```

Payload:

```json
{
  "signals": [
    {"path": "Vehicle.Driver.State", "value": "microsleep"},
    {"path": "Vehicle.Driver.AlertnessScore", "value": 0.15},
    {"path": "Vehicle.ADAS.MinTTC", "value": 1.2},
    {"path": "Vehicle.ADAS.FinalRiskScore", "value": 88.0},
    {"path": "Vehicle.ADAS.CriticalAlert", "value": true},
    {"path": "Vehicle.Speed", "value": 80.0},
    {"path": "Vehicle.SpeedLimit", "value": 80.0},
    {"path": "Vehicle.ADAS.Headway", "value": 0.9},
    {"path": "Vehicle.ADAS.DisplaySeverity", "value": "CRITICAL"},
    {"path": "Vehicle.ADAS.AlertReasonCode", "value": "TTC_CRITICAL"},
    {"path": "Vehicle.ADAS.RecommendedActionCode", "value": "BRAKE_SAFE"},
    {"path": "Vehicle.ADAS.EventTransition", "value": "START"},
    {"path": "Vehicle.ADAS.AIStatus", "value": "ONLINE"},
    {"path": "Vehicle.ADAS.DataAgeMs", "value": 40}
  ]
}
```

## 5. HMI demo APK hiện tại

APK live demo được build ở:

```text
SE/HMI/demo-live
```

Build:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
SE/HMI/demo-live/build_demo_apk.sh
```

Script paste qua CarSky ADB:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
pbcopy < SE/HMI/install_hmi_live_via_carsky_adb_widget.sh
```

Trong CarSky ADB shell paste script. Thành công khi thấy:

```text
Success
Starting: Intent { cmp=vn.fpt.dms.hmi/.MainActivity }
```

APK này:

- Package: `vn.fpt.dms.hmi`.
- Hiển thị trạng thái tài xế, risk, alertness, TTC, action.
- Có voice button.
- Không phụ thuộc custom Android VHAL.
- Ưu tiên đọc CarSky REST values nếu Android VM gọi được API.
- Nếu VM không gọi được API hoặc bị chặn mạng, fallback tự chạy cycle `SAFE → WARNING → CRITICAL` để demo không chết.

Nếu muốn demo thật 100%, nên sửa APK/Backend để HMI đọc từ Backend public WebSocket/SSE trong cùng mạng thay vì gọi CarSky API trực tiếp từ Android VM.

## 6. Checklist nghiệm thu nhanh

### CarSky

- [ ] Deployment `Running 3/3`.
- [ ] `DMS Signal Broker` Running.
- [ ] `DMS HMI Bridge` Running nếu còn dùng bridge để debug.
- [ ] `DMS Android HMI` Running.
- [ ] Signal Watch thấy 19 signals.
- [ ] `Vehicle.ADAS.FinalRiskScore`, `DisplaySeverity`, `AIStatus`, `Driver.State` đổi sau khi gửi mock/realtime.

### Backend

- [ ] `scripts/carsky_phase05.py send-critical` trả:

```json
{"ok": true, "sent": 14}
```

- [ ] `scripts/carsky_phase05.py values` đọc lại được value.
- [ ] Không log API key.
- [ ] Nếu AI mất dữ liệu quá ngưỡng, gửi `AIStatus=OFFLINE`, không giữ cảnh báo cũ như live.

### HMI

- [ ] APK install thành công, không có `INSTALL_FAILED_VERSION_DOWNGRADE`.
- [ ] Nếu gặp `INSTALL_FAILED_DEPRECATED_SDK_VERSION`, kiểm tra build có `--min-sdk-version` và `--target-sdk-version`.
- [ ] HMI hiển thị:

```text
AI ONLINE
NGUY HIỂM
PHANH AN TOÀN
Tài xế: Vi ngủ • TTC 1.2s
80 km/h Risk 88 Alertness 15%
```

## 7. Bài học lỗi đã gặp

### Lỗi KUKSA Broker parse VSS

BTC báo:

```text
ParseError("invalid type: sequence, expected a map at line 1 column 1")
```

Nguyên nhân: VSS artifact cũ là array `[...]`; KUKSA Databroker cần object/map `{...}`.

Fix: `SE/BE/carsky/dms-vss-signals.json` phải bắt đầu bằng:

```json
{
  "Vehicle": {
    "type": "branch",
    "children": {}
  }
}
```

### Lỗi Android HMI không đổi dù signal đúng

Triệu chứng:

- Signal Watch thấy `CRITICAL`, `Risk 88`, `AIStatus ONLINE`.
- HMI vẫn `AI OFFLINE / Risk 0`.

Nguyên nhân đã xác nhận:

- App cũ đọc Android `CarPropertyManager`.
- Android CarPropertyService chỉ expose `291504647 PERF_VEHICLE_SPEED`.
- Custom DMS property không expose.

Debug command:

```sh
dumpsys car_service | grep -iE "557843456|559940617|559940618|555746306|555746307|555746308|555746309|291504647"
```

Nếu chỉ thấy `291504647`, không dùng custom VHAL path cho demo.

### Lỗi ADB paste/cài APK

Nếu ADB widget báo:

```text
Connection closed (code 1006)
```

thì bấm `Reconnect`, đợi thấy:

```text
trout_arm64:/ $
```

rồi mới paste.

Nếu cài APK báo:

```text
INSTALL_FAILED_VERSION_DOWNGRADE
```

tăng `versionCode` trong build.

Nếu báo:

```text
INSTALL_FAILED_DEPRECATED_SDK_VERSION
```

đảm bảo `aapt2 link` có:

```bash
--min-sdk-version 29
--target-sdk-version 35
```

## 8. Việc cần làm khi AI realtime thật sẵn sàng

1. Implement endpoint/consumer nhận frame AI realtime.
2. Validate bằng AI contract Phase 01.
3. Tạo `RealtimeSignalNormalizer`.
4. Tạo `AlertLifecycleEngine`.
5. Tạo background publisher đến CarSky, throttle `2–5 FPS`.
6. HMI đọc state từ Backend WebSocket/SSE hoặc CarSky values.
7. Test 3 scenario:
   - Safe.
   - Distracted warning.
   - Microsleep/TTC critical.
8. Ghi audit log mỗi lần đổi severity:

```json
{
  "timestamp": 0.0,
  "trip_id": "T01d",
  "frame_id": 120,
  "severity": "CRITICAL",
  "reason": "TTC_CRITICAL",
  "risk": 88.0,
  "driver_state": "microsleep",
  "action": "BRAKE_SAFE",
  "published_to_carsky": true
}
```

## 9. Nguyên tắc cho AI Agent sau này

- Đọc file này trước khi sửa Phase 05 hoặc CarSky HMI.
- Không quay lại custom Android VHAL nếu chưa có bằng chứng `dumpsys car_service` expose đủ DMS property.
- Không bịa rằng Signal Watch là driver HMI.
- Không commit credential CarSky/API key.
- Nếu AI thêm field mới nhưng không đổi tên field cũ, chỉ mở rộng normalizer, không rewrite toàn pipeline.
- Luôn kiểm tra 4 lớp theo thứ tự:
  1. AI frame có đúng không.
  2. Backend normalize đúng không.
  3. CarSky Signal Watch đổi không.
  4. HMI render đổi không.
