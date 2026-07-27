# Phase 05.2 — Cầm tay chỉ việc đưa DMS lên CarSky HMI

> Mục tiêu duy nhất: làm theo từ trên xuống để dữ liệu DMS đi từ Backend vào CarSky, xuất hiện trên màn hình HMI và phát cảnh báo âm thanh đúng lúc.
>
> Tài liệu này được đối chiếu trực tiếp với giao diện `https://hackathon-1.carsky.io/` ngày 25/07/2026. Không lưu tài khoản, mật khẩu, API key hoặc client secret vào Git.

## Trạng thái triển khai thật — đọc trước khi thao tác

Nguồn context contract: [`AI_CONTRACT_AND_CHANGELOG.md`](../AI_CONTRACT_AND_CHANGELOG.md).

| Thành phần | Giá trị hiện tại | Trạng thái đã kiểm chứng |
|---|---|---|
| VSS artifact | `dms-driver-safety-vss` `0.0.3` | Upload thành công; đã `Public` |
| Blueprint | `DMS Driver Safety HMI UI` | `valid=true`, 3 node, 2 edge |
| Broker | `DMS Signal Broker` | Schema-less mode theo guide CarSky; giữ nguyên mọi DMS path |
| Bridge | `DMS HMI Bridge` | Inline Lua, KUKSA → VHAL |
| Android | `DMS Android HMI` | `aaos 0.0.1`, `aarch64`, 9 VHAL properties |
| Device | `DMS Driver Safety HMI` | Đã tạo |
| Deployment | `dms-hmi-demo-01` | Namespace được tạo nhưng Dashboard `Pending 0/0` |
| APK | `SE/HMI/app/build/outputs/apk/debug/app-debug.apk` | Build thành công |
| Backend | mapper/client/queue publisher | 23 Backend tests PASS |

UI preflight từng trả lỗi artifact-version dù cả VSS lẫn Android image đều tồn tại và Public:

```text
KUKSA node "DMS Signal Broker": VSS artifact version
"qFgk2pNqQMg5DS34rJ1Gm" not found.
```

VSS đã được chuyển Public và tạo version `0.0.3`, nhưng preflight vẫn lỗi. Theo guide kỹ thuật,
Broker đã chuyển sang schema-less mode để chấp nhận nguyên vẹn 14 DMS paths. Endpoint deployment
tạo namespace `room-01yki2m8`, nhưng Dashboard vẫn `Pending 0/0 nodes ready`, pods/nodes/signals
đều rỗng. Không ghi `FINAL PASS` cho tới khi đủ 3 node Running và có ảnh Screen.

## 0. Đọc 2 phút trước khi bấm

Luồng cần tạo:

```text
Backend DMS
  -> CarSky Signals API
  -> KUKSA Broker trong Room
  -> Android/Skycraft chạy ứng dụng HMI
  -> Screen widget để người thao tác nhìn thấy HMI
  -> loa Android phát câu cảnh báo
```

<<<<<<< Updated upstream
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
=======
Các tên trong giao diện thật:
>>>>>>> Stashed changes

- Thanh dọc bên trái: `Devices`, `Videos`, `Artifacts`, `Nydus`, `Hubs`, `Registry`, `Dashboard`.
- Bánh răng góc trái dưới: `Settings`.
- `Artifacts`: nơi tạo VSS và Android image.
- `Nydus`: nơi tạo Blueprint và Deployment.
- `Devices`: nơi kết nối Room và mở widget.
- `Dashboard`: nơi xem deployment có chạy đủ node hay không.

### Cảnh báo rất quan trọng

- Dấu `+` màu tím trong `Devices` **tạo device ngay lập tức**, không mở form hỏi tên.
- Muốn xoá device: nhấp chuột phải vào device → `Delete Device` → nhập đúng tên → `Confirm`.
- Không sửa hoặc xoá Blueprint `FPTU DMS Vision` nếu chưa được trưởng nhóm cho phép.
- Không dùng deployment đang `Deploying... (9/21)` để nghiệm thu HMI. Chỉ PASS khi tất cả node cần thiết là `Running`.
- CarSky không tự biến JSON AI thành một giao diện DMS hoàn chỉnh. Con người/AI coding agent vẫn phải cung cấp VSS file và ứng dụng HMI Android.

## 1. Chuẩn bị file trước khi vào CarSky

Tạo một thư mục local ngoài Git hoặc thư mục đã được `.gitignore` và đặt vào đó:

```text
carsky-input/
├── dms-vss.json
└── dms-hmi-android-image-or-package
```

