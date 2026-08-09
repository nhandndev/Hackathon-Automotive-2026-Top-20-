# Run Evidence - Output #007 Backend To CarSky To Android HMI

Mục tiêu: quay evidence cho `Output #007 - Backend To CarSky To Android HMI`.

Script sẽ dừng ở từng bước. Sau mỗi lần nhấn `Enter`, bạn làm đúng thao tác bên dưới để quay. Không deploy lại, không build lại APK, không sửa source code.

---

# 0. Mở Sẵn Trước Khi Quay

## Terminal Mac

Mở terminal tại project root:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
```

## CarSky UI

Mở CarSky deployment đang chạy.

Chuẩn bị sẵn các panel/tab:

```text
1. Blueprint view: thấy 3 node
   - DMS Signal Broker
   - DMS HMI Bridge
   - DMS Android HMI

2. Signal Watch / Browse Signals
   - Watch signal: Vehicle.Speed

3. Logs: DMS HMI Bridge

4. DMS Android HMI screen

5. Android shell/logcat nếu bạn muốn quay logcat
```

---

# 1. Chạy Script

Trong terminal Mac:

```bash
./scripts/show_output_007_carsky_hmi_evidence.sh
```

Khi script hiện:

```text
Press Enter to continue...
```

thì bạn bấm `Enter` để qua bước tiếp theo.

---

# 2. Step-By-Step Khi Quay

## Bước 1 - Backend Mapper / Vehicle.Speed Source Evidence

Sau khi bấm `Enter` lần đầu, script sẽ show source evidence cho backend mapper.

Bạn quay terminal và nói:

```text
Backend mapper publish DMS event bằng Vehicle.Speed speed-mux để CarSky/KUKSA nhận signal.
```

Khi terminal show xong các dòng trong `mapper.py`, `client.py`, `service.py`, bấm `Enter`.

---

## Bước 2 - HMI Bridge / VHAL Source Evidence

Script sẽ show bridge source evidence.

Bạn quay terminal và nói:

```text
HMI Bridge forward Vehicle.Speed sang VHAL PERF_VEHICLE_SPEED cho Android HMI.
```

Cần thấy các dòng như:

```text
PERF_VEHICLE_SPEED
Vehicle.Speed
DMS_HMI_SPEED_MUX
```

Sau đó bấm `Enter`.

---

## Bước 3 - Android APK Artifact Evidence

Script sẽ show APK file, SHA-256 và APK entries.

Bạn quay terminal và nói:

```text
Android HMI APK artifact tồn tại trong project, có hash, classes.dex, manifest và signing metadata.
```

Cần thấy:

```text
SE/HMI/release/dms-hmi-realtime-vhal.apk
SHA-256
AndroidManifest.xml
classes.dex
META-INF
```

Sau đó bấm `Enter`.

---

## Bước 4 - Android HMI Runtime Strings

Script sẽ extract `classes.dex` và show runtime strings.

Bạn quay terminal và nói:

```text
APK chứa runtime strings cho DMS_HMI, PERF_VEHICLE_SPEED, CarPropertyManager và các state hiển thị trên HMI.
```

Cần thấy:

```text
DMS_HMI
PERF_VEHICLE_SPEED
CarPropertyManager
SAFE
CRITICAL
TTC
km/h
```

Sau đó bấm `Enter`.

---

## Bước 5 - CarSky Deployment Status

Script sẽ gọi:

```bash
carsky_phase05.py status
carsky_phase05.py nodes
```

Bạn quay terminal và nói:

```text
Deployment đang RUNNING và có đủ 3 node: Signal Broker, HMI Bridge và Android HMI.
```

Cần thấy:

```text
status: RUNNING
DMS Android HMI
DMS Signal Broker
DMS HMI Bridge
phase: Running
```

Sau khi terminal show xong, **chuyển sang CarSky UI**.

Trong CarSky:

1. Mở blueprint/deployment view.
2. Quay rõ 3 node:

```text
DMS Signal Broker
DMS HMI Bridge
DMS Android HMI
```

3. Nếu có panel deployment status, quay `Running`.

Xong quay lại terminal và bấm `Enter`.

---

## Bước 6 - Chuẩn Bị Signal Watch Trước Khi Bắn Critical

Trước khi bấm `Enter` ở bước bắn critical, làm trong CarSky:

1. Mở `Signal Watch` hoặc `Browse Signals`.
2. Search/watch:

```text
Vehicle.Speed
```

3. Để màn hình Signal Watch đang thấy `Vehicle.Speed`.

4. Mở thêm một tab/panel khác nếu tiện:

```text
Logs: DMS HMI Bridge
```

5. Nếu quay được Android HMI screen thì để Android HMI visible.

Sau khi đã sẵn sàng, quay lại terminal và bấm `Enter`.

---

## Bước 7 - Send Critical Notification / Vehicle.Speed Speed-Mux

Script sẽ bắn:

```bash
.venv/bin/python scripts/carsky_phase05.py scenario critical
```

Bạn quay terminal.

Pass condition:

```text
"ok": true
"mode": "vehicle-speed-mux"
"sent": 14
```

Nếu thấy:

```text
Unknown signal path: Vehicle.Driver.State
```

thì nói:

```text
Custom VSS path không có trong deployment hiện tại, nên runtime fallback đúng sang Vehicle.Speed speed-mux.
```

Sau khi terminal show kết quả xong, **đừng bấm Enter vội**. Chuyển sang CarSky UI để quay runtime.

---

## Bước 8 - Quay Signal Watch

Trong CarSky `Signal Watch`, quay `Vehicle.Speed`.

Cần thấy một số giá trị kiểu:

```text
41.088
42.002
43.004
44.015
45.012
46.001
48.003
49.029
```

Nói:

```text
Signal Watch nhận Vehicle.Speed speed-mux từ Backend. Các giá trị 41.xxx đến 49.xxx là encoded DMS state.
```

Nếu Signal Watch chỉ thấy giá trị cuối, ví dụ `49.029`, vẫn nói:

```text
Signal Watch đang hiển thị giá trị cuối của burst speed-mux. Backend log cho thấy đã gửi đủ chuỗi critical mux values.
```

---

## Bước 9 - Quay HMI Bridge Log

Trong CarSky UI, mở:

```text
Logs: DMS HMI Bridge
```

Tìm dòng:

```text
DMS_HMI_SPEED_MUX
Vehicle.Speed=41.088
Vehicle.Speed=42.002
Vehicle.Speed=49.029
```

Nói:

```text
HMI Bridge nhận Vehicle.Speed từ Signal Broker và forward sang VHAL PERF_VEHICLE_SPEED.
```

---

## Bước 10 - Quay Android HMI / Logcat

Nếu quay Android HMI UI:

1. Mở Android HMI screen.
2. Quay state đổi sang warning/critical hoặc hiển thị DMS values.

Nói:

```text
Android HMI nhận dữ liệu qua CarProperty/VHAL và render state cho tài xế.
```

Nếu quay logcat trong Android shell:

```bash
logcat -d -s DMS_HMI:I AndroidRuntime:E CarPropertyManager:E | tail -160
```

Cần thấy:

```text
DMS_HMI
mux raw
mux speed
```

Sau khi quay xong Signal Watch / Bridge log / Android HMI, quay lại terminal và bấm `Enter`.

---

## Bước 11 - Show Saved Critical Publish Log

Script sẽ show:

```text
/tmp/carsky-critical.log
```

Bạn quay terminal và nói:

```text
Đây là log bắn critical signal. Kết quả ok=true, mode=vehicle-speed-mux, sent=14 chứng minh Backend đã gửi notification/signal thành công.
```

Sau đó bấm `Enter`.

---

## Bước 12 - Reset To Normal

Script sẽ in hướng dẫn CarSky UI và sau đó reset về normal.

Khi tới bước reset, quay terminal và nói:

```text
Sau khi test critical, hệ thống reset signal về normal.
```

Script sẽ chạy:

```bash
.venv/bin/python scripts/carsky_phase05.py scenario normal
```

Nếu muốn show rõ, quay lại Signal Watch để thấy `Vehicle.Speed` đổi về normal mux.

---

# 3. Timestamp Gợi Ý Dán Vào Report

```text
00:00 - 00:30 Backend mapper / Vehicle.Speed source evidence
00:30 - 01:00 HMI Bridge / VHAL source evidence
01:00 - 01:30 Android APK artifact/hash evidence
01:30 - 02:00 APK runtime strings evidence
02:00 - 02:30 CarSky status/nodes + 3 node Running
02:30 - 03:00 Critical speed-mux publish result
03:00 - 03:25 Signal Watch Vehicle.Speed
03:25 - 03:50 HMI Bridge log
03:50 - 04:15 Android logcat / APK UI
04:15 - 04:30 Reset normal
```

---

# 4. Caveat Dán Vào Report

```text
Custom VSS paths are not available in the current CarSky deployment, so runtime correctly falls back to Vehicle.Speed speed-mux. Same-event Android UI proof should include Signal Watch, bridge log, Android logcat and APK UI in the same recording.
```

