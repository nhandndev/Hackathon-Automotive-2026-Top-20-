# Phase 05.1 — Runbook đưa cảnh báo Backend lên CarSky HMI

## 1. Kết quả cuối cùng

Sau khi hoàn thành runbook này, một request từ Backend phải tạo được chuỗi kết quả có thể quan sát:

```text
POST Signals API thành công
→ Signal Watch thấy đúng giá trị
→ HMI app trong Skycraft đổi NORMAL/WARNING/CRITICAL
→ Screen Widget hoặc screenshot thấy đúng giao diện
→ Reset signal đưa HMI về RECOVERY rồi NORMAL
```

Không coi HTTP `2xx` là hoàn thành nếu chưa nhìn thấy UI đổi trên HMI.

Nguồn kỹ thuật: `carsky/carsky-guideline-web 3/index.html`. Tên menu có thể thay đổi nhẹ theo phiên bản CarSky; endpoint và pin phải kiểm tra lại bằng OpenAPI/Blueprint của environment thật.

## 2. Kiến trúc phải tạo

```text
Backend
  │ REST POST /api/v1/signals/{roomId}/{signalNodeKey}/actuate
  ▼
KUKSA Broker/Signal Node
  │ KUKSA pin
  ├── Signal Watch                         chỉ để debug
  │
  └── Script Node hoặc direct KUKSA client
          │ interface do HMI app hỗ trợ
          ▼
      Skycraft Android HMI app
          │
          ├── Screen Widget                xem UI
          └── Audio consumer               phát tone nếu có
```

### Tuyệt đối không làm sai

- Không dùng Signal Watch làm giao diện cho tài xế.
- Không dùng GPIO Panel làm đầu ra cảnh báo.
- Không gọi `/shell`, `/tap` hoặc `/text` để giả lập cảnh báo production.
- Không tạo pin Zenoh. Zenoh chỉ xuất hiện trên Ethernet khi Blueprint nối qua Ethernet Bridge.
- Không giả định Screen Widget tự tạo UI. Nó chỉ phản chiếu VM/app đang chạy.
- Không phụ thuộc Text-to-Speech cho critical alert; TTS cần `a8/audio-play` và guide chưa xác nhận voice tiếng Việt.

## 3. Điều kiện trước khi bắt đầu

| Đầu vào | Người cung cấp | Điều kiện đạt |
|---|---|---|
| Tài khoản CarSky Workbench | CarSky/admin | Đăng nhập được |
| API credential | CarSky/admin | Có key và biết dùng `X-API-Key` hay Bearer |
| Quyền Artifacts/Nydus/Deploy | CarSky/admin | Tạo artifact, blueprint và deployment được |
| Skycraft Android image | HMI/CarSky team | VM boot được và Screen Widget xem được |
| HMI APK hoặc source project | HMI team | App có code nhận KUKSA/bridge state và render UI |
| Custom VSS artifact | Backend + CarSky team | Chứa đúng path và data type bên dưới |
| CarSky domain | CarSky/admin | Mở được `/api/v1/docs` |

Nếu chưa có HMI app, dừng ở Gate 0. AI Agent có thể sinh state machine/view-model và code khi được cung cấp Android project, nhưng con người vẫn phải build/sign/install và kiểm tra trên màn hình thật.

### Gate 0 — Chọn đường nhận signal của HMI

HMI team phải trả lời một trong hai phương án:

- **A — Direct KUKSA:** Android HMI app subscribe KUKSA trực tiếp. Không cần Script Node mapper.
- **B — Bridge:** Script Node subscribe KUKSA rồi chuyển state qua interface HMI app đã hỗ trợ, ví dụ VHAL hoặc network. Blueprint phải có đúng pin/edge cho interface đó.

Không tự chọn giao thức khi chưa xem source/config của HMI app. Ghi quyết định vào phiếu cấu hình:

```text
HMI_INTEGRATION_MODE=direct_kuksa|script_bridge
HMI_BRIDGE_PROTOCOL=none|vhal|network
ANDROID_NODE_KEY=
SIGNAL_NODE_KEY=
SCRIPT_NODE_KEY=
```

Gate đạt khi HMI team xác nhận app đọc được ít nhất một signal test và chỉ rõ pin contract.

## 4. Bước 1 — Tạo API credential

