# Video Script - Output #007 Backend To CarSky To Android HMI

Mục tiêu: quay evidence cho `Output #007 - Backend To CarSky To Android HMI` bằng source/artifact hiện có. Script này dùng để show feature path, không deploy lại, không build lại APK.

---

# Runtime Test - Bắn Noti / Signal Lên CarSky

Chạy các lệnh này từ project root hoặc `SE/BE`. Các lệnh này chỉ gửi signal test lên deployment hiện tại, không deploy lại, không cài lại APK.

## 1. Kiểm tra CarSky config và deployment

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

.venv/bin/python scripts/carsky_phase05.py status
.venv/bin/python scripts/carsky_phase05.py nodes
```

Kỳ vọng:

```text
status trả về deployment đang running
nodes có DMS Signal Broker / DMS HMI Bridge / Android HMI
```

## 2. Bắn critical notification / signal

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

.venv/bin/python scripts/carsky_phase05.py scenario critical
```

Kỳ vọng output:

```text
{
  "ok": true,
  "mode": "vehicle-speed-mux",
  "sent": ...
}
```

Giá trị mux critical sẽ đi qua `Vehicle.Speed`, ví dụ:

```text
41.088 = risk 88
42.002 = CRITICAL
43.004 = microsleep
44.015 = alertness 15%
45.012 = TTC 1.2s
46.001 = critical alert true
48.003 = BRAKE_SAFE
49.029 = real speed 29 km/h
```

## 3. Lưu log lúc bắn signal

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

.venv/bin/python scripts/carsky_phase05.py scenario critical 2>&1 | tee /tmp/carsky-critical.log
cat /tmp/carsky-critical.log
```

## 4. Xem HMI Bridge log trong CarSky

Trong CarSky UI, mở log của node:

```text
Logs: DMS HMI Bridge
```

Tìm các dòng kiểu:

```text
DMS_HMI_SPEED_MUX Vehicle.Speed=41.088 -> 0x11600207=41.088
DMS_HMI_SPEED_MUX Vehicle.Speed=42.002 -> 0x11600207=42.002
DMS_HMI_SPEED_MUX Vehicle.Speed=43.004 -> 0x11600207=43.004
DMS_HMI_SPEED_MUX Vehicle.Speed=48.003 -> 0x11600207=48.003
DMS_HMI_SPEED_MUX Vehicle.Speed=49.029 -> 0x11600207=49.029
```

## 5. Xem Android HMI logcat

Trong Android shell của CarSky, chạy:

```bash
logcat -c
```

Sau đó quay lại terminal BE và bắn lại critical:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python scripts/carsky_phase05.py scenario critical
```

Quay lại Android shell, chạy:

```bash
logcat -d -s DMS_HMI:I AndroidRuntime:E CarPropertyManager:E | tail -160
```

Kỳ vọng thấy log kiểu:

```text
DMS_HMI ... mux raw=41.088
DMS_HMI ... mux raw=42.002
DMS_HMI ... mux speed=49.029
```

## 6. Reset về normal

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

.venv/bin/python scripts/carsky_phase05.py scenario normal
```

## 7. Flow quay runtime evidence

```text
1. Mở Signal Watch và watch Vehicle.Speed.
2. Mở Logs: DMS HMI Bridge.
3. Mở Android HMI APK.
4. Chạy scenario critical từ SE/BE.
5. Quay Signal Watch đổi giá trị 41.xxx-49.xxx.
6. Quay bridge log có DMS_HMI_SPEED_MUX.
7. Quay Android logcat DMS_HMI.
8. Quay APK UI đổi sang warning/critical state.
9. Chạy scenario normal để reset.
```

Timestamp runtime gợi ý:

```text
00:00 - 00:10 status/nodes running
00:10 - 00:25 bắn scenario critical
00:25 - 00:45 Signal Watch thấy Vehicle.Speed mux
00:45 - 01:05 HMI Bridge log forward sang PERF_VEHICLE_SPEED
01:05 - 01:25 Android logcat DMS_HMI nhận mux
01:25 - 01:45 APK UI đổi critical state
01:45 - 02:00 reset scenario normal
```

---

# 02:55 - 04:35 | Output #007 - Backend To CarSky To Android HMI

## 02:55 - 03:20 | Backend Mapper / Vehicle.Speed

Chạy:

```bash
rg -n "vehicle-speed-mux|Vehicle.Speed" SE/BE/app/integrations/carsky/mapper.py SE/BE/app/integrations/carsky/client.py SE/BE/app/integrations/carsky/service.py
```

Nói:

```text
Backend mapper publish DMS event bằng Vehicle.Speed speed-mux để CarSky/KUKSA nhận signal.
```

---

## 03:20 - 03:40 | HMI Bridge

Chạy:

```bash
rg -n "PERF_VEHICLE_SPEED|Vehicle.Speed|DMS_HMI" SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua SE/BE/carsky/dms_hmi_bridge.lua SE/BE/carsky/dms_hmi_bridge_dual_push.lua
```

Nói:

```text
Bridge path forward Vehicle.Speed sang VHAL PERF_VEHICLE_SPEED cho Android HMI.
```

---

## 03:40 - 04:10 | Android APK Artifact

Chạy:

```bash
ls -lh SE/HMI/release/dms-hmi-realtime-vhal.apk
shasum -a 256 SE/HMI/release/dms-hmi-realtime-vhal.apk
unzip -l SE/HMI/release/dms-hmi-realtime-vhal.apk | head -20
```

Nói:

```text
Android HMI APK artifact tồn tại trong project, có hash và có classes.dex/manifest/signing metadata.
```

---

## 04:10 - 04:35 | Android HMI Runtime Strings

Chạy:

```bash
unzip -p SE/HMI/release/dms-hmi-realtime-vhal.apk classes.dex | strings | rg "DMS_HMI|PERF_VEHICLE_SPEED|CarPropertyManager|SAFE|CRITICAL|TTC|km/h"
```

Nói:

```text
APK chứa runtime strings cho DMS_HMI, PERF_VEHICLE_SPEED, CarPropertyManager và các state hiển thị trên HMI.
```

---

# Timestamp dán vào report

```text
02:55 - 03:20 Backend mapper Vehicle.Speed evidence
03:20 - 03:40 HMI bridge VHAL evidence
03:40 - 04:10 APK artifact/hash evidence
04:10 - 04:35 APK runtime strings evidence
```

---

# Caveat cho Output #007

Dùng câu này nếu video chỉ quay source/artifact, chưa quay runtime CarSky:

```text
Video hiện chứng minh source/artifact path. Same-event runtime chain từ Signal Watch -> bridge log -> Android logcat -> APK UI cần được quay riêng khi CarSky runtime sẵn sàng.
```
