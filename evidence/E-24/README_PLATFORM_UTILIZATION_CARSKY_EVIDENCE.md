# E-24 - Platform Utilization / CarSky Ecosystem Evidence

## Mục tiêu evidence

Chứng minh dự án không chỉ chạy UI riêng lẻ, mà có tích hợp thật với CarSky ecosystem ở mức demo-runtime:

- Backend gửi DMS safety state qua CarSky Signal API/KUKSA.
- CarSky Signal Watch quan sát được signal `Vehicle.Speed` thay đổi.
- DMS HMI Bridge chạy trong CarSky Script Node, forward `Vehicle.Speed` sang VHAL `PERF_VEHICLE_SPEED`.
- Android HMI chạy trên Skycraft/AAOS node và đọc property bằng Android `CarPropertyManager`.

Evidence này dùng dữ liệu thật đã capture từ repo/evidence trước đó. Không dùng mock, không tự bịa trạng thái production.

## Trạng thái

**PARTIAL / RUNTIME COMMAND AND SOURCE-APK PATH VERIFIED; SAME-EVENT MEDIA CAPTURE PENDING**

Nói ngắn gọn: đủ để trình bày rằng CarSky integration đã chạy được ở demo path, nhưng chưa nên claim production-ready hoặc full custom VSS.

## Claim / outcome

Backend đã publish được critical DMS scenario vào CarSky bằng `Vehicle.Speed` speed-mux. Flow hiện tại đi qua CarSky/KUKSA, DMS HMI Bridge, VHAL và Android HMI thay vì gọi trực tiếp APK.

## Điều kiện xác định đạt

- Có command log thật cho `carsky_phase05.py scenario critical`.
- Command trả `ok=true`, `mode=vehicle-speed-mux`, `sent=14`.
- Có source mapping chứng minh `Vehicle.Speed` được bridge sang `PERF_VEHICLE_SPEED`.
- APK artifact có runtime string liên quan tới `PERF_VEHICLE_SPEED`, `CarPropertyManager`, `DMS_HMI`, `SAFE`, `CRITICAL`, `TTC`, `km/h`.
- Có caveat rõ rằng custom DMS VSS path chưa production-ready.

## Kết quả quan sát

- Runtime command trong `raw/carsky_scenario_critical_command.json` trả `returncode=0`.
- Parsed output trong `raw/carsky_scenario_critical_parsed.json` ghi nhận:
  - `ok=true`
  - `mode=vehicle-speed-mux`
  - `sent=14`
- Backend fallback reason ghi rõ custom path `Vehicle.Driver.State` chưa được CarSky deployment nhận, nên demo path dùng `Vehicle.Speed` speed-mux.
- `mapping.md` mô tả chain:
  - Backend scenario script
  - CarSky Signal API/KUKSA
  - `Vehicle.Speed`
  - Lua HMI Bridge
  - `PERF_VEHICLE_SPEED`
  - Android `CarPropertyManager`
- APK artifact evidence được copy từ E-15 và có hash/static scan.

## Evidence locator

| Evidence | File |
|---|---|
| Runtime CarSky command | `evidence/E-24/raw/carsky_scenario_critical_command.json` |
| Parsed runtime result | `evidence/E-24/raw/carsky_scenario_critical_parsed.json` |
| Source/API/APK locator grep | `evidence/E-24/raw/source_locators.log` |
| APK static scan | `evidence/E-24/raw/hmi_apk_static_scan.log` |
| Boundary mapping | `evidence/E-24/reports/mapping.md` |
| Source report | `evidence/E-24/reports/source_report.md` |
| Mapping CSV | `evidence/E-24/derived/mapping.csv` |
| Speed-mux values | `evidence/E-24/derived/speed_mux_values.csv` |
| Evidence manifest | `evidence/E-24/derived/manifest.json` |
| Evidence bundle | `evidence/E-24/derived/carsky_trace_bundle.zip` |

## CarSky capability alignment

| CarSky capability | Nhóm dùng như thế nào | Vì sao là ecosystem alignment | Evidence |
|---|---|---|---|
| Blueprint / node orchestration | Tổ chức runtime thành DMS Signal Broker, DMS HMI Bridge, DMS Android HMI | Không tự dựng runtime ngoài; dùng topology của CarSky để chứng minh flow | `mapping.md`, video/Drive nếu attach |
| KUKSA Broker / Signal API | Backend publish DMS state vào `Vehicle.Speed` | Tái sử dụng signal state layer thay vì tự dựng message bus riêng | `carsky_scenario_critical_command.json`, `carsky_scenario_critical_parsed.json` |
| Signal Watch | Quan sát `Vehicle.Speed` đổi khi Backend publish | Dùng observability/debug tool của CarSky để chứng minh runtime signal | Cần attach screenshot/video Drive |
| Script Node | Lua bridge subscribe `Vehicle.Speed`, push VHAL property | Tái sử dụng compute node trong blueprint thay vì hardcode bridge trong APK | `source_locators.log`, `mapping.md` |
| Skycraft / AAOS node | Chạy Driver HMI APK | Dùng Android Automotive node để thể hiện driver-facing HMI | APK artifact/static scan, video/Drive nếu attach |
| VHAL / CarProperty path | APK đọc `PERF_VEHICLE_SPEED` qua `CarPropertyManager` | Bám vào Android Automotive vehicle property mechanism | `hmi_apk_static_scan.log`, `hmi_apk_artifact_from_E15.json` |

## Đoạn copy vào mục 6 - Platform utilization / ecosystem alignment

```text
Dự án có evidence cho CarSky ecosystem alignment ở mức demo-runtime verified. Backend publish DMS safety state qua CarSky Signal API/KUKSA bằng Vehicle.Speed speed-mux; DMS HMI Bridge chạy trong CarSky Script Node forward Vehicle.Speed sang VHAL PERF_VEHICLE_SPEED; Android HMI chạy trên Skycraft/AAOS node và đọc dữ liệu qua CarPropertyManager.

Evidence hiện có gồm runtime command log trả ok=true, mode=vehicle-speed-mux, sent=14; source mapping Vehicle.Speed -> Lua Bridge -> PERF_VEHICLE_SPEED -> Android CarPropertyManager; APK artifact/hash/static scan; và media evidence runtime nếu attach link Drive. Điều này chứng minh team tái sử dụng CarSky blueprint/node orchestration, KUKSA signal layer, Script Node, VHAL và Android Automotive HMI path thay vì dựng một channel riêng gọi trực tiếp APK.

Giới hạn: custom DMS VSS properties chưa claim production-ready. Demo path hiện dùng Vehicle.Speed speed-mux fallback vì deployment hiện tại chưa nhận custom path Vehicle.Driver.State. Hệ thống không claim physical vehicle actuation; intervention vẫn là human workflow.
```

## Dòng cần thêm nếu có video Drive

Thêm dòng này vào report hoặc `Task_Nhan.md` sau khi có link:

```text
Runtime media evidence: [Drive Video - Signal Watch + Bridge Log + Android HMI same event](PASTE_DRIVE_LINK_HERE)
```

## Caveat / giới hạn

- E-24 chưa đánh DONE nếu chưa attach video/screenshot/logcat same-event vào `evidence/E-24/screenshots/` hoặc `evidence/E-24/video/`.
- Không claim custom DMS VSS production-ready.
- Không claim physical vehicle actuation.
- Không claim production reliability hoặc long-run stability từ evidence này.