1. Đăng nhập CarSky/Rework UI.
2. Mở **Settings → Credentials**.
3. Chọn **New credential**.
4. Đặt tên, ví dụ `fleet-backend-demo`.
5. Tạo key và sao chép ngay; guide lưu ý key chỉ hiện một lần.
6. Lưu vào secret manager hoặc `.env` local, không commit Git.

```dotenv
CARSKY_ENABLED=true
CARSKY_MODE=external
CARSKY_BASE_URL=https://<carsky-domain>
CARSKY_API_KEY=<secret>
CARSKY_AUTH_MODE=x-api-key
CARSKY_ROOM_ID=
CARSKY_NODE_KEY=
CARSKY_ANDROID_NODE_KEY=
CARSKY_TIMEOUT_SEC=1.5
```

Kiểm tra OpenAPI:

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/openapi.json"
```

Nếu environment dùng Bearer:

```bash
curl --fail --silent --show-error \
  -H "Authorization: Bearer ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/openapi.json"
```

Checkpoint: nhận JSON OpenAPI, không phải trang đăng nhập HTML.

## 5. Bước 2 — Chuẩn bị VSS artifact

### Signal tối thiểu để HMI chạy

| Path | Data type đề xuất | Ví dụ | Ý nghĩa |
|---|---|---:|---|
| `Vehicle.Driver.State` | string/enum | `microsleep` | Trạng thái tài xế |
| `Vehicle.Driver.AlertnessScore` | float | `0.15` | Mức tỉnh táo 0–1 |
| `Vehicle.ADAS.MinTTC` | float | `1.2` | TTC giây; không gửi JSON Infinity |
| `Vehicle.ADAS.FinalRiskScore` | float | `88.0` | Risk nguyên gốc từ AI |
| `Vehicle.ADAS.CriticalAlert` | boolean | `true` | Bật/tắt critical lifecycle |
| `Vehicle.ADAS.AIStatus` | string/enum | `ONLINE` | `ONLINE|DEGRADED|OFFLINE` |
| `Vehicle.ADAS.DataAgeMs` | integer | `40` | Tuổi frame AI gần nhất |

Khuyến nghị thêm để HMI không phải đoán:

- `Vehicle.Speed`: float, km/h.
- `Vehicle.SpeedLimit`: float, km/h.
- `Vehicle.ADAS.Headway`: float, giây.
- `Vehicle.ADAS.DisplaySeverity`: enum `SAFE|WARNING|CRITICAL|RECOVERY`.
- `Vehicle.ADAS.AlertReasonCode`: enum đã định nghĩa ở Phase 05.
- `Vehicle.ADAS.RecommendedActionCode`: enum đã định nghĩa ở Phase 05.
- `Vehicle.ADAS.EventTransition`: enum `NONE|START|UPDATE|END`.

Local setting trong Android HMI:

```text
VoiceEnabled=true
WarningVoiceCooldownSec=15
CriticalToneEnabled=true
AIOnlineMaxAgeMs=1000
AIDegradedMaxAgeMs=3000
```

Quy tắc TTC:

- AI có thể trả `Infinity`, nhưng JSON/CarSky signal không được nhận giá trị Infinity không chuẩn.
- Khi TTC không hữu hạn, dùng `CriticalAlert=false`, reason không phải TTC và không hiển thị TTC.
- Chỉ dùng sentinel nếu VSS/HMI team thống nhất trước; không tự chọn `-1`.

Thao tác:

1. Tạo hoặc cập nhật VSS artifact với đúng path/data type.
2. Vào **Artifacts** trong Workbench.
3. Import/upload artifact.
4. Ghi lại artifact ID/version.
5. Gắn artifact vào KUKSA Broker/Signal node trong Blueprint.

Checkpoint: sau deploy, API list signals phải trả đủ năm path tối thiểu. Nếu thiếu path, không tiếp tục gửi payload.

## 6. Bước 3 — Tạo Blueprint

1. Mở **Nydus → Manage Blueprint**.
2. Tạo Blueprint mới, ví dụ `fleet-driver-safety-hmi-v1`.
3. Thêm **KUKSA Broker Node** và chọn VSS artifact ở Bước 2.
4. Thêm **Skycraft Node**, chọn Android image có HMI app.
5. Nếu Gate 0 chọn Bridge, thêm **Script Node**.
6. Thêm pin theo phương án đã chọn.
7. Nối edge, kiểm tra không có pin treo thuộc critical path.
8. Save Blueprint.

### Phương án A — Direct KUKSA

```text
KUKSA Broker KUKSA pin ↔ Skycraft KUKSA pin
```

HMI app phải thực sự có KUKSA client và subscribe các path dự án. Có pin không đồng nghĩa app tự đọc signal.

### Phương án B — Script bridge

```text
KUKSA Broker KUKSA pin ↔ Script Node KUKSA pin
Script Node output pin ↔ Skycraft input pin tương ứng
```

Script Luau tối thiểu để chứng minh nhận signal:

```lua
local paths = {
  "Vehicle.Driver.State",
  "Vehicle.Driver.AlertnessScore",
  "Vehicle.ADAS.MinTTC",
  "Vehicle.ADAS.FinalRiskScore",
  "Vehicle.ADAS.CriticalAlert",
  "Vehicle.ADAS.DisplaySeverity",
  "Vehicle.ADAS.AlertReasonCode",
  "Vehicle.ADAS.RecommendedActionCode",
  "Vehicle.ADAS.EventTransition"
}

