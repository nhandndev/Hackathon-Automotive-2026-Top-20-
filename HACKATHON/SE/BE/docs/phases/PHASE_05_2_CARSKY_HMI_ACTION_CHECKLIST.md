# Phase 05.2 — Checklist thao tác CarSky HMI từ đầu đến cuối

> Làm đúng thứ tự. Chỉ đi tiếp khi bước hiện tại `PASS`.

## 0. Điền thông tin

```text
CARSKY_DOMAIN=
DEVICE_NAME=
DEPLOYMENT_NAME=fleet-hmi-demo-01
BLUEPRINT_NAME=fleet-driver-safety-hmi-v1
HMI_MODE=direct_kuksa|script_bridge
HMI_BRIDGE_PROTOCOL=none|vhal|network
ANDROID_IMAGE=
HMI_APK_OR_IMAGE=
```

- [ ] Có tài khoản CarSky.
- [ ] Có quyền Settings, Artifacts, Nydus, Deployments và Devices.
- [ ] Có Android image.
- [ ] Có HMI app đã nhận được KUKSA hoặc bridge signal.

Thiếu một mục: `STOP`.

## 1. Tạo API key

- [ ] Đăng nhập CarSky.
- [ ] Chọn **Settings → Credentials → New credential**.
- [ ] Nhập `fleet-backend-demo`.
- [ ] Chọn **Create**.
- [ ] Sao chép key ngay.
- [ ] Không commit key.

```bash
cd SE/BE
export CARSKY_BASE_URL='https://<carsky-domain>'
export CARSKY_API_KEY='<api-key>'
```

Kiểu `X-API-Key`:

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/openapi.json" \
  -o /tmp/carsky-openapi.json
```

Nếu dùng Bearer:

```bash
curl --fail --silent --show-error \
  -H "Authorization: Bearer ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/openapi.json" \
  -o /tmp/carsky-openapi.json
```

- [ ] `/tmp/carsky-openapi.json` chứa JSON.

`PASS 1`

## 2. Upload VSS artifact

Artifact phải có:

```text
Vehicle.Driver.State                         string
Vehicle.Driver.AlertnessScore                float
Vehicle.ADAS.MinTTC                          float
Vehicle.ADAS.FinalRiskScore                  float
Vehicle.ADAS.CriticalAlert                   boolean
Vehicle.Speed                                float
Vehicle.SpeedLimit                           float
Vehicle.ADAS.Headway                         float
Vehicle.ADAS.DisplaySeverity                 string
Vehicle.ADAS.AlertReasonCode                 string
Vehicle.ADAS.RecommendedActionCode            string
Vehicle.ADAS.EventTransition                 string
Vehicle.ADAS.AIStatus                        string
Vehicle.ADAS.DataAgeMs                       integer
```

File upload lên CarSky phải là JSON object/map, không phải JSON array.

Đúng:

```json
{
  "Vehicle": {
    "type": "branch",
    "children": {}
  }
}
```

Sai:

```json
[
  {"path": "Vehicle.Driver.State", "datatype": "string"}
]
```

Nếu upload dạng mảng `[...]`, KUKSA Broker sẽ crash với lỗi:

```text
ParseError("invalid type: sequence, expected a map at line 1 column 1")
```

File chuẩn hiện tại của dự án nằm tại:

```text
SE/BE/carsky/dms-vss-signals.json
```

- [ ] Chọn **Artifacts → New/Manage Artifact**.
- [ ] Upload artifact.
- [ ] Đặt tên `fleet-driver-safety-vss-v1`.
- [ ] Save.
- [ ] Ghi artifact ID/version.

`PASS 2`

## 3. Kiểm tra HMI app

- [ ] App đã nằm trong Android image hoặc đã có APK.
- [ ] App tự khởi động.
- [ ] App subscribe toàn bộ signal ở Bước 2.
- [ ] App map `SAFE` → NORMAL.
- [ ] App map `WARNING` → WARNING.
- [ ] App map `CRITICAL` → CRITICAL.
- [ ] App map `RECOVERY` → RECOVERY.
- [ ] `CriticalAlert=false` tắt alarm.
- [ ] Góc trên hiển thị `AI ONLINE|DEGRADED|OFFLINE`.
- [ ] Có nút `VOICE ON|MUTED`.
- [ ] Warning voice cooldown 15 giây.
- [ ] Critical ngắt warning voice.
- [ ] Voice muted vẫn giữ critical safety tone.
- [ ] Có phrase tiếng Việt cố định hoặc audio thu sẵn.

Chưa có app: `STOP — giao HMI team build/install app`.

`PASS 3`

## 4. Tạo Blueprint

- [ ] Chọn **Nydus → Manage Blueprint → New Blueprint**.
- [ ] Nhập `fleet-driver-safety-hmi-v1`.
- [ ] Thêm **KUKSA Broker Node**.
- [ ] Gắn artifact `fleet-driver-safety-vss-v1`.
- [ ] Thêm **Skycraft Node**.
- [ ] Chọn Android image có HMI app.

Nếu `direct_kuksa`:

- [ ] Thêm KUKSA pin cho Broker.
- [ ] Thêm KUKSA pin cho Skycraft.
- [ ] Nối hai pin.

Nếu `script_bridge`:

- [ ] Thêm **Script Node**.
- [ ] Nối Broker KUKSA pin với Script KUKSA pin.
- [ ] Thêm output pin VHAL/network theo HMI app.
- [ ] Nối output Script với input Skycraft.
- [ ] Mở Script Editor và dán:

```lua
local paths = {
  "Vehicle.Driver.State",
  "Vehicle.Driver.AlertnessScore",
  "Vehicle.ADAS.MinTTC",
  "Vehicle.ADAS.FinalRiskScore",
  "Vehicle.ADAS.CriticalAlert",
  "Vehicle.Speed",
  "Vehicle.SpeedLimit",
  "Vehicle.ADAS.Headway",
  "Vehicle.ADAS.DisplaySeverity",
  "Vehicle.ADAS.AlertReasonCode",
  "Vehicle.ADAS.RecommendedActionCode",
  "Vehicle.ADAS.EventTransition",
  "Vehicle.ADAS.AIStatus",
  "Vehicle.ADAS.DataAgeMs"
}

