# Hướng dẫn thao tác fix KUKSA Broker trên CarSky

Mục tiêu cuối cùng: `DMS Signal Broker` phải chuyển sang `Running`, sau đó CarSky `/signals` thấy được các signal DMS và HMI mới có dữ liệu.

Làm đúng thứ tự. Bước nào không giống mô tả thì dừng lại, chụp màn hình/log gửi BTC hoặc hỏi lại team.

## 0. Lỗi hiện tại là gì

BTC đã xác nhận lỗi cũ của team DMS:

```text
Error: ParseError("invalid type: sequence, expected a map at line 1 column 1")
```

Nghĩa là file `dms-vss-signals.json` cũ đang là JSON array:

```json
[
  {
    "path": "Vehicle.Speed"
  }
]
```

Nhưng `kuksa-databroker` cần JSON object/map:

```json
{
  "Vehicle": {
    "type": "branch",
    "children": {}
  }
}
```

File đúng của project hiện nằm ở:

```text
SE/BE/carsky/dms-vss-signals.json
```

## 1. Chuẩn bị trước khi mở CarSky

Mở terminal tại root project:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
```

Kiểm tra file VSS đúng JSON:

```bash
SE/BE/.venv/bin/python -m json.tool SE/BE/carsky/dms-vss-signals.json >/tmp/dms-vss-signals.validated.json
```

Nếu command không báo lỗi là pass.

Mở nhanh file để nhìn dòng đầu:

```bash
sed -n '1,20p' SE/BE/carsky/dms-vss-signals.json
```

Dòng đầu phải là:

```json
{
```

Không được là:

```json
[
```

## 2. Đăng nhập CarSky

1. Mở browser.
2. Vào:

```text
https://hackathon-1.carsky.io/
```

3. Đăng nhập bằng tài khoản team.
4. Sau khi vào workspace, nhìn thanh trái có các mục:
   - Devices
   - Artifacts
   - Nydus
   - Dashboard

## 3. Upload lại VSS artifact đúng format

Đây là bước quan trọng nhất.

1. Ở thanh bên trái, bấm **Artifacts**.
2. Tìm artifact tên:

```text
dms-driver-safety-vss
```

3. Bấm vào artifact đó.
4. Tìm phần **Versions**.
5. Tạo version mới.
6. Đặt version:

```text
0.0.5
```

Nếu CarSky không cho `0.0.5`, dùng version lớn hơn version đang có, ví dụ:

```text
0.0.6
```

7. Khi CarSky yêu cầu upload file, chọn file:

```text
SE/BE/carsky/dms-vss-signals.json
```

8. Role/type nếu có chọn:

```text
signal_db
```

9. File name phải là:

```text
dms-vss-signals.json
```

10. Save/Upload.

Checklist pass:

- [ ] Version mới được tạo thành công.
- [ ] File upload là `dms-vss-signals.json`.
- [ ] File bắt đầu bằng `{`, không phải `[`.
- [ ] Role là `signal_db` nếu UI có field này.

Nếu UI chỉ tạo metadata mà không có nút chọn file thật, dừng lại và hỏi BTC:

```text
CarSky UI/API hiện chỉ cho tạo artifact version metadata, team chưa thấy cách upload file bytes.
Nhờ BTC chỉ giúp thao tác upload file bytes cho artifact VSS version mới.
```

## 4. Update Blueprint dùng VSS version mới

Nếu Codex đã tạo sẵn blueprint fixed thì ưu tiên dùng bản này:

```text
DMS Driver Safety HMI UI - Fixed VSS 0.0.4
Blueprint ID: 7010b280-57ed-4b1e-b018-281481f0b377
```

Nhưng nếu bạn vừa upload version mới `0.0.5`, cần sửa Broker sang `0.0.5`.

Thao tác:

1. Thanh bên trái bấm **Nydus**.
2. Ở danh sách blueprint, chọn:

```text
DMS Driver Safety HMI UI - Fixed VSS 0.0.4
```

Hoặc nếu muốn sửa bản gốc:

```text
DMS Driver Safety HMI UI
```

3. Trên canvas, bấm node:

```text
DMS Signal Broker
```

4. Nhìn panel **Inspector** bên phải.
5. Trong phần **Configuration**, tìm field:

```text
Artifact
Version
```

6. Artifact phải chọn:

```text
dms-driver-safety-vss
```

7. Version phải chọn version mới vừa upload:

```text
0.0.5
```

Hoặc nếu bạn dùng version Codex đã tạo metadata:

```text
0.0.4
```

8. Bấm save nếu UI có nút save.
9. Bấm **Done** ở góc trên nếu đang ở edit mode.

Checklist pass:

- [ ] Node `DMS Signal Broker` đang dùng artifact `dms-driver-safety-vss`.
- [ ] Version là version mới có file object/map.
- [ ] Không còn dùng version `0.0.3`.

## 5. Kiểm tra 3 node trong Blueprint

Trong **Nydus**, blueprint đúng phải có 3 node:

```text
DMS Signal Broker
DMS HMI Bridge
DMS Android HMI
```

Kiểm tra từng node:

### 5.1 DMS Signal Broker

1. Click node `DMS Signal Broker`.
2. Inspector bên phải phải là:

```text
Type: KUKSA Broker
Artifact: dms-driver-safety-vss
Version: version mới
Pins:
- kuksa: Server
```

### 5.2 DMS HMI Bridge

1. Click node `DMS HMI Bridge`.
2. Inspector bên phải phải là:

```text
Type: Script Node
Pins:
- kuksa: Client
- vhal: Server
```

3. Bấm **Edit Script**.
4. Script phải có mapping các path:

```text
Vehicle.Speed
Vehicle.ADAS.FinalRiskScore
Vehicle.ADAS.DisplaySeverity
Vehicle.Driver.State
Vehicle.Driver.AlertnessScore
Vehicle.ADAS.MinTTC
Vehicle.ADAS.CriticalAlert
Vehicle.ADAS.AIStatus
Vehicle.ADAS.RecommendedActionCode
```

5. Đóng script.

### 5.3 DMS Android HMI

1. Click node `DMS Android HMI`.
2. Inspector bên phải phải là:

```text
Type: Skycraft
OS: Android
Artifact: aaos
Version: 0.0.1
Architecture: aarch64 (ARM)
Pins:
- vhal: Client
```

## 6. Kiểm tra dây nối node

Trên canvas phải có 2 dây:

```text
DMS Signal Broker kuksa  ->  DMS HMI Bridge kuksa
DMS HMI Bridge vhal      ->  DMS Android HMI vhal
```

Nếu bị lỗi:

```text
addEdge: source or target pin not found
```

Thì đừng import file blueprint cũ nữa. Tạo lại bằng UI:

1. Xóa dây lỗi nếu có.
2. Kéo từ pin `kuksa` của `DMS Signal Broker`.
3. Thả vào pin `kuksa` của `DMS HMI Bridge`.
4. Kéo từ pin `vhal` của `DMS HMI Bridge`.
5. Thả vào pin `vhal` của `DMS Android HMI`.

## 7. Deploy lại

1. Ở Nydus, chọn blueprint fixed.
2. Nhìn panel phải, phần **Deployments**.
3. Nếu có deployment cũ đang `Pending`, `Deploying`, hoặc `Failed`, bấm vào deployment đó.
4. Bấm **Delete Deployment**.
5. Quay lại blueprint fixed.
6. Bấm **New Deployment**.
7. Chọn device:

```text
FPTU DMS Vision
```

8. Đặt tên deployment:

```text
DMS HMI Fixed VSS Deploy
```

9. Bấm deploy.

## 8. Chờ deploy bao lâu

Mốc thời gian hợp lý:

- 0-2 phút: `Pending` hoặc `Deploying` là bình thường.
- 2-5 phút: Android/Skycraft có thể vẫn đang kéo image.
- Sau 5 phút: ít nhất phải có 1-2 node `Running`.
- Sau 8-10 phút: nếu Broker vẫn `PodInitializing` hoặc `Pending` thì coi là kẹt.

Đừng chờ vô hạn.

## 9. Kiểm tra Dashboard

1. Thanh trái bấm **Dashboard**.
2. Ở góc trên, chọn deployment mới:

```text
DMS HMI Fixed VSS Deploy
```

3. Nhìn cards:

Pass mong muốn:

```text
DMS Signal Broker: Running
DMS HMI Bridge: Running
DMS Android HMI: Running
3/3 nodes ready
```

Nếu thấy:

```text
DMS Signal Broker: Pending / Provisioning
0/3 hoặc 2/3 nodes ready
```

Thì sang bước 10.

## 10. Xem log Broker

1. Thanh trái bấm **Nydus**.
2. Ở danh sách deployment bên trái, chọn deployment mới.
3. Trên canvas, click node:

```text
DMS Signal Broker
```

4. Panel phải bấm:

```text
View Logs
```

5. Đợi log hiện.

Nếu log có:

```text
ParseError("invalid type: sequence, expected a map at line 1 column 1")
```

Kết luận:

```text
Broker vẫn đang đọc file VSS dạng array hoặc đang đọc nhầm version cũ.
```

Cách xử lý:

- Quay lại Bước 3 upload lại file đúng.
- Quay lại Bước 4 kiểm tra Broker không dùng version `0.0.3`.

Nếu log không hiện và báo:

```text
container "kuksa-databroker" is waiting to start: PodInitializing
```

Kết luận:

```text
Broker chưa start được. Khả năng nằm ở artifact mount/init/image pull.
```

Gửi BTC đoạn này:

```text
Hi BTC, Broker của team đang kẹt PodInitializing nên chưa có log app.
Nhờ BTC kiểm tra event/init-container/artifact mount của pod KUKSA Broker.
Team đã upload VSS dạng object/map và đã chọn artifact version mới trong blueprint.
```

## 11. Kiểm tra signal sau khi Broker Running

Khi `DMS Signal Broker` đã `Running`, dùng terminal:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python scripts/carsky_phase05.py status
.venv/bin/python scripts/carsky_phase05.py nodes
```

Kết quả mong muốn:

```text
status: RUNNING
nodes: có DMS Signal Broker hoặc KUKSA signal node
```

Nếu script chưa đúng room/node, mở `.env` và cập nhật:

```text
CARSKY_ROOM_ID=97fg4ghsgeo9w4bvze3qq
CARSKY_NODE_KEY=<node key của DMS Signal Broker>
CARSKY_ANDROID_NODE_KEY=<node key của DMS Android HMI>
```

Node key hiện tại của deployment fixed:

```text
DMS Signal Broker: n-3d8f2bce-9cef-49ef-85e8-3a46e9856017
DMS HMI Bridge: fa2fba18-578a-4570-8a7b-4adb564452a0
DMS Android HMI: n-23eecfaa-0230-4c80-9242-7176bdac3c86
```

## 12. Gửi mock signal

Chỉ làm bước này khi Broker đã `Running`.

Gửi trạng thái an toàn:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python scripts/carsky_phase05.py send-safe
```

Gửi trạng thái cảnh báo:

```bash
.venv/bin/python scripts/carsky_phase05.py send-warning
```

Gửi trạng thái nguy hiểm:

```bash
.venv/bin/python scripts/carsky_phase05.py send-critical
```

Nếu script không có các command trên thì dùng API/script hiện tại của Backend để gửi các signal tương đương:

```text
Vehicle.Speed
Vehicle.Driver.State
Vehicle.Driver.AlertnessScore
Vehicle.ADAS.MinTTC
Vehicle.ADAS.FinalRiskScore
Vehicle.ADAS.CriticalAlert
Vehicle.ADAS.DisplaySeverity
Vehicle.ADAS.AIStatus
Vehicle.ADAS.RecommendedActionCode
```

## 13. Kiểm tra HMI

1. Thanh trái bấm **Devices**.
2. Chọn device:

```text
FPTU DMS Vision
```

3. Mở widget:

```text
Screen / IVI Screen
```

4. HMI phải hiển thị:

- Speed.
- Driver state.
- Alertness score.
- Risk score.
- TTC/headway nếu có.
- Severity: SAFE/WARNING/CRITICAL/RECOVERY.
- AI status.
- Recommended action.

Pass cuối:

```text
Broker Running
Signals readable
Mock signal gửi thành công
HMI đổi trạng thái theo mock signal
```

## 14. Nếu vẫn fail thì gửi BTC đúng đoạn này

```text
Hi BTC, team DMS đã làm lại VSS artifact đúng dạng object/map, không còn JSON array.

File local đã validate JSON:
SE/BE/carsky/dms-vss-signals.json

Blueprint fixed:
- DMS Driver Safety HMI UI - Fixed VSS 0.0.4
- Blueprint ID: 7010b280-57ed-4b1e-b018-281481f0b377
- Validate: valid=true

Deployment:
- DMS HMI Fixed VSS 0.0.4 Deploy
- Room ID: 97fg4ghsgeo9w4bvze3qq

Hiện trạng:
- Bridge Running
- Android Running
- KUKSA Broker vẫn Provisioning/Pending/PodInitializing

Nhờ BTC kiểm tra giúp:
1. Broker pod event.
2. Init container artifact mount.
3. File VSS mounted trong Broker có tồn tại không.
4. File mounted bắt đầu bằng `{` hay `[`.
5. CarSky UI/API upload artifact version có thật sự upload file bytes chưa.
```