pins.kuksa:subscribe(paths)

pins.kuksa:on_change(function(ev)
  print("HMI_SIGNAL", ev.path, ev.value)
  -- Chuyển ev sang VHAL/network chỉ khi HMI app đã chốt interface đó.
end)
```

Checkpoint:

- Blueprint save thành công.
- KUKSA Broker có VSS artifact.
- Skycraft có Android image/HMI app.
- Edge đúng theo Gate 0.
- Script không tham chiếu pin chưa tồn tại.

## 7. Bước 4 — Deploy và lấy các ID

1. Trong Nydus chọn Blueprint.
2. Chọn **New Deployment**.
3. Chọn/tạo đúng Device.
4. Đặt tên deployment, ví dụ `fleet-hmi-demo-01`.
5. Chọn **Deploy**.
6. Mở Deployment Viewer.
7. Chờ KUKSA, Script (nếu có) và Skycraft đều `Running`.
8. Không tiếp tục nếu pod đang `Pending`, `CrashLoopBackOff` hoặc `ImagePullBackOff`.

Khám phá qua API:

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/devices"

curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/deployments/find?device=<device-name>"

curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/deployments/<room-id>/nodes"

curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/signals/<room-id>"
```

Ghi riêng ba ID:

```dotenv
CARSKY_ROOM_ID=<deployment-room-id>
CARSKY_NODE_KEY=<kuksa-or-signal-node-key>
CARSKY_ANDROID_NODE_KEY=<skycraft-node-key>
```

Không lấy Android node key làm signal node key. Nếu API trả nhiều room/node, con người chọn theo tên Blueprint/deployment; Agent không chọn phần tử đầu tiên.