pins.kuksa:subscribe(paths)
pins.kuksa:on_change(function(ev)
  print("HMI_SIGNAL", ev.path, ev.value)
end)
```

- [ ] Thêm code chuyển VHAL/network do HMI team cung cấp.
- [ ] Save Script.
- [ ] Save Blueprint.

`PASS 4`

## 5. Deploy

- [ ] Chọn Blueprint.
- [ ] Chọn **New Deployment**.
- [ ] Chọn đúng Device.
- [ ] Nhập `fleet-hmi-demo-01`.
- [ ] Chọn **Deploy**.
- [ ] Mở Deployment Viewer.
- [ ] KUKSA Broker `Running`.
- [ ] Script Node `Running` nếu có.
- [ ] Skycraft Node `Running`.

Có `Pending`, `CrashLoopBackOff` hoặc `ImagePullBackOff`: `STOP`.

`PASS 5`

## 6. Lấy ID

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/devices" \
  -o /tmp/carsky-devices.json

curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/deployments/find?device=<device-name>" \
  -o /tmp/carsky-deployment.json
```

- [ ] Mở `/tmp/carsky-deployment.json`.
- [ ] Lấy Room ID của `fleet-hmi-demo-01`.

```bash
export CARSKY_ROOM_ID='<room-id>'

curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/deployments/${CARSKY_ROOM_ID}/nodes" \
  -o /tmp/carsky-nodes.json
```

- [ ] Lấy KUKSA/Signal node key.
- [ ] Lấy Skycraft Android node key.

```bash
export CARSKY_SIGNAL_NODE_KEY='<signal-node-key>'
export CARSKY_ANDROID_NODE_KEY='<android-node-key>'
```

`PASS 6`

## 7. Kiểm tra signal

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_SIGNAL_NODE_KEY}" \
  -o /tmp/carsky-signals.json
```

- [ ] Mở `/tmp/carsky-signals.json`.
- [ ] Có đủ 14 signal ở Bước 2.

Thiếu signal: `STOP — sửa artifact và redeploy`.

`PASS 7`

## 8. Mở HMI

- [ ] Chọn **Devices**.
- [ ] Chọn đúng Device/Room.
- [ ] Mở **Manage Widgets**.
- [ ] Thêm **Signal Watch** cho Signal node.
- [ ] Chọn 14 signal.
- [ ] Thêm **Screen Widget** cho Android node.
- [ ] Mở Log Widget cho Script nếu có.
- [ ] HMI app đang chạy.
- [ ] Screen Widget thấy NORMAL.

Không thấy HMI app: `STOP`.

`PASS 8`

## 9. Test NORMAL

```bash
curl --fail-with-body --silent --show-error -X POST \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  -H 'Content-Type: application/json' \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_SIGNAL_NODE_KEY}/actuate" \
  --data '{"signals":[
    {"path":"Vehicle.Driver.State","value":"alert"},
    {"path":"Vehicle.Driver.AlertnessScore","value":0.95},
    {"path":"Vehicle.ADAS.MinTTC","value":10.0},
    {"path":"Vehicle.ADAS.FinalRiskScore","value":5.0},
    {"path":"Vehicle.ADAS.CriticalAlert","value":false},
    {"path":"Vehicle.Speed","value":60.0},
    {"path":"Vehicle.SpeedLimit","value":80.0},
    {"path":"Vehicle.ADAS.Headway","value":3.0},
    {"path":"Vehicle.ADAS.DisplaySeverity","value":"SAFE"},
    {"path":"Vehicle.ADAS.AlertReasonCode","value":"NONE"},
    {"path":"Vehicle.ADAS.RecommendedActionCode","value":"NONE"},
    {"path":"Vehicle.ADAS.EventTransition","value":"END"},
    {"path":"Vehicle.ADAS.AIStatus","value":"ONLINE"},
    {"path":"Vehicle.ADAS.DataAgeMs","value":40}
  ]}'
