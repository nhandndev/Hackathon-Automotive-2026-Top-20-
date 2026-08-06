# Android HMI Fix — CarSky/SOVD/VHAL Multiplex

File này ghi lại quyết định fix Android HMI sau khi đối chiếu tài liệu/ảnh kiến trúc BTC.

## 1. Kết luận từ tài liệu BTC

BTC mô tả luồng tham chiếu:

```text
Team Application / Backend / AI
  -> CarSky Platform API
  -> SOVD Service
  -> MQTT topics scoped by VIN
  -> Vehicle / HPC / vECU
```

Ý nghĩa đối với DMS HMI:

- APK Android không nên tự gọi cloud REST trực tiếp nếu Android VM không có route mạng.
- Backend/AI nên gửi dữ liệu qua CarSky Platform/KUKSA/SOVD side.
- Android HMI nên chỉ đóng vai trò UI trong xe, đọc tín hiệu từ vehicle runtime/HPC/VHAL rồi render.

## 2. Lỗi cũ đã gặp

### 2.1 APK REST bị kẹt network

Android VM từng báo:

```text
ping hackathon-1.carsky.io
Destination Host Unreachable
No route to host
```

Vì vậy bản APK poll trực tiếp:

```text
https://hackathon-1.carsky.io/api/v1/signals/.../values
```

không đáng tin cậy cho demo trên CarSky Android Screen.

### 2.2 Custom VHAL property không expose đủ

Khi kiểm tra Android CarService:

```sh
dumpsys car_service | grep -iE "557843456|559940617|559940618|555746306|555746307|555746308|555746309|291504647"
```

Kết quả ổn định chỉ thấy:

```text
291504647 = 0x11600207 = PERF_VEHICLE_SPEED
```

Các custom DMS property như Risk, AIStatus, Alertness, DriverState không expose ổn định trong Android `CarPropertyService`.

## 3. Fix hiện tại

Luồng runtime sau khi fix:

```text
AI/Backend
  -> CarSky KUKSA signal
  -> dms_hmi_bridge.lua
  -> VHAL PERF_VEHICLE_SPEED multiplex
  -> Android CarPropertyManager
  -> DMS Android HMI
```

APK Android dùng 2 cơ chế đọc VHAL:

- `registerCallback(...)` để nhận event realtime từ `CarPropertyManager`.
- Polling fallback mỗi `250ms` bằng `getFloatProperty(PERF_VEHICLE_SPEED, 0)` để tránh trường hợp callback trên CarSky/AAOS bị chập chờn nhưng property thật vẫn đổi.

## 4. File đã sửa

```text
SE/BE/carsky/dms_hmi_bridge.lua
SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java
SE/HMI/app/build.gradle
SE/HMI/app/src/main/AndroidManifest.xml
SE/HMI/demo-live/build_demo_apk.sh
SE/HMI/demo-live/AndroidManifest.xml
```

## 5. Multiplex contract

Tất cả DMS state được encode vào property chuẩn:

```text
PERF_VEHICLE_SPEED = 291504647 = 0x11600207
```

Encoding:

| Signal gốc | Encoded value |
|---|---:|
| `Vehicle.Speed` | speed thật, ví dụ `75` |
| `Vehicle.ADAS.FinalRiskScore` | `10000 + risk`, ví dụ `10088` |
| `Vehicle.ADAS.DisplaySeverity` | `11000 + code` |
| `Vehicle.Driver.State` | `12000 + code` |
| `Vehicle.Driver.AlertnessScore` | `13000 + alertness*100` |
| `Vehicle.ADAS.MinTTC` | `14000 + ttc*10` |
| `Vehicle.ADAS.CriticalAlert` | `15000 + 0/1` |
| `Vehicle.ADAS.AIStatus` | `16000 + code` |
| `Vehicle.ADAS.RecommendedActionCode` | `17000 + code` |

Severity code:

```text
SAFE=0, WARNING=1, CRITICAL=2, RECOVERY=3
```

Driver code:

```text
alert=0, drowsy=1, yawning=2, distracted=3, microsleep=4
```

AI status:

```text
ONLINE=0, DEGRADED=1, OFFLINE=2
```

Action:

```text
NONE=0, FOCUS_FORWARD=1, TAKE_BREAK=2, BRAKE_SAFE=3, REDUCE_SPEED=4
```

## 6. Cách verify đúng

### 6.0 Verify có producer nội bộ trong CarSky

BTC đã nhắc đúng một điểm: nếu blueprint chỉ có `KUKSA Broker -> HMI Bridge -> Android HMI`
thì trong topology chưa có node nào tự phát dữ liệu KUKSA. Khi demo/debug độc lập trong CarSky,
nên thêm một Script Node producer:

```text
DMS KUKSA Producer -> DMS Signal Broker -> DMS HMI Bridge -> DMS Android HMI
```

Script producer nằm tại:

```text
SE/BE/carsky/dms_kuksa_producer.lua
```

Cấu hình node:

- Type: `Script Node`
- Label: `DMS KUKSA Producer`
- Pin: `kuksa`, type `KUKSA`
- Edge: nối `DMS KUKSA Producer.kuksa` vào `DMS Signal Broker.kuksa`

Khi Restart node producer, log producer phải có:

```text
DMS_KUKSA_PRODUCER Vehicle.ADAS.FinalRiskScore=88
DMS KUKSA producer published 14 demo signals
```

Sau đó log `DMS HMI Bridge` phải có:

```text
DMS_HMI_MUX Vehicle.ADAS.FinalRiskScore=88 -> 10088 on 0x11600207
```

Nếu Signal Watch đổi nhưng Bridge không log, edge producer/broker/bridge chưa đúng.

### 6.1 Verify Bridge log

Sau khi deploy/redeploy blueprint, log `DMS HMI Bridge` phải có dạng:

```text
DMS_HMI_MUX Vehicle.ADAS.FinalRiskScore=88 -> 10088 on 0x11600207
DMS_HMI_MUX Vehicle.ADAS.DisplaySeverity=CRITICAL -> 11002 on 0x11600207
```

Nếu log vẫn là:

```text
DMS_HMI Vehicle.ADAS.FinalRiskScore=88 -> 0x21400400
```

thì blueprint vẫn đang dùng script cũ.

### 6.2 Verify APK log

Trong Android ADB:

```sh
logcat -c
am force-stop vn.fpt.dms.hmi
am start -n vn.fpt.dms.hmi/.MainActivity
logcat -d -s DMS_HMI:I AndroidRuntime:E
```

Kỳ vọng:

```text
Registered DMS multiplex transport on PERF_VEHICLE_SPEED with callback + polling fallback
mux raw=10088 group=10 payload=88
mux raw=11002 group=11 payload=2
```

### 6.3 Verify UI

Gửi critical:

```bash
cd SE/BE
CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
.venv/bin/python scripts/carsky_phase05.py scenario critical
```

Kỳ vọng HMI:

```text
AI ONLINE hoặc AI DEGRADED
NGUY HIEM hoặc CANH BAO
Risk != 0
Alertness != 0
TTC != 0
```

## 7. Lưu ý quan trọng

- Không quay lại bản APK hardcode `VALUES_URL` gọi CarSky REST trực tiếp.
- Không quay lại 9 custom Android CarProperty nếu `dumpsys car_service` chưa expose đủ property.
- Nếu BTC cung cấp SOVD/MQTT API thật, Backend nên tích hợp ở tầng CarSky/SOVD; APK vẫn giữ vai trò đọc vehicle runtime.
- Nếu cần chứng minh đúng kiến trúc BTC, trình bày flow:

```text
Backend/AI -> CarSky/KUKSA/SOVD side -> VHAL standard property -> Android HMI
```