`dms-vss.json` phải khai báo tối thiểu các signal sau:

```text
Vehicle.Driver.State                          string
Vehicle.Driver.AlertnessScore                 float
Vehicle.ADAS.MinTTC                           float
Vehicle.ADAS.FinalRiskScore                   float
Vehicle.ADAS.CriticalAlert                    boolean
Vehicle.Speed                                 float
Vehicle.SpeedLimit                            float
Vehicle.ADAS.Headway                          float
Vehicle.ADAS.DisplaySeverity                  string
Vehicle.ADAS.AlertReasonCode                  string
Vehicle.ADAS.RecommendedActionCode             string
Vehicle.ADAS.EventTransition                  string
Vehicle.ADAS.AIStatus                         string
Vehicle.ADAS.DataAgeMs                        integer
```

Nguồn dữ liệu:

- AI cung cấp nguyên gốc: driver state, alertness, TTC, headway, speed, speed limit, final risk.
- Backend bổ sung cho HMI: critical alert, severity, reason, recommended action, transition, AI status và data age.
- Backend không được ghi đè `risk.final_risk_score` của AI.
- AI gửi `Infinity`; trước khi đẩy sang signal kiểu số, Backend phải dùng trạng thái `unavailable`/bỏ giá trị theo API CarSky, không đổi thành `0`.

Ứng dụng HMI Android phải có sẵn các chức năng:

- Subscribe 14 signal trên.
- Màn hình `NORMAL`, `WARNING`, `CRITICAL`, `RECOVERY`.
- Hiển thị tốc độ, giới hạn tốc độ, driver state, risk và TTC khi TTC hữu hạn.
- Hiển thị `AI ONLINE`, `AI DEGRADED` hoặc `AI OFFLINE`.
- Có nút `VOICE ON/MUTED`.
- Phát voice theo event transition, không phát theo từng frame 20 FPS.
- Warning cooldown tối thiểu 15 giây; critical được ưu tiên hơn warning.
- Có câu tiếng Việt cố định hoặc file audio thu sẵn để demo ổn định.

Các file hiện đã có tại `SE/BE/carsky/dms-vss-signals.json`,
`SE/BE/carsky/dms_hmi_bridge.lua` và `SE/HMI`. Không tạo lại nếu contract chưa đổi.

## 2. Đăng nhập

1. Mở Chrome.
2. Truy cập `https://hackathon-1.carsky.io/`.
3. Nếu thấy trang đăng nhập, nhập tài khoản nhóm vào ô username/email.
4. Nhập mật khẩu vào ô password.
5. Bấm `Sign In` hoặc nhấn Enter.
6. Chờ màn hình có logo `rework` và thanh menu dọc bên trái.
7. Kiểm tra tab trình duyệt hiển thị `Rework — No device` khi chưa kết nối device.

PASS khi thấy `Devices`, `Artifacts`, `Nydus` và `Dashboard`.

## 3. Tạo credential cho Backend

Không dùng tài khoản đăng nhập web trong code Backend.

1. Bấm biểu tượng bánh răng ở góc trái dưới.
2. Cửa sổ `Settings` mở ra.
3. Ở cột trái của Settings, bấm `Credentials`.
4. Bấm `New`.
5. Ô `Credential name (e.g. CI pipeline)` xuất hiện.
6. Nhập `dms-backend-demo`.
7. Bấm `Create`.
8. Sao chép API key được hiển thị một lần.
9. Dán vào password manager hoặc `.env` local; không dán vào file `.md`.
10. Nếu secret chỉ hiện một lần, xác nhận đã lưu trước khi đóng.

Kết quả phải thấy một dòng mới trong bảng `NAME / CLIENT ID / CREATED`.

```dotenv
CARSKY_BASE_URL=https://hackathon-1.carsky.io
CARSKY_API_KEY=<api-key-vừa-tạo>
CARSKY_AUTH_MODE=bearer
```

Portal/OpenAPI của workspace hiện tại đã được kiểm chứng dùng
`Authorization: Bearer <api-key>`. API key chỉ dùng outbound Backend → CarSky và không bảo vệ
endpoint Backend.

## 4. Tạo VSS Artifact đúng giao diện thật

### 4.1 Tạo vỏ Artifact