```

- [ ] Signal Watch đúng.
- [ ] HMI NORMAL.
- [ ] Hiển thị `AI ONLINE` và `VOICE ON` hoặc `MUTED`.
- [ ] Không alarm.

`PASS 9`

## 10. Test WARNING

```bash
curl --fail-with-body --silent --show-error -X POST \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  -H 'Content-Type: application/json' \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_SIGNAL_NODE_KEY}/actuate" \
  --data '{"signals":[
    {"path":"Vehicle.Driver.State","value":"distracted"},
    {"path":"Vehicle.Driver.AlertnessScore","value":0.45},
    {"path":"Vehicle.ADAS.MinTTC","value":3.0},
    {"path":"Vehicle.ADAS.FinalRiskScore","value":55.0},
    {"path":"Vehicle.ADAS.CriticalAlert","value":false},
    {"path":"Vehicle.Speed","value":75.0},
    {"path":"Vehicle.SpeedLimit","value":80.0},
    {"path":"Vehicle.ADAS.Headway","value":2.2},
    {"path":"Vehicle.ADAS.DisplaySeverity","value":"WARNING"},
    {"path":"Vehicle.ADAS.AlertReasonCode","value":"DISTRACTED"},
    {"path":"Vehicle.ADAS.RecommendedActionCode","value":"FOCUS_FORWARD"},
    {"path":"Vehicle.ADAS.EventTransition","value":"START"},
    {"path":"Vehicle.ADAS.AIStatus","value":"ONLINE"},
    {"path":"Vehicle.ADAS.DataAgeMs","value":40}
  ]}'
```

- [ ] Signal Watch đúng.
- [ ] HMI WARNING màu vàng/cam.
- [ ] Hiển thị `TẬP TRUNG PHÍA TRƯỚC`.
- [ ] Không critical alarm.
- [ ] Voice đọc “Hãy tập trung nhìn về phía trước” đúng một lần.
- [ ] Gửi lại trong 15 giây: voice không đọc lặp.

`PASS 10`

## 11. Test CRITICAL

```bash
curl --fail-with-body --silent --show-error -X POST \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  -H 'Content-Type: application/json' \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_SIGNAL_NODE_KEY}/actuate" \
  --data '{"signals":[
    {"path":"Vehicle.Driver.State","value":"microsleep"},
    {"path":"Vehicle.Driver.AlertnessScore","value":0.15},
    {"path":"Vehicle.ADAS.MinTTC","value":1.2},
    {"path":"Vehicle.ADAS.FinalRiskScore","value":88.0},
    {"path":"Vehicle.ADAS.CriticalAlert","value":true},
    {"path":"Vehicle.Speed","value":80.0},
    {"path":"Vehicle.SpeedLimit","value":80.0},
    {"path":"Vehicle.ADAS.Headway","value":0.9},
    {"path":"Vehicle.ADAS.DisplaySeverity","value":"CRITICAL"},
    {"path":"Vehicle.ADAS.AlertReasonCode","value":"TTC_CRITICAL"},
    {"path":"Vehicle.ADAS.RecommendedActionCode","value":"BRAKE_SAFE"},
    {"path":"Vehicle.ADAS.EventTransition","value":"START"},
    {"path":"Vehicle.ADAS.AIStatus","value":"ONLINE"},
    {"path":"Vehicle.ADAS.DataAgeMs","value":40}
  ]}'