## 8. Bước 5 — Kiểm tra signal tồn tại

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_NODE_KEY}"
```

Tìm đủ các path tối thiểu. Kiểm tra data type khớp payload. Nếu server không có path:

1. Không retry vô hạn.
2. Kiểm tra artifact đã attach đúng node chưa.
3. Kiểm tra version artifact trong deployment.
4. Redeploy nếu Blueprint/artifact vừa thay đổi.

Gate 1 đạt khi signal list chứa đủ path và node đang Running.

## 9. Bước 6 — Mở các cửa sổ quan sát

Trước khi gửi dữ liệu, mở song song:

1. **Signal Watch** trỏ vào KUKSA/signal pin, chọn các path dự án.
2. **Screen Widget** trỏ vào Skycraft VM.
3. Log Widget hoặc log của Script Node nếu dùng bridge.

Xác minh HMI app đang ở NORMAL. Nếu Screen Widget chỉ thấy launcher/màn hình trống:

- HMI app chưa chạy hoặc chưa được cài.
- Mở app thủ công để debug, sau đó cấu hình auto-start/kiosk cho demo.
- Không dùng thao tác thủ công này để che lỗi nhận signal.

Gate 2 đạt khi Screen Widget thấy màn hình HMI NORMAL trước khi test.

### Cấu hình voice trên HMI app

1. Tạo phrase catalog cố định:

```text
TTC_CRITICAL/BRAKE_SAFE       = Nguy cơ va chạm. Hãy phanh an toàn.
MICROSLEEP/STOP_AND_REST      = Phát hiện dấu hiệu vi ngủ. Hãy giảm tốc và dừng nghỉ an toàn.
DROWSY/STOP_AND_REST          = Bạn đang buồn ngủ. Hãy tìm điểm dừng nghỉ.
DISTRACTED/FOCUS_FORWARD      = Hãy tập trung nhìn về phía trước.
TAILGATING/INCREASE_DISTANCE  = Hãy tăng khoảng cách với xe phía trước.
SPEEDING/REDUCE_SPEED         = Bạn đang vượt giới hạn tốc độ. Hãy giảm tốc.
RECOVERY/NONE                 = Đã trở lại vùng an toàn.
```

2. Ưu tiên Android TTS tiếng Việt; nếu device không có voice phù hợp, đóng gói file audio thu sẵn.
3. Nếu dùng CarSky TTS Widget, thêm part `a8/audio-play` và chỉ dùng voice mà environment liệt kê.
4. Cấu hình warning đọc một lần/cooldown 15 giây.
5. Cấu hình critical ngắt warning đang đọc.
6. Cấu hình `VOICE MUTED` chỉ tắt speech; safety tone và visual critical vẫn chạy.
7. Cấu hình OFFLINE ẩn TTC cũ và đổi halo xám.

## 10. Bước 7 — Gửi fixture theo thứ tự

### 7.1 Normal/reset fixture

```bash
curl --fail-with-body --silent --show-error \
  -X POST \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  -H "Content-Type: application/json" \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_NODE_KEY}/actuate" \
  --data '{"signals":[
    {"path":"Vehicle.Driver.State","value":"alert"},
    {"path":"Vehicle.Driver.AlertnessScore","value":0.95},
    {"path":"Vehicle.ADAS.MinTTC","value":10.0},
    {"path":"Vehicle.ADAS.FinalRiskScore","value":5.0},
    {"path":"Vehicle.ADAS.CriticalAlert","value":false},
    {"path":"Vehicle.ADAS.DisplaySeverity","value":"SAFE"},
    {"path":"Vehicle.ADAS.AlertReasonCode","value":"NONE"},
    {"path":"Vehicle.ADAS.RecommendedActionCode","value":"NONE"},
    {"path":"Vehicle.ADAS.EventTransition","value":"END"},
    {"path":"Vehicle.ADAS.AIStatus","value":"ONLINE"},
    {"path":"Vehicle.ADAS.DataAgeMs","value":40}
  ]}'
```

Kết quả: Signal Watch đổi giá trị; HMI về NORMAL/RECOVERY; không có alarm.

### 7.2 Warning fixture

```bash
curl --fail-with-body --silent --show-error \
  -X POST \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  -H "Content-Type: application/json" \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_NODE_KEY}/actuate" \
  --data '{"signals":[
    {"path":"Vehicle.Driver.State","value":"distracted"},
    {"path":"Vehicle.Driver.AlertnessScore","value":0.45},
    {"path":"Vehicle.ADAS.MinTTC","value":3.0},
    {"path":"Vehicle.ADAS.FinalRiskScore","value":55.0},
    {"path":"Vehicle.ADAS.CriticalAlert","value":false},
    {"path":"Vehicle.ADAS.DisplaySeverity","value":"WARNING"},
    {"path":"Vehicle.ADAS.AlertReasonCode","value":"DISTRACTED"},
    {"path":"Vehicle.ADAS.RecommendedActionCode","value":"FOCUS_FORWARD"},
    {"path":"Vehicle.ADAS.EventTransition","value":"START"},
    {"path":"Vehicle.ADAS.AIStatus","value":"ONLINE"},
    {"path":"Vehicle.ADAS.DataAgeMs","value":40}
  ]}'
```

Kết quả: halo vàng/cam, một primary message “Tập trung phía trước”, không có critical alarm.

### 7.3 Critical fixture

```bash
curl --fail-with-body --silent --show-error \
  -X POST \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  -H "Content-Type: application/json" \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_NODE_KEY}/actuate" \
  --data '{"signals":[
    {"path":"Vehicle.Driver.State","value":"microsleep"},
    {"path":"Vehicle.Driver.AlertnessScore","value":0.15},
    {"path":"Vehicle.ADAS.MinTTC","value":1.2},
    {"path":"Vehicle.ADAS.FinalRiskScore","value":88.0},
    {"path":"Vehicle.ADAS.CriticalAlert","value":true},
    {"path":"Vehicle.ADAS.DisplaySeverity","value":"CRITICAL"},
    {"path":"Vehicle.ADAS.AlertReasonCode","value":"TTC_CRITICAL"},
    {"path":"Vehicle.ADAS.RecommendedActionCode","value":"BRAKE_SAFE"},
    {"path":"Vehicle.ADAS.EventTransition","value":"START"},
    {"path":"Vehicle.ADAS.AIStatus","value":"ONLINE"},
    {"path":"Vehicle.ADAS.DataAgeMs","value":40}
  ]}'