1. Đóng Settings.
2. Bấm `Artifacts` ở thanh trái.
3. Bấm dấu `+` màu tím phía trên danh sách; rê chuột sẽ thấy `New artifact`.
4. Form `New Artifact` xuất hiện.
5. Tại `Name`, nhập `dms-driver-safety-vss`.
6. Tại `Category`, chọn `VSS`.
7. Tại `Description (optional)`, nhập `DMS driver state, risk, TTC, headway and HMI alert signals`.
8. Bấm `Create`.

Nếu nút `Create` bị mờ: kiểm tra `Name` chưa trống và `Category` là `VSS`.

### 4.2 Upload file thành Version

1. Trong danh sách Artifacts, bấm `dms-driver-safety-vss`.
2. Nhìn panel `Inspector` bên phải.
3. Tại `VERSIONS`, bấm `Add Version`.
4. Chọn `patch` cho version đầu/phiên bản sửa nhỏ. Portal sẽ hiện version dự kiến.
5. Tại `Signal Specification`, bấm vùng chọn file.
6. Chọn file `dms-vss.json` đã chuẩn bị ở Bước 1.
7. Bấm `Upload`.
8. Chờ upload nền hoàn tất; không đóng trang ngay.
9. Bấm lại artifact và kiểm tra version mới có nhãn `latest`.
10. Kiểm tra tên file và dung lượng hiện dưới version.

PASS khi Inspector hiển thị ít nhất `1 version`, version có `latest` và đúng file signal specification.

## 5. Tạo hoặc chọn Android Image Artifact

Nếu danh sách đã có Android image chứa đúng app DMS:

1. Bấm category `Android Image`.
2. Bấm artifact tương ứng.
3. Ghi lại chính xác tên artifact và version `latest`.
4. Chuyển sang Bước 6.

Nếu chưa có:

1. Trong `Artifacts`, bấm dấu `+`.
2. `Name`: nhập `dms-hmi-android`.
3. `Category`: chọn `ANDROID IMAGE`.
4. `Description`: nhập `Android HMI for DMS safety demo`.
5. Bấm `Create`.
6. Bấm artifact vừa tạo → `Add Version`.
7. Chọn version.
8. Chọn đúng image/package theo định dạng CarSky yêu cầu.
9. Bấm `Upload` và đợi `latest`.

Không có image hợp lệ: **STOP — HMI member phải build/cung cấp image. AI coding agent có thể viết app nhưng con người phải xác nhận app chạy và âm thanh phát trên Android.**

## 6. Tạo Blueprint

### 6.1 Tạo Blueprint rỗng

1. Bấm `Nydus` ở thanh trái.
2. Bấm nút dấu `+`/menu phía trên; rê chuột thấy `Blueprint actions`.
3. Bấm `New Blueprint`.
4. `Name`: nhập `dms-driver-safety-hmi-v1`.
5. `Description (optional)`: nhập `KUKSA signals to Android DMS HMI`.
6. Bấm `Create`.
7. Bấm Blueprint vừa tạo trong danh sách.

Màn hình editor phải có palette `Nodes` và Inspector `BLUEPRINT`.

### 6.2 Thêm KUKSA Broker

1. Trong palette `Nodes`, chọn `KUKSA Broker`.
2. Kéo `KUKSA Broker` vào vùng canvas giữa màn hình.
3. Bấm node vừa thả.
4. Trong Inspector, đặt tên `DMS Signal Broker`.
5. Chọn VSS artifact `dms-driver-safety-vss`.
6. Chọn version `latest` vừa upload.
7. Kiểm tra node có pin `kuksa`, direction `INPUT`.

### 6.3 Thêm Android HMI

1. Kéo `Skycraft` từ palette vào canvas.
2. Bấm node Android.
3. Đặt tên `DMS Android HMI`.
4. Chọn Android image artifact chứa app DMS.
5. Chọn version `latest`.
6. Tạo/chọn pin `vhal`, direction `OUTPUT`.
7. Mở properties và đăng ký 9 property ID: `0x21400400`, `0x21600409`,
   `0x2160040A`, `0x21200402`, `0x21200403`, `0x21200401`, `0x21200404`,
   `0x21200405`, `0x11600207`; area `0`.

### 6.4 Chọn đúng một cách nối

Ứng dụng hiện tại đọc Android Car API/VHAL, vì vậy dùng **Script Bridge**:

1. Kéo `Script Node` vào canvas.
2. Đặt tên `DMS HMI Bridge`.
3. Nối Broker `kuksa` → Script `kuksa`.
4. Tạo output `vhal` hoặc `eth` trên Script theo đúng app.
5. Nối Script output → Android input tương ứng.
6. Mở editor Script và thêm subscribe 14 signal.
7. Dán nguyên file `SE/BE/carsky/dms_hmi_bridge.lua`, nhấn `Ctrl/Cmd+S`.

