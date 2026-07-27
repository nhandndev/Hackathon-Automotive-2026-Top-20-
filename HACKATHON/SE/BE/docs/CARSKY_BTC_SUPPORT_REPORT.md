<<<<<<< Updated upstream
# Báo cáo gửi BTC - Sự cố KUKSA/VSS của DMS Driver Safety HMI

## 1. Tóm tắt ngắn

Nhóm DMS Vision đã xác nhận nguyên nhân chính theo phản hồi của BTC: file tín hiệu `dms-vss-signals.json` trong artifact `dms-driver-safety-vss` bản cũ đang có sai định dạng dữ liệu.

Lỗi BTC ghi nhận:

```text
Error: ParseError("invalid type: sequence, expected a map at line 1 column 1")
```

Diễn giải:

- File VSS cũ đang được lưu ở dạng JSON array, bắt đầu bằng `[...]`.
- `kuksa-databroker` yêu cầu file VSS là JSON object/map, bắt đầu bằng `{...}`.
- Vì vậy `DMS Signal Broker` không khởi động được, kéo theo `DMS HMI Bridge` không fetch được metadata KUKSA và HMI không có signal.

## 2. Môi trường kiểm tra
=======
# Báo cáo gửi BTC - Sự cố CarSky/Nydus của DMS Driver Safety HMI

## Tóm tắt

Nhóm DMS Vision đang bị chặn ở tầng runtime/provisioning của CarSky/Nydus.
Backend, AI contract, Lua bridge, Android APK và blueprint validation hiện chưa
phải nguyên nhân chính.

Deployment tạo được, nhưng các runtime node không đạt trạng thái ready.

Triệu chứng chính:

```text
Deployment status: DEPLOYING
Nodes ready: 0/3
KUKSA Broker: Provisioning / Pending / PodInitializing
Skycraft Android: Provisioning / Pending / PodInitializing
Script Node: container running, sidecar waiting
```

Nhóm cần BTC kiểm tra Kubernetes events, init-container, generated pod spec,
image pull, volume mount, registry/runtime configuration và Nydus readiness
sidecar.

## Môi trường
>>>>>>> Stashed changes

```text
CarSky URL: https://hackathon-1.carsky.io
Team account: dmsvision@hackathon.fpt.com
<<<<<<< Updated upstream
Ngày cập nhật report: 2026-07-27
```

Report này không chứa password, API key hoặc secret.

## 3. Tài nguyên liên quan

```text
Device BTC dùng để test:
- Name: FPTU DMS Vision
- Device ID / room ID: 97fg4ghsgeo9w4bvze3qq

Artifact VSS của nhóm:
- Name: dms-driver-safety-vss
- Artifact ID: Q4ruRJhflspQoU0SY1l2f

Version cũ bị nghi lỗi:
- Version: 0.0.3
- Version ID: Gf_KU8fO-yAnonHE8gNe7

Version mới đã tạo metadata:
- Version: 0.0.4
- Version ID: 91420fac-3220-46a0-aaff-577c656637ee
- File path: Q4ruRJhflspQoU0SY1l2f/0.0.4/signal_db/dms-vss-signals.json

Blueprint cũ:
- Name: DMS Driver Safety HMI UI
- Blueprint ID: UEvNecDPUDgmOwo6-dA48
- Broker vẫn trỏ tới VSS version 0.0.3

Blueprint fixed đã tạo:
- Name: DMS Driver Safety HMI UI - Fixed VSS 0.0.4
- Blueprint ID: 7010b280-57ed-4b1e-b018-281481f0b377
- Validate: valid=true, errors=[]

Deployment fixed đã tạo:
- Name: DMS HMI Fixed VSS 0.0.4 Deploy
- Deployment ID: 5daed932-96f1-4c0f-8ef3-d444c054ec11
- Room ID: 97fg4ghsgeo9w4bvze3qq
- Namespace: room-snr5j54l
```

## 4. Việc nhóm đã sửa

Nhóm đã tạo lại file VSS local đúng dạng object/map tại:

```text
SE/BE/carsky/dms-vss-signals.json
```

File mới bắt đầu bằng object:

```json
{
  "Vehicle": {
    "type": "branch",
    "children": {
      "Speed": {
        "type": "sensor",
        "datatype": "float"
      }
=======
Ngày kiểm tra: 2026-07-26
```

Báo cáo này không chứa password, API key hoặc secret.

## Tài nguyên liên quan