```

Kết quả cuối cần thấy:

```text
NGUY CƠ VA CHẠM — TTC 1.2s
PHANH AN TOÀN • GIỮ THẲNG LÁI
```

HMI có viền/halo đỏ; collision là primary, microsleep có thể là icon phụ; tone chỉ phát pattern ngắn đã được duyệt.

Sau đó gửi lại Normal/reset fixture. HMI phải chuyển RECOVERY rồi NORMAL và dừng audio.

### Test voice, mute và AI freshness

1. Gửi WARNING hai lần trong 15 giây: UI cập nhật, voice chỉ đọc lần đầu.
2. Trong khi warning đang đọc, gửi CRITICAL: warning dừng, critical phrase/tone phát ngay.
3. Bật `VOICE MUTED`, gửi WARNING: không speech; UI vẫn đổi.
4. Giữ `VOICE MUTED`, gửi CRITICAL: UI đỏ và safety tone vẫn chạy.
5. Tắt TTS/audio engine, gửi CRITICAL: visual alert vẫn chạy và delivery không bị block.
6. Actuate `AIStatus=DEGRADED`: chip đổi vàng, hiển thị đang dùng safety rules.
7. Actuate `AIStatus=OFFLINE` và `DataAgeMs=4000`: chip offline, halo xám, TTC cũ bị ẩn.

Nếu environment dùng Bearer, thay header `X-API-Key` bằng `Authorization: Bearer ...` trong toàn bộ lệnh.

## 11. Bước 8 — Đọc lại signal và chụp HMI

Guide mô tả endpoint `/values` bằng POST. Request body chính xác phải lấy từ OpenAPI của environment vì có thể yêu cầu danh sách path. Không tự suy đoán body.

```text
POST /api/v1/signals/{roomId}/{nodeKey}/values
GET  /api/v1/signals/{roomId}/{nodeKey}/subscribe
```

Chụp màn hình VM:

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/vms/${CARSKY_ROOM_ID}/${CARSKY_ANDROID_NODE_KEY}/screenshot" \
  --output /tmp/carsky-hmi-critical.png
```