Không nối `kuksa` thẳng vào `vhal` nếu chưa có bridge chuyển protocol.

### 6.5 Kiểm tra trước Deploy

1. Bấm từng node và kiểm tra artifact/version không trống.
2. Kiểm tra đường nối không màu đỏ và không treo một đầu.
3. Trong Inspector `BLUEPRINT`, kiểm tra Name đúng.
4. Không bật `Locked` trước khi cấu hình xong.
5. Nếu muốn chống sửa nhầm sau khi hoàn tất, bật `Locked`.

CarSky editor lưu thay đổi tự động. PASS khi reload trang mà node và dây vẫn còn.

## 7. Tạo Device và Deployment

### 7.1 Chỉ tạo Device khi chưa có device dành cho DMS

1. Bấm `Devices`.
2. Kiểm tra danh sách có device được trưởng nhóm chỉ định hay chưa.
3. Nếu đã có, không bấm dấu `+`.
4. Nếu chưa có và đã được phép tạo, bấm dấu `+` **một lần**.
5. Portal tạo ngay device với tên ngẫu nhiên.
6. Ghi lại tên device vừa tạo.

Muốn đổi/xoá phải dùng menu chuột phải. Không tạo nhiều device để thử.

### 7.2 Deploy Blueprint

1. Bấm `Nydus`.
2. Bấm `dms-driver-safety-hmi-v1`.
3. Trong Inspector bên phải, tìm `DEPLOYMENTS`.
4. Bấm `New Deployment`.
5. Form `Deploy Blueprint` xuất hiện.
6. Tại `Deployment Name`, nhập `dms-hmi-demo-01`.
7. Tại `Device`, mở dropdown `Select a device...`.
8. Chọn đúng device đã được nhóm chỉ định.
9. Không bấm `+ Create new device` nếu device đã tồn tại.
10. Bấm `Deploy`.
11. Chờ deployment xuất hiện dưới Blueprint.

### 7.3 Đợi deployment thật sự sẵn sàng

1. Bấm `Dashboard`.
2. Chọn `dms-hmi-demo-01` nếu có bộ chọn deployment.
3. Nhìn dòng trạng thái và `nodes ready`.
4. Bấm `Refresh` nếu số node không thay đổi.
5. Chỉ PASS khi KUKSA Broker, Android HMI và Script Bridge (nếu dùng) đều `Running` và đủ node ready.
6. Nếu node có badge lỗi, bấm badge để mở logs.

- `Pending`: chờ hoặc thiếu tài nguyên.
- `ImagePullBackOff`: sai image/version/registry.
- `CrashLoopBackOff`: app hoặc cấu hình node bị lỗi.
- `Deploying... (9/21)`: chưa hoàn tất, không PASS.

## 8. Kết nối Device và thêm widget

1. Bấm `Devices`.
2. Tìm đúng device có dòng deployment `dms-hmi-demo-01` bên dưới.
3. Bấm `Connect` ở đúng card đó.
4. Chờ thanh trạng thái dưới cùng không còn `No device connected`.
5. Bấm mũi tên `Expand` bên phải card nếu danh sách widget chưa hiện.
6. Mở `Manage Widgets` hoặc nút thêm widget trong device đã kết nối.
7. Thêm `Signal Watch`.
8. Chọn node `DMS Signal Broker`.
9. Chọn 14 signal ở Bước 1.
10. Xác nhận/Save widget.
11. Mở lại `Manage Widgets`.
12. Thêm `Screen`.
13. Chọn node `DMS Android HMI`.
14. Xác nhận/Save widget.
15. Nếu có Script Bridge, thêm `Logs` cho `DMS HMI Bridge`.

PASS khi:

- Signal Watch hiện danh sách signal.
- Screen hiện màn hình Android, không phải nền đen/loading vô hạn.
- App DMS đang ở trạng thái NORMAL.

Nếu chỉ thấy `Connect to view widgets`, device chưa được kết nối. Nếu nút Connect thất bại, quay về Dashboard sửa deployment trước.

## 9. Lấy Room ID và node key

Sau khi credential/token flow đã được CarSky xác nhận, dùng Signals API theo tài liệu kỹ thuật:

```bash
export CARSKY_BASE_URL='https://hackathon-1.carsky.io'
export CARSKY_ACCESS_TOKEN='<api-key-tạo-trong Settings/Credentials>'
export CARSKY_ROOM_ID='<room-id-của-dms-hmi-demo-01>'
export CARSKY_SIGNAL_NODE_KEY='<node-key-của-DMS-Signal-Broker>'
export CARSKY_ANDROID_NODE_KEY='<node-key-của-DMS-Android-HMI>'
```

Không commit các giá trị này. Room ID/node key lấy từ deployment/Room inspector hoặc API deployment mà CarSky cung cấp. Không dùng tên hiển thị thay cho ID.

Kiểm tra signal:

```bash
curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CARSKY_ACCESS_TOKEN}" \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_SIGNAL_NODE_KEY}"
```

Nếu credential của môi trường thực tế yêu cầu header khác, thay header theo OpenAPI/CarSky admin; không tự thử secret trên nhiều kiểu header.

PASS khi response có đủ 14 signal.

## 10. Gửi bộ dữ liệu kiểm tra

Endpoint ghi signal:

```text
POST /api/v1/signals/{roomId}/{nodeKey}/actuate
```

### 10.1 NORMAL

```json
{"signals":[
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
]}
```

Kỳ vọng: màn hình bình thường, không alarm, `AI ONLINE`.

### 10.2 WARNING

```json
{"signals":[
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
]}
```

Kỳ vọng: vàng/cam, `TẬP TRUNG PHÍA TRƯỚC`, voice phát đúng một lần; gửi lại trong 15 giây không đọc lặp.

### 10.3 CRITICAL

```json
{"signals":[
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
]}
```

Kỳ vọng: đỏ, `NGUY CƠ VA CHẠM — TTC 1.2s`, `PHANH AN TOÀN`, tone ngắn và voice critical ưu tiên.

Gửi bằng curl:

```bash
curl --fail-with-body --silent --show-error -X POST \
  -H "Authorization: Bearer ${CARSKY_ACCESS_TOKEN}" \
  -H 'Content-Type: application/json' \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}/${CARSKY_SIGNAL_NODE_KEY}/actuate" \
  --data @payload.json
```

Lưu đúng một block JSON trên vào `payload.json` rồi chạy lệnh. Sau mỗi test, nhìn đồng thời Signal Watch và Screen.

## 11. Test voice, mute, recovery và offline

1. Gửi WARNING: voice phải đọc một lần.
2. Gửi WARNING lại ngay: không đọc lặp.
3. Gửi CRITICAL: warning voice bị ngắt, critical voice/tone phát.
4. Trên HMI bấm `VOICE MUTED`.
5. Gửi lại CRITICAL: không speech; visual đỏ và safety tone vẫn còn.
6. Bật lại `VOICE ON`.
7. Gửi NORMAL với transition `END`.
8. HMI chuyển `RECOVERY`, tắt alarm rồi về `NORMAL`.
9. Gửi `AIStatus=DEGRADED`, `DataAgeMs=2000`: hiện `AI DEGRADED`.
10. Gửi `AIStatus=OFFLINE`, `DataAgeMs=4000`: hiện `AI OFFLINE`, ẩn TTC cũ.
11. Gửi NORMAL để trả hệ thống về trạng thái an toàn.

Voice online/TTS chỉ được coi là phần tăng cường. Demo chính phải có fallback câu cố định/audio local để vẫn hoạt động khi mất Internet hoặc API TTS lỗi.

## 12. Chụp bằng chứng

1. Gửi CRITICAL.
2. Mở widget `Screen` tối đa.
3. Chụp ảnh thấy rõ cảnh báo đỏ, risk, TTC và hành động khuyến nghị.
4. Chụp thêm Dashboard thấy các node Running.
5. Chụp Signal Watch thấy giá trị tương ứng.
6. Không để token/secret xuất hiện trong ảnh.

Nếu API screenshot được bật:

```bash
curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CARSKY_ACCESS_TOKEN}" \
  "${CARSKY_BASE_URL}/api/v1/vms/${CARSKY_ROOM_ID}/${CARSKY_ANDROID_NODE_KEY}/screenshot" \
  --output /tmp/dms-hmi-critical.png
```

## 13. Gắn vào Backend

`.env` local:

```dotenv
CARSKY_ENABLED=true
CARSKY_MODE=external
CARSKY_BASE_URL=https://hackathon-1.carsky.io
CARSKY_API_KEY=<api-key>
CARSKY_AUTH_MODE=bearer
CARSKY_ROOM_ID=<room-id>
CARSKY_NODE_KEY=<signal-node-key>
CARSKY_ANDROID_NODE_KEY=<android-node-key>
CARSKY_TIMEOUT_SEC=1.5
```