```text
Device đã test:
- FPTU DMS Vision
- Device ID / room ID: 97fg4ghsgeo9w4bvze3qq

Blueprint DMS của nhóm:
- Tên: DMS Driver Safety HMI UI
- Blueprint ID: UEvNecDPUDgmOwo6-dA48

Deployment DMS mới nhất trên device FPTU:
- Tên: DMS HMI on FPTU Device
- Deployment ID: 17738907-0a7c-49bc-b94c-b913d9d06812
- Namespace thấy ban đầu: room-rxc03zqo
- Namespace thấy sau restart/reconcile node: room-x8jf4fn6

Blueprint mẫu của BTC:
- Tên: FPTU DMS Vision
- Blueprint ID: F7C8MDoL9KziX745upJYY

Blueprint chẩn đoán tối giản:
- Tên: DMS Broker Schema-less Atomic
- Mục đích: chỉ có một KUKSA Broker, không VSS artifact, không prefix
```

## Những gì nhóm đã kiểm tra

### 1. Script Node Health Test

Nhóm tạo một Script Node health test tối giản với một VHAL pin. Node này có chạy
được Lua và có in health log:

```text
Loaded config: script=/config/inline, pins=1
[vhal-grpc] starting VehicleServer on unix:/run/nydus/ingress-health_vhal.sock
[vhal-grpc] grpcio listening on 127.0.0.1:<dynamic-port>
[lua] DMS_DEVICE_HEALTH_STARTED
Script loaded: /config/inline
Starting event loop with 1 pins, 0 sockets, 0 someip request handlers
[lua] DMS_DEVICE_HEALTH_OK
```

Tuy nhiên process/script có dấu hiệu restart hoặc reload khoảng mỗi 150 giây:

```text
14:58:58 STARTED
15:01:28 STARTED
15:03:58 STARTED
15:06:28 STARTED
15:08:58 STARTED
15:11:28 STARTED
15:13:58 STARTED
```

Điều này cho thấy container script-node có thể chạy, nhưng readiness hoặc sidecar
lifecycle của Nydus có thể vẫn chưa healthy.

### 2. KUKSA Broker tối giản

Nhóm đã test blueprint chỉ có một node `kuksa-databroker`:

```text
Blueprint validation: valid=true
Deployment namespace: tạo được
Node phase: Provisioning
Pod phase: Pending
Container: kuksa-databroker waiting
Log API: PodInitializing
Signals API: nodes=[]
```

Kết quả tương tự vẫn xảy ra kể cả khi không cấu hình VSS artifact. Vì vậy vấn đề
không có vẻ đến từ nội dung DMS VSS artifact của nhóm.

### 3. KUKSA Broker dùng VSS artifact của blueprint BTC

Nhóm cũng đã test KUKSA với VSS artifact được blueprint BTC `FPTU DMS Vision`
tham chiếu:

```text
artifactId: zsJexrIgGwIeyk3ODyYoh
versionId: Cpi8WkMz_bH35uIQFviim
version: 0.0.1
```

Kết quả vẫn là:

```text
KUKSA Broker: Provisioning / Pending / PodInitializing
```

### 4. Topology DMS HMI 3 node

Blueprint DMS HMI của nhóm validate thành công:

```text
Blueprint: DMS Driver Safety HMI UI
Blueprint ID: UEvNecDPUDgmOwo6-dA48
Validation: valid=true
```

Deployment được tạo trên device `FPTU DMS Vision`:

```text
Deployment ID: 17738907-0a7c-49bc-b94c-b913d9d06812
Initial namespace: room-rxc03zqo
Status sau 60 giây: DEPLOYING
Nodes ready: 0/3
```

Chi tiết runtime node:

```text
DMS Signal Broker
- nodeType: kuksa-databroker
- phase: Provisioning
- pod phase: Pending
- container: kuksa-databroker waiting
- log API: PodInitializing

DMS HMI Bridge
- nodeType: script-node
- phase: Provisioning
- pod phase: Running
- container: script-node running
- container: sidecar waiting
- live log API không chọn được container, API trả lỗi yêu cầu chọn một trong:
  script-node, sidecar

DMS Android HMI
- nodeType: skycraft
- phase: Provisioning
- pod phase: Pending
- container: skycraft waiting
- log API: PodInitializing
```

### 5. Restart riêng Broker

Nhóm đã thử restart runtime node của `DMS Signal Broker`:

```text
Runtime node key: n-1408douatrkcwxba9bm3d-n0
Restart endpoint result: 500 Internal server error
```