```

- [ ] Signal Watch đúng.
- [ ] HMI CRITICAL màu đỏ.
- [ ] Hiển thị `NGUY CƠ VA CHẠM — TTC 1.2s`.
- [ ] Hiển thị `PHANH AN TOÀN • GIỮ THẲNG LÁI`.
- [ ] Alarm phát ngắn rồi dừng.
- [ ] Voice warning đang phát bị ngắt.
- [ ] Voice đọc “Nguy cơ va chạm. Hãy phanh an toàn” hoặc phát audio tương ứng.

Test mute:

- [ ] Chọn `VOICE MUTED`.
- [ ] Gửi lại CRITICAL.
- [ ] Không speech.
- [ ] Visual đỏ và safety tone vẫn hoạt động.
- [ ] Chọn lại `VOICE ON`.

`PASS 11`

## 12. Chụp screenshot

```bash
curl --fail --silent --show-error \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/vms/${CARSKY_ROOM_ID}/${CARSKY_ANDROID_NODE_KEY}/screenshot" \
  --output /tmp/carsky-hmi-critical.png
```

- [ ] Mở `/tmp/carsky-hmi-critical.png`.
- [ ] Ảnh đúng CRITICAL.
- [ ] Lưu ảnh làm bằng chứng.

`PASS 12`

## 13. Test RESET

- [ ] Chạy lại lệnh Bước 9.
- [ ] HMI chuyển RECOVERY.
- [ ] Alarm tắt.
- [ ] HMI về NORMAL.
- [ ] Viền đỏ biến mất.

`PASS 13`

## 13.1 Test AI DEGRADED/OFFLINE

Gửi `DEGRADED`:

```bash
curl --fail-with-body --silent --show-error -X POST \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  -H 'Content-Type: application/json' \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_SIGNAL_NODE_KEY}/actuate" \
  --data '{"signals":[
    {"path":"Vehicle.ADAS.AIStatus","value":"DEGRADED"},
    {"path":"Vehicle.ADAS.DataAgeMs","value":2000}
  ]}'
```

- [ ] HMI hiển thị `AI DEGRADED`.

Gửi `OFFLINE`:

```bash
curl --fail-with-body --silent --show-error -X POST \
  -H "X-API-Key: ${CARSKY_API_KEY}" \
  -H 'Content-Type: application/json' \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_SIGNAL_NODE_KEY}/actuate" \
  --data '{"signals":[
    {"path":"Vehicle.ADAS.AIStatus","value":"OFFLINE"},
    {"path":"Vehicle.ADAS.DataAgeMs","value":4000}
  ]}'
```

- [ ] HMI hiển thị `AI OFFLINE`.
- [ ] Halo xám.
- [ ] TTC cũ bị ẩn.
- [ ] Chạy lại Bước 9 để trở về ONLINE/NORMAL.

`PASS 13.1`

## 14. Cấu hình Backend

Thêm vào `.env` local:

```dotenv
CARSKY_ENABLED=true
CARSKY_MODE=external
CARSKY_BASE_URL=https://<carsky-domain>
CARSKY_API_KEY=<api-key>
CARSKY_AUTH_MODE=x-api-key
CARSKY_ROOM_ID=<room-id>
CARSKY_NODE_KEY=<signal-node-key>
CARSKY_ANDROID_NODE_KEY=<android-node-key>
CARSKY_TIMEOUT_SEC=1.5
```

- [ ] `.env` nằm trong `.gitignore`.
- [ ] Restart Backend.
- [ ] Readiness CarSky là `ready`.

`PASS 14`

## 15. Chạy Backend thật

```bash
cd SE/BE
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] Chạy replay trip có critical event.
- [ ] Signal Watch nhận `START` đúng một lần.
- [ ] HMI chuyển CRITICAL.
- [ ] Cuối episode nhận `END`.
- [ ] HMI chuyển RECOVERY rồi NORMAL.
- [ ] Không gửi CarSky ở 20 FPS.
- [ ] WebSocket không bị đứng.

`PASS 15`

## 16. Test mất kết nối

- [ ] Đổi API key thành key sai.
- [ ] Restart Backend.
- [ ] Chạy replay.
- [ ] CarSky status là `degraded` hoặc `offline`.
- [ ] REST Backend vẫn chạy.
- [ ] WebSocket vẫn chạy.
- [ ] Không retry `401/403` vô hạn.
- [ ] Khôi phục key đúng.
- [ ] Restart Backend.
- [ ] CarSky trở lại `ready`.

`PASS 16`

## 17. Hoàn thành

- [ ] PASS 1–4: key, artifact, HMI app, Blueprint.
- [ ] PASS 5–8: deployment, ID, signal, widget.
- [ ] PASS 9–13.1: NORMAL, WARNING, CRITICAL, voice/mute, screenshot, RESET, AI status.
- [ ] PASS 14–16: Backend thật và offline mode.

```text
FINAL PASS = Signal đúng + HMI đúng + screenshot đúng + reset đúng + replay không bị chặn
```

Đủ 16 PASS: hoàn thành Phase 05.2.