Accessibility là bằng chứng bổ sung nếu UI expose semantic tree:

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/vms/${CARSKY_ROOM_ID}/${CARSKY_ANDROID_NODE_KEY}/accessibility"
```

Gate 3 đạt khi có đủ ba bằng chứng:

- Response REST thành công.
- Signal Watch hoặc `/values` cho thấy đúng giá trị.
- Screenshot/Screen Widget cho thấy đúng state HMI.

## 12. Bước 9 — Kết nối Backend thật

Sau khi fixture thủ công pass, mới bật adapter Backend:

```dotenv
CARSKY_ENABLED=true
CARSKY_MODE=external
CARSKY_BASE_URL=https://<carsky-domain>
CARSKY_API_KEY=<secret>
CARSKY_AUTH_MODE=x-api-key
CARSKY_ROOM_ID=<room-id>
CARSKY_NODE_KEY=<signal-node-key>
CARSKY_ANDROID_NODE_KEY=<skycraft-node-key>
CARSKY_TIMEOUT_SEC=1.5
```

Backend mapper phải:

1. Validate output AI.
2. Chuyển `Infinity` thành trạng thái không-TTC hợp lệ, không serialize JSON Infinity.
3. Tạo reason/action/severity deterministic; không dùng LLM text để điều khiển HMI.
4. Enqueue `START` đúng một lần khi episode bắt đầu.
5. Không gửi lặp ở 20 FPS.
6. Gửi `END` và `CriticalAlert=false` khi episode kết thúc.
7. Không chặn WebSocket replay trong lúc chờ CarSky.
8. Retry giới hạn cho network/429/5xx; không retry vô hạn 4xx.

Chạy lần lượt:

- Test adapter với mock HTTP.
- Chạy Backend bằng fixture file.
- Replay trip có critical event.
- Quan sát Signal Watch, Screen Widget và Backend delivery log.
- Ngắt mạng/API key để xác nhận replay vẫn chạy và CarSky chuyển `degraded`.

## 13. Bảng xử lý lỗi

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `401/403` | Sai key/auth mode/quyền | Tạo lại credential, kiểm tra header và scope |
| `404 room` | Sai deployment/room đã teardown | Discover lại room từ device |
| `404 node` | Dùng Android node key thay signal node | Xem `/deployments/{roomId}/nodes` |
| `404/422 path` | VSS artifact thiếu path hoặc sai type | Sửa artifact, attach và redeploy |
| API `2xx`, Signal Watch không đổi | Sai node/path hoặc semantics `actuate` | Kiểm tra OpenAPI; dùng Script `on_actuate → publish` nếu runtime yêu cầu |
| Signal Watch đổi, HMI không đổi | App chưa subscribe, bridge/edge sai | Xem Script/app log và Gate 0 pin contract |
| Screen Widget trống | VM/app chưa boot hoặc widget trỏ sai node | Kiểm tra node Running, Android node key, auto-start app |
| Critical hiện nhưng không reset | Backend thiếu `END`/false hoặc HMI state machine lỗi | Gửi reset fixture và kiểm tra lifecycle |
| Không có âm thanh | Thiếu audio consumer/`a8/audio-play` | Dùng tone trong HMI app hoặc thêm playback part |
| TTS không có tiếng Việt | Voice không được guide xác nhận | Dùng tone/pre-recorded audio/custom Vietnamese TTS |
| `/tap` hoặc `/swipe` lỗi | Thiếu `COOLGATE_URL_SERVER` | Không phụ thuộc touch route cho alert flow |
| HMI bị spam | Backend gửi mỗi frame | Deduplicate episode và thêm cooldown/update rate |

## 14. Checklist quay demo

- [ ] Deployment và tất cả node đang Running.
- [ ] HMI app auto-start ở NORMAL.
- [ ] Signal Watch và Screen Widget đã mở.
- [ ] API key/room/node được nạp từ env, không lộ trên màn hình.
- [ ] Normal fixture pass.
- [ ] Warning fixture pass.
- [ ] Critical fixture pass.
- [ ] Collision + microsleep ưu tiên collision đúng.
- [ ] Reset fixture tắt alert/audio và qua RECOVERY.
- [ ] Backend replay tạo cùng kết quả như fixture thủ công.
- [ ] Mất CarSky không làm Backend/WebSocket chết.
- [ ] Có screenshot bằng chứng cho NORMAL, WARNING, CRITICAL và RECOVERY.

## 15. Definition of Done Phase 05.1

- [ ] Có Blueprint thật, không chỉ có sơ đồ trong tài liệu.
- [ ] VSS artifact chứa đúng path/data type và đã attach vào deployment.
- [ ] Room, signal node và Android node được xác định rõ.
- [ ] Signal fixture đi qua REST → KUKSA → HMI app.
- [ ] Screen Widget thấy đúng bốn state NORMAL/WARNING/CRITICAL/RECOVERY.
- [ ] Critical start và end/reset đều hoạt động.
- [ ] Không có request CarSky ở tốc độ 20 FPS.
- [ ] Signal Watch/GPIO/TTS được dùng đúng vai trò từ guide.
- [ ] Audio không phụ thuộc TTS tiếng Việt chưa được xác nhận.
- [ ] AI ONLINE/DEGRADED/OFFLINE và stale-data suppression hoạt động.
- [ ] Voice phrase, cooldown, interrupt, mute và fallback tone hoạt động.
- [ ] Human sign-off hoàn tất cho pin contract, APK deployment, UI readability, âm lượng và privacy.

## 16. Ai làm gì để ra kết quả cuối

### AI Agent có thể tự implement

- Backend CarSky adapter, signal mapper, queue/retry/dedup.
- Config validation và discovery logic.
- Script Node Luau sau khi biết interface bridge.
- HMI state machine/view-model và Android code nếu source project đã có.
- Fixture, mock test, integration script và acceptance checklist.

### Bắt buộc con người nhúng tay

- Cấp quyền Workbench và API credential.
- Chọn đúng device/deployment khi có nhiều room.
- Xác nhận HMI app nhận KUKSA trực tiếp hay qua bridge.
- Import artifact, nối/duyệt Blueprint và deploy trên CarSky thật.
- Build/sign/install APK hoặc cung cấp image đã có app.
- Kiểm thử hình ảnh, âm thanh, độ dễ đọc và an toàn trên màn hình thật.

Không được đánh dấu Phase 05.1 hoàn thành nếu mới dừng ở Signal Watch. Kết quả cuối bắt buộc là cảnh báo nhìn thấy được trong HMI app qua Screen Widget hoặc screenshot API.