Sau restart, CarSky tạo thêm pod Broker mới:

```text
Old pod: n-1408douatrkcwxba9bm3d-n0-64ddc6cb98-dtcnz
New pod: n-1408douatrkcwxba9bm3d-n0-5f5dccc7d-lcnwz
```

Pod mới vẫn ở trạng thái:

```text
phase: Pending
container: kuksa-databroker waiting
log API: PodInitializing
```

## Config Broker quan sát được từ Blueprint

Config của `DMS Signal Broker` trong blueprint chỉ chứa tham chiếu VSS artifact:

```json
{
  "kuksa": {
    "vss": {
      "artifactId": "Q4ruRJhflspQoU0SY1l2f",
      "versionId": "Gf_KU8fO-yAnonHE8gNe7",
      "version": "0.0.3"
>>>>>>> Stashed changes
    }
  }
}
```

<<<<<<< Updated upstream
File mới không còn dạng array:

```json
[
  {
    "path": "Vehicle.Speed"
  }
]
```

Nhóm đã validate JSON local thành công bằng:

```bash
python -m json.tool SE/BE/carsky/dms-vss-signals.json
```

Các signal chính trong file mới:

- `Vehicle.Speed`
- `Vehicle.SpeedLimit`
- `Vehicle.Driver.State`
- `Vehicle.Driver.AlertnessScore`
- `Vehicle.ADAS.MinTTC`
- `Vehicle.ADAS.Headway`
- `Vehicle.ADAS.FinalRiskScore`
- `Vehicle.ADAS.CriticalAlert`
- `Vehicle.ADAS.DisplaySeverity`
- `Vehicle.ADAS.AlertReasonCode`
- `Vehicle.ADAS.RecommendedActionCode`
- `Vehicle.ADAS.EventTransition`
- `Vehicle.ADAS.AIStatus`
- `Vehicle.ADAS.DataAgeMs`

## 5. Việc đã làm trên CarSky

Nhóm đã tạo artifact version metadata mới:

```text
Artifact: dms-driver-safety-vss
Version: 0.0.4
Version ID: 91420fac-3220-46a0-aaff-577c656637ee
Size khai báo: 4110 bytes
```

Nhóm đã tạo blueprint mới trỏ Broker tới VSS `0.0.4`:

```text
DMS Driver Safety HMI UI - Fixed VSS 0.0.4
Blueprint ID: 7010b280-57ed-4b1e-b018-281481f0b377
Validation: valid=true
```

Nhóm đã xóa deployment cũ đang kẹt và deploy lại vào device `FPTU DMS Vision`:

```text
Deployment mới: DMS HMI Fixed VSS 0.0.4 Deploy
Deployment ID: 5daed932-96f1-4c0f-8ef3-d444c054ec11
Room ID: 97fg4ghsgeo9w4bvze3qq
Namespace: room-snr5j54l
```

## 6. Trạng thái runtime mới nhất

Sau khi deploy bản fixed, trạng thái ghi nhận:

```text
Deployment status: DEPLOYING
Namespace: room-snr5j54l
```

Node status:

```text
DMS HMI Bridge: Running
DMS Android HMI: Running
DMS Signal Broker: Provisioning / Pending / PodInitializing
```

Pod status:

```text
Bridge pod:
- script-node: running, ready=true
- sidecar: running, ready=true

Android pod:
- skycraft: running, ready=true

Broker pod:
- kuksa-databroker: waiting
- pod phase: Pending
```

Khi đọc log Broker:

```text
container "kuksa-databroker" is waiting to start: PodInitializing
```

Hiện chưa thấy log parse mới của Broker vì container chính chưa start tới bước ghi log ứng dụng.

## 7. Điểm còn bị chặn

OpenAPI CarSky hiện cho phép tạo artifact version metadata qua:

```text
POST /api/v1/artifacts/{id}/versions
```

Nhưng OpenAPI không thấy endpoint upload nội dung file artifact lên storage. Vì vậy nhóm đã tạo được version `0.0.4` ở metadata, nhưng chưa xác nhận được chắc chắn file bytes `dms-vss-signals.json` đã thật sự nằm trong artifact storage.

Nhóm cũng thử đường vòng ghi file vào container qua:

```text
POST /api/v1/deployments/{roomId}/container-file/{nodeKey}
```

Kết quả:

```text
SERVICE_UNAVAILABLE: Conduit service not configured
```

Vì vậy nhóm chưa thể tự push file vào pod bằng API hiện tại.

