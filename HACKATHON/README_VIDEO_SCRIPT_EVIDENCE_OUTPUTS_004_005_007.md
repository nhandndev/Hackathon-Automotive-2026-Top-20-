# Video Script - Evidence Outputs #004 #005 #007

Mục tiêu: quay evidence cho 3 output bằng UI/source/artifact hiện có. Không deploy lại, không build lại APK, không thay đổi code.

---

# Chuẩn bị

Mở sẵn 3 tab:

```text
Tab 1 - FleetDashboard:
http://127.0.0.1:3000/?view=MAP

Tab 2 - AI Copilot Report:
http://127.0.0.1:3000/?view=copilot-report&type=safety&trip_ids=T02-Sample

Tab 3 - Terminal hoặc VS Code tại project root:
/Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
```

Các lệnh terminal dùng để show evidence, chỉ đọc file:

```bash
pwd
find SE/FE/src/data/saved_trips -maxdepth 1 -name '*.json' | sort
rg -n "saved_trips|runtime_status|Infinity|completed" SE/FE/src/data/btcTripData.ts SE/FE/src/App.tsx SE/FE/server.ts
rg -n "BEDROCK|validated|pending|unavailable|handleExportWord|application/msword|\\.doc" SE/FE/server.ts SE/FE/src/components/CopilotFleetReportPage.tsx
rg -n "vehicle-speed-mux|Vehicle.Speed|PERF_VEHICLE_SPEED|DMS_HMI|CarPropertyManager" SE/BE/app/integrations/carsky/mapper.py SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java
ls -lh SE/HMI/release/dms-hmi-realtime-vhal.apk
```

---

# 00:00 - 00:10 | Intro

Quay terminal hoặc dashboard.

Nói:

```text
Video này chứng minh FleetDashboard, AI Copilot fallback/export và Backend-to-CarSky-to-Android-HMI bằng UI và source/artifact hiện có. Không deploy lại và không build lại APK.
```

---

# 00:10 - 01:25 | Output #004 - FleetDashBoard & Saved Trips

## 00:10 - 00:35 | Saved Trips

Chạy:

```bash
find SE/FE/src/data/saved_trips -maxdepth 1 -name '*.json' | sort
```

Sau đó chuyển qua Dashboard tab.

Cần thấy:

```text
T01-Sample.json -> T06-Sample.json
Dashboard list/map có saved trips
```

Nói:

```text
Saved trips T01 đến T06 có sẵn trong project và được dùng làm demo/replay context.
```

## 00:35 - 01:05 | Dashboard Views

Trên UI:

1. Mở Fleet Map/List.
2. Click một trip.
3. Mở Trip Detail.
4. Chuyển Ranking.
5. Chuyển Insights.

Nói:

```text
FleetDashboard mở được các view chính gồm trip detail, ranking và insights. Các số liệu baseline lấy từ JSON/local AI.
```

## 01:05 - 01:25 | Source Evidence

Chạy:

```bash
rg -n "saved_trips|runtime_status|Infinity|completed" SE/FE/src/data/btcTripData.ts SE/FE/src/App.tsx SE/FE/server.ts
```

Nói:

```text
Source có parser/normalizer cho saved trips và legacy Infinity, giúp JSON không làm lỗi browser parse.
```

Timestamp dán vào report:

```text
00:10 - 00:35 Saved Trips
00:35 - 01:05 Dashboard views
01:05 - 01:25 Saved trip parser/normalizer source evidence
```

---

# 01:25 - 02:55 | Output #005 - AI Copilot Report + Bedrock Fallback + Export Report

## 01:25 - 01:55 | AI Copilot Report

Mở:

```text
http://127.0.0.1:3000/?view=copilot-report&type=safety&trip_ids=T02-Sample
```

Quay:

```text
report title
Ranking Score / KPI
report content
Bedrock status nếu có
```

Nói:

```text
AI Copilot Report render local baseline trước. Bedrock chỉ là explanation layer và không tạo canonical metrics.
```

## 01:55 - 02:15 | Fallback

Kéo tới phần Bedrock/fallback status.

Cần thấy một trong các trạng thái:

```text
Đang chờ Bedrock
Chờ Bedrock hợp lệ
validated
unavailable
pending
local report vẫn hiện
```

Nói:

```text
Khi Bedrock chưa có phản hồi hợp lệ, UI giữ local report và không hiển thị insight giả.
```

## 02:15 - 02:35 | Source Evidence

Chạy:

```bash
rg -n "BEDROCK|validated|pending|unavailable|handleExportWord|application/msword|\\.doc" SE/FE/server.ts SE/FE/src/components/CopilotFleetReportPage.tsx
```

Nói:

```text
Source có Bedrock server-side config, validation state và Word/DOC export.
```

## 02:35 - 02:55 | Export Report

Trên UI:

1. Click `Export Report`.
2. Cho thấy file `.doc` được tải hoặc mở file vừa tải nếu có.

Nói:

```text
Report hỗ trợ Word/DOC export. PDF không nằm trong final demo claim.
```

Timestamp dán vào report:

```text
01:25 - 01:55 AI Copilot Report
01:55 - 02:15 Bedrock fallback state
02:15 - 02:35 fallback/export source evidence
02:35 - 02:55 Export Report
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

## 03:20 - 03:40 | HMI Bridge

Chạy:

```bash
rg -n "PERF_VEHICLE_SPEED|Vehicle.Speed|DMS_HMI" SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua SE/BE/carsky/dms_hmi_bridge.lua SE/BE/carsky/dms_hmi_bridge_dual_push.lua
```

Nói:

```text
Bridge path forward Vehicle.Speed sang VHAL PERF_VEHICLE_SPEED cho Android HMI.
```

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

## 04:10 - 04:35 | Android HMI Runtime Strings

Chạy:

```bash
unzip -p SE/HMI/release/dms-hmi-realtime-vhal.apk classes.dex | strings | rg "DMS_HMI|PERF_VEHICLE_SPEED|CarPropertyManager|SAFE|CRITICAL|TTC|km/h"
```

Nói:

```text
APK chứa runtime strings cho DMS_HMI, PERF_VEHICLE_SPEED, CarPropertyManager và các state hiển thị trên HMI.
```

Timestamp dán vào report:

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