Backend phải:

- Nhận AI frame ở 20 FPS nhưng không gọi CarSky/TTS 20 lần mỗi giây.
- Chỉ publish khi giá trị hiển thị thay đổi hoặc theo nhịp throttle.
- Gửi `START/UPDATE/END` theo episode cảnh báo.
- Timeout/retry có giới hạn; CarSky lỗi không làm REST/WebSocket chính đứng.
- Không retry vô hạn lỗi `401/403`.
- Không log access token/client secret.

### Lệnh vận hành đã chuẩn bị

Chạy từ `SE/BE`; công cụ tự đọc `.env` và không in API key:

```bash
.venv/bin/python scripts/carsky_phase05.py status
.venv/bin/python scripts/carsky_phase05.py nodes
.venv/bin/python scripts/carsky_phase05.py install-apk ../HMI/app/build/outputs/apk/debug/app-debug.apk
.venv/bin/python scripts/carsky_phase05.py scenario normal
.venv/bin/python scripts/carsky_phase05.py scenario warning
.venv/bin/python scripts/carsky_phase05.py scenario critical
.venv/bin/python scripts/carsky_phase05.py screenshot /tmp/dms-hmi-critical.png
```

Không chạy `install-apk`, `scenario` hoặc `screenshot` trước khi `status` trả `RUNNING` và
`nodes` có đúng Broker, Bridge và Android node.

## 14. Checklist nghiệm thu cuối

- [ ] Đăng nhập và thấy đúng workspace.
- [x] Credential Backend đã tạo và lưu trong `.env` bị ignore.
- [x] VSS artifact có version `0.0.2` và đủ 14 signal.
- [x] APK DMS đã build; Android image `aaos 0.0.1` đã chọn.
- [x] Blueprint có Broker + Android HMI + Script Bridge.
- [x] Blueprint validation PASS và VHAL có đủ 9 properties HMI sử dụng.
- [ ] Deployment đạt đủ node ready; không còn `Deploying`.
- [ ] Device kết nối được.
- [ ] Signal Watch đọc được signal.
- [ ] Screen hiện app DMS.
- [ ] NORMAL đúng.
- [ ] WARNING đúng và không đọc voice lặp.
- [ ] CRITICAL đúng, ưu tiên voice/tone.
- [ ] Mute và recovery đúng.
- [ ] AI DEGRADED/OFFLINE đúng.
- [ ] Có ba ảnh bằng chứng: Dashboard, Signal Watch, Screen.
- [ ] Backend replay không bị chặn khi CarSky lỗi.

```text
FINAL PASS = deployment healthy + signal đúng + HMI đúng + voice/fallback đúng + reset đúng + có bằng chứng
```

## 15. Việc AI làm được và việc bắt buộc con người xác nhận

AI coding agent làm được:

- Tạo VSS JSON.
- Viết CarSky client, mapping, throttle, retry và test.
- Viết app HMI, state machine, TTS/fallback audio và test logic.
- Tạo payload NORMAL/WARNING/CRITICAL.
- Phân tích log và đề xuất sửa Blueprint/config.

Con người phải nhúng tay:

- Giữ credential/secret và cấp quyền đúng.
- Chọn đúng device của nhóm; tránh phá tài nguyên người khác.
- Xác nhận Android image/app tương thích với CarSky.
- Xác nhận protocol thực tế giữa KUKSA và Android (`kuksa`, `vhal` hay `eth`).
- Nghe loa thật, kiểm tra tiếng Việt, âm lượng và mute.
- Xác nhận UX không làm tài xế mất tập trung.
- Chấp nhận kết quả cuối trên Screen/HMI thật.

## 16. Trạng thái workspace đã quan sát

Tại thời điểm đối chiếu:

- Có device riêng `DMS Driver Safety HMI`.
- Có Blueprint riêng `DMS Driver Safety HMI UI` đã validation PASS.
- Deployment DMS cũ đã được dọn; lần deploy mới dừng trước khi tạo Room vì VSS private.
- Blueprint `FPTU DMS Vision` chỉ dùng làm tài liệu đối chiếu image/VHAL; không sửa.
- Có sẵn artifact mẫu `vss` version `0.0.1` với file `vss_full_demo.json`.
- Có artifact Android mẫu `aaos`.

Đây chỉ là tài nguyên tham khảo. Không mặc định chúng đã chứa 14 signal DMS hoặc app HMI của nhóm. Kiểm tra nội dung trước khi tái sử dụng.