## 8. Nhận định hiện tại

Nhóm đã sửa đúng lỗi dữ liệu VSS ở phía project local và đã tạo blueprint fixed dùng version `0.0.4`.

Tuy nhiên, để Broker chạy thật, cần xác nhận một trong hai việc sau:

1. Artifact version `0.0.4` đã có file bytes thật trên CarSky storage.
2. Nếu chưa có, cần BTC hướng dẫn hoặc cấp endpoint/cách upload file bytes cho artifact version.

Nếu artifact `0.0.4` chỉ có metadata mà không có file thật, Broker có thể tiếp tục kẹt ở bước mount/init artifact và không bao giờ vào log app.

## 9. Yêu cầu hỗ trợ từ BTC

Nhờ BTC hỗ trợ kiểm tra các mục sau trong namespace:

```text
namespace: room-snr5j54l
broker pod: n-3d8f2bce-9cef-49ef-85e8-3a46e9856017-*
```

Cần BTC kiểm tra:

1. Kubernetes event của Broker pod.
2. Init container hoặc artifact mount step của Broker pod.
3. File artifact được mount vào container có tồn tại không.
4. Nội dung file mounted VSS có bắt đầu bằng `{` không, hay vẫn là `[`.
5. CarSky có endpoint hoặc UI flow nào để upload bytes cho artifact version `0.0.4` không.
6. `kuksa-databroker` đang đọc file ở path nào trong container.
7. Nếu Broker còn lỗi parse, gửi lại 20-50 dòng log đầu tiên sau khi container start.

## 10. Câu hỏi cụ thể gửi BTC

Nhóm đề xuất gửi BTC nội dung ngắn sau:

```text
Hi BTC, team DMS đã sửa file VSS từ JSON array sang JSON object/map theo lỗi BTC báo.

Team đã tạo artifact version mới:
- Artifact: dms-driver-safety-vss
- Artifact ID: Q4ruRJhflspQoU0SY1l2f
- Version: 0.0.4
- Version ID: 91420fac-3220-46a0-aaff-577c656637ee
- File path khai báo: Q4ruRJhflspQoU0SY1l2f/0.0.4/signal_db/dms-vss-signals.json

Team cũng đã tạo blueprint fixed:
- DMS Driver Safety HMI UI - Fixed VSS 0.0.4
- Blueprint ID: 7010b280-57ed-4b1e-b018-281481f0b377
- Validate: valid=true

Deployment mới:
- DMS HMI Fixed VSS 0.0.4 Deploy
- Deployment ID: 5daed932-96f1-4c0f-8ef3-d444c054ec11
- Room ID: 97fg4ghsgeo9w4bvze3qq
- Namespace: room-snr5j54l

Hiện Bridge và Android đã Running, chỉ còn KUKSA Broker Pending/PodInitializing.
Nhờ BTC kiểm tra giúp Broker pod event/init-container/artifact mount và xác nhận version 0.0.4 đã có file bytes thật chưa. OpenAPI team dùng chỉ tạo được metadata version, chưa thấy endpoint upload file bytes.
```

## 11. Kết luận

Lỗi ban đầu là lỗi cấu hình VSS artifact của nhóm: file JSON dạng array thay vì object/map. Nhóm đã sửa file local, tạo version metadata mới và deploy blueprint fixed. Phần còn lại cần BTC xác nhận artifact storage/mount vì API hiện tại chưa cho nhóm upload hoặc kiểm tra trực tiếp file bytes trong artifact storage.
=======
Trong blueprint và repo của nhóm không thấy `CMD`, `ENTRYPOINT`, `--vss`,
`--grpc-port`, `RUST_LOG` hoặc `LOG_LEVEL`. Các tham số này có vẻ được CarSky/Nydus
generate ở runtime. Nhóm không thể tự xác nhận hoặc patch từ workspace hiện tại.

## Vấn đề với blueprint mẫu của BTC

Nhóm thử deploy lại blueprint mẫu `FPTU DMS Vision` của BTC. Deployment bị fail ở
bước preflight:

```text
invalid blueprint: node 'IVI - Android': skycraft requires 'image' config with VM image artifact details
```

Node `IVI - Android` trong blueprint này có vẻ đang dùng schema Skycraft cũ:

```json
{
  "prefix": "face",
  "gpuBackend": "virglrenderer",
  "displayHeight": 1080
}
```

