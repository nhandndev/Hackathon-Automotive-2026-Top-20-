# 6. Platform Utilization / Ecosystem Alignment

## Nội dung đề xuất đưa vào báo cáo

FPTU DMS Vision không chỉ dùng CarSky như một nơi “host UI”, mà dùng CarSky làm connected-car runtime để chứng minh luồng cảnh báo từ AI/Backend đi vào vehicle signal ecosystem và tới Driver HMI. Core alignment của nhóm là tái sử dụng `KUKSA Signal Broker`, `Signal Watch`, `Script Node`, `VHAL/CarProperty path` và `Skycraft Android HMI node` thay vì tự dựng một dashboard ngoài xe rồi gọi đó là connected-car.

Trong demo hiện tại, AI/Backend publish DMS state vào CarSky qua `Vehicle.Speed` speed-mux. `DMS Signal Broker` giữ signal state, `DMS HMI Bridge` subscribe `Vehicle.Speed` và forward sang VHAL `PERF_VEHICLE_SPEED`, Android HMI APK đọc qua `CarPropertyManager` và render trạng thái cho tài xế. Đây là workaround có chủ đích vì runtime CarSky hiện expose property chuẩn `PERF_VEHICLE_SPEED` ổn định hơn custom DMS CarProperty. Custom VSS paths được xem là explored path, không claim production-ready trong bản demo này.

## Boundary / Component Ownership

| Boundary | Component / workload | Cơ chế giao tiếp | Trạng thái |
|---|---|---|---|
| AI / Decision Engine -> Backend | Backend nhận event/risk state từ AI pipeline | HTTP/API nội bộ + event payload | Implemented |
| Backend -> CarSky | `SE/BE/app/integrations/carsky/*` publish DMS signal | CarSky REST Signal API | Implemented |
| CarSky Signal Runtime | `DMS Signal Broker` / KUKSA node | `Vehicle.Speed` signal state | Verified in deployment |
| Signal Broker -> Bridge | `DMS HMI Bridge` Script Node | Subscribe `Vehicle.Speed` | Verified by bridge script/log |
| Bridge -> Android VHAL | Bridge forward sang `PERF_VEHICLE_SPEED` | VHAL / CarProperty-compatible signal | Implemented for demo |
| Android VHAL -> Driver HMI | `DMS Android HMI` APK | Android `CarPropertyManager` | APK artifact verified; runtime capture required |

## CarSky Capabilities Reused

| CarSky capability | Cách đội sử dụng |
|---|---|
| Blueprint / node orchestration | Tổ chức 3 node: `DMS Signal Broker`, `DMS HMI Bridge`, `DMS Android HMI` |
| KUKSA / Signal Broker | Lưu và expose `Vehicle.Speed` speed-mux state |
| Signal Watch | Evidence để quan sát signal thay đổi trong runtime |
| Script Node | Bridge signal từ KUKSA sang VHAL property |
| Skycraft Android node | Chạy Driver HMI APK trong connected-car environment |
| VHAL / CarProperty route | Android HMI đọc dữ liệu qua `PERF_VEHICLE_SPEED` |

## End-To-End Evidence

Evidence hiện có cho platform utilization:

1. Backend source có mapper/publisher CarSky:
   - `SE/BE/app/integrations/carsky/mapper.py`
   - `SE/BE/app/integrations/carsky/client.py`
   - `SE/BE/app/integrations/carsky/service.py`

2. Bridge source có mapping `Vehicle.Speed -> PERF_VEHICLE_SPEED`:
   - `SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua`
   - `SE/BE/carsky/dms_hmi_bridge.lua`
   - `SE/BE/carsky/dms_hmi_bridge_dual_push.lua`

3. Android HMI artifact tồn tại và có runtime strings:
   - `SE/HMI/release/dms-hmi-realtime-vhal.apk`
   - `classes.dex` chứa `DMS_HMI`, `PERF_VEHICLE_SPEED`, `CarPropertyManager`, `SAFE`, `CRITICAL`, `TTC`, `km/h`

4. Runtime script bắn critical signal:
   - `SE/BE/scripts/carsky_phase05.py scenario critical`
   - Expected result: `ok=true`, `mode=vehicle-speed-mux`, `sent=14`

5. Runtime video cần thể hiện:
   - CarSky deployment có 3 node running
   - Signal Watch thấy `Vehicle.Speed`
   - Bridge log có `DMS_HMI_SPEED_MUX`
   - Android HMI/logcat nhận `DMS_HMI` mux

## What Is Real vs Limited

| Phần | Claim đúng |
|---|---|
| Backend -> CarSky REST Signal API | Real, implemented |
| CarSky Signal Broker / KUKSA state | Real, verified by status/nodes + Signal Watch |
| HMI Bridge | Real, implemented by Script Node source and runtime log |
| Android HMI APK artifact | Real artifact, hash/DEX/signing evidence available |
| Android HMI same-event runtime | Needs final same-event video evidence |
| Custom DMS CarProperty IDs | Explored path, not final demo transport |
| `Vehicle.Speed` speed-mux | Final demo workaround transport |
| PDF export / unrelated dashboard hosting | Not part of CarSky platform utilization claim |

## Evidence Timestamp Dán Vào Report

```text
00:00 - 01:00 Backend + HMI Bridge source evidence
01:00 - 02:00 Android APK artifact + runtime strings
02:00 - 02:30 CarSky 3 nodes Running
02:30 - 03:00 Send critical Vehicle.Speed speed-mux
03:00 - 04:15 Signal Watch + Bridge log + Android HMI/logcat
04:15 - 04:30 Reset normal
```

## Caveat / Giới Hạn

Custom VSS paths are not available in the current CarSky deployment, so runtime correctly falls back to `Vehicle.Speed` speed-mux. This is an intentional demo transport aligned with the current CarSky AAOS/VHAL capability. Same-event Android UI proof should include Signal Watch, bridge log, Android logcat and APK UI in the same recording.

