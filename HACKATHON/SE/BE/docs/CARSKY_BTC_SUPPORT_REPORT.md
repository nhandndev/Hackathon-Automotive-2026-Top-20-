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

```text
CarSky URL: https://hackathon-1.carsky.io
Team account: dmsvision@hackathon.fpt.com
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
    }
  }
}
```

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