Trong môi trường CarSky hiện tại, Skycraft node có vẻ cần thêm block `image` chứa
artifact/version details. Nhờ BTC xác nhận blueprint mẫu `FPTU DMS Vision` có còn
deploy lại được trên môi trường hiện tại hay không.

## Những nguyên nhân đã loại trừ

Hiện tại blocker không có vẻ đến từ:

- JSON output của AI.
- Backend REST/WebSocket.
- Nội dung Android APK.
- Lua script syntax.
- Script Node runtime cơ bản.
- Nội dung DMS VSS artifact riêng lẻ.
- Thiếu Skycraft image config trong DMS blueprint của nhóm.
- Blueprint validation failure.
- Một device lỗi riêng lẻ.

## Ảnh hưởng tới demo

Nhóm chưa thể hoàn tất demo HMI vì room chưa đạt runtime ready:

```text
Yêu cầu: Running 3/3 nodes ready
Hiện tại: DEPLOYING 0/3 nodes ready
```

Vì Android Skycraft node vẫn `PodInitializing`, nhóm chưa thể cài APK hoặc mở
Screen widget. Vì KUKSA Broker vẫn `PodInitializing`, nhóm chưa thể gửi hoặc xác
thực mock DMS signals.

## Nhờ BTC hỗ trợ kiểm tra

Nhờ BTC kiểm tra các điểm sau:

1. Kubernetes events của pod KUKSA Broker đang kẹt `PodInitializing`.
2. Kubernetes events của pod Skycraft đang kẹt `PodInitializing`.
3. Trạng thái init-container của `kuksa-databroker` và `skycraft`.
4. Trạng thái volume mount cho VSS artifact và Skycraft image/runtime dependency.
5. Image pull và registry credentials của `kuksa-databroker` và `skycraft`.
6. Generated pod spec của Broker, gồm command, args và env:
   `--vss`, `--grpc-port`, `RUST_LOG`, `LOG_LEVEL`.
7. Vì sao restart riêng Broker trả `500 Internal server error` nhưng vẫn tạo pod
   Broker mới ở trạng thái Pending.
8. Vì sao Script Node chạy được Lua health script nhưng sidecar/readiness không
   đạt ready.
9. Blueprint mẫu `FPTU DMS Vision` của BTC có đang outdated không, vì deploy lại
   bị fail do node `IVI - Android` thiếu Skycraft `image` config.

## Acceptance check sau khi BTC xử lý

Sau khi BTC fix runtime, nhờ xác nhận:

```text
1. Blueprint chỉ có một KUKSA Broker đạt 1/1 nodes ready.
2. Blueprint DMS HMI 3 node đạt 3/3 nodes ready.
3. /api/v1/deployments/{roomId}/nodes trả runtime nodes.
4. /api/v1/signals/{roomId} trả usable signal node.
5. Android/Skycraft node dùng được cho ADB/APK install.
```

## Nội dung có thể gửi BTC

```text
Chào BTC,

Nhóm em đang bị blocker ở CarSky/Nydus runtime provisioning. Blueprint DMS HMI
3-node validate thành công và deployment được tạo, nhưng room vẫn DEPLOYING
0/3 nodes ready. KUKSA Broker và Skycraft Android đều Pending/PodInitializing,
Script Node container chạy nhưng sidecar waiting.

Deployment cần BTC kiểm tra:
- Device: FPTU DMS Vision
- Device/room ID: 97fg4ghsgeo9w4bvze3qq
- Deployment ID: 17738907-0a7c-49bc-b94c-b913d9d06812
- Namespace từng thấy: room-rxc03zqo, sau restart/reconcile thấy room-x8jf4fn6
- Blueprint: DMS Driver Safety HMI UI
- Blueprint ID: UEvNecDPUDgmOwo6-dA48

Nhóm đã thử KUKSA với artifact DMS, artifact VSS của blueprint BTC và cả
schema-less không artifact; đều kẹt PodInitializing. Restart riêng Broker trả
500 Internal server error nhưng vẫn tạo thêm pod Broker mới, pod mới vẫn Pending.

Nhờ BTC kiểm tra Kubernetes events/init-container, volume mount, image pull,
registry/runtime và generated pod spec của kuksa-databroker/skycraft. Đồng thời
nhờ BTC xác nhận blueprint mẫu FPTU DMS Vision có đang outdated không, vì deploy
lại blueprint đó bị preflight fail: node 'IVI - Android' thiếu Skycraft image
config.

Tụi em chưa thể cài APK/gửi mock signal vì Android và KUKSA chưa ready.
```
>>>>>>> Stashed changes
