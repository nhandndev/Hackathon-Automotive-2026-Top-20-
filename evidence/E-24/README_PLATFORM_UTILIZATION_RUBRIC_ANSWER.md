# 6. Platform Utilization / Ecosystem Alignment

## Nội dung đội điền

Dự án sử dụng CarSky như một phần của connected-car runtime, không chỉ dùng làm nơi host UI. Core demo flow hiện tại là:

```text
Backend
  -> CarSky Signal API / KUKSA
  -> Vehicle.Speed speed-mux
  -> DMS HMI Bridge Script Node
  -> VHAL PERF_VEHICLE_SPEED
  -> Android Automotive HMI qua CarPropertyManager
```

Backend không gọi trực tiếp Android APK. Thay vào đó, DMS safety state được publish vào signal layer của CarSky, bridge qua VHAL, rồi Android HMI consume bằng Android Automotive property API. Đây là ecosystem alignment thật vì team tái sử dụng blueprint/node orchestration, KUKSA signal layer, Script Node, VHAL path và Skycraft/AAOS HMI node của CarSky.

## CarSky mapping

| Boundary / component | Chạy ở đâu | Giao tiếp qua cơ chế nào | Evidence |
|---|---|---|---|
| Backend -> CarSky | Backend local/demo runtime -> CarSky deployment | CarSky Signal API, final demo path là `Vehicle.Speed` speed-mux | `evidence/E-24/raw/carsky_scenario_critical_command.json` |
| CarSky/KUKSA signal layer | DMS Signal Broker / KUKSA side | Signal state `Vehicle.Speed` | `evidence/E-24/raw/carsky_scenario_critical_parsed.json` |
| KUKSA -> HMI Bridge | DMS HMI Bridge Script Node | Lua subscribe `Vehicle.Speed` | `evidence/E-24/reports/mapping.md` |
| HMI Bridge -> VHAL | Script Node -> VHAL pin | Push `PERF_VEHICLE_SPEED` / `0x11600207` | `evidence/E-24/raw/source_locators.log` |
| VHAL -> Android HMI | Skycraft/AAOS Android node | Android `CarPropertyManager` reads `PERF_VEHICLE_SPEED` | `evidence/E-24/raw/hmi_apk_static_scan.log` |

## CarSky capabilities reused

| CarSky capability | Nhóm dùng như thế nào | Vì sao không phải wrapper/mock |
|---|---|---|
| Blueprint / node orchestration | Tổ chức runtime thành DMS Signal Broker, DMS HMI Bridge, DMS Android HMI | Flow đi qua node topology thật thay vì chạy một app độc lập ngoài CarSky |
| KUKSA Broker / Signal API | Backend publish DMS state vào `Vehicle.Speed` | Dùng vehicle signal layer của platform thay vì tự dựng message bus riêng |
| Signal Watch | Quan sát `Vehicle.Speed` đổi khi Backend publish | Dùng observability/debug tool của CarSky để kiểm tra runtime signal |
| Script Node | Chạy Lua bridge từ KUKSA sang VHAL | Bridge logic nằm trong CarSky Script Node, không hardcode đường vòng vào APK |
| Skycraft / AAOS node | Chạy Android Driver HMI | Driver-facing UI chạy trên Android Automotive environment |
| VHAL / CarProperty path | APK đọc `PERF_VEHICLE_SPEED` bằng `CarPropertyManager` | Bám vào Android Automotive vehicle property mechanism |

## Evidence chứng minh core flow end-to-end trên blueprint

Evidence hiện có trong E-24:

| Evidence | Kết quả |
|---|---|
| Runtime command | `ok=true`, `mode=vehicle-speed-mux`, `sent=14` |
| Runtime fallback reason | Custom path `Vehicle.Driver.State` bị CarSky deployment reject, nên demo dùng `Vehicle.Speed` speed-mux |
| Mapping report | Mô tả chain Backend -> CarSky/KUKSA -> Lua Bridge -> VHAL -> Android HMI |
| APK static scan | APK có runtime string `PERF_VEHICLE_SPEED`, `CarPropertyManager`, `DMS_HMI`, `SAFE`, `CRITICAL`, `TTC`, `km/h` |
| Manifest | Ghi rõ claim và not-claimed boundary để tránh overclaim |

File evidence chính:

- `evidence/E-24/raw/carsky_scenario_critical_command.json`
- `evidence/E-24/raw/carsky_scenario_critical_parsed.json`
- `evidence/E-24/reports/mapping.md`
- `evidence/E-24/reports/source_report.md`
- `evidence/E-24/derived/manifest.json`
- `evidence/E-24/raw/hmi_apk_static_scan.log`

Nếu có video Drive, thêm vào câu này:

```text
Runtime media evidence: [Drive Video - Signal Watch + Bridge Log + Android HMI same event](PASTE_DRIVE_LINK_HERE)
```

## Phần nào là thật, phần nào chưa claim

| Nội dung | Trạng thái trung thực |
|---|---|
| Backend publish signal sang CarSky | Verified bằng command log: `ok=true`, `sent=14` |
| CarSky/KUKSA demo path | Verified ở mức `Vehicle.Speed` speed-mux |
| HMI Bridge mapping | Verified bằng source/report evidence |
| Android HMI APK artifact | Verified bằng APK hash/static scan |
| Same-event screenshot/video trong E-24 | Pending nếu chưa attach media vào `screenshots/` hoặc `video/` |
| Custom DMS VSS properties | Không claim production-ready |
| Physical vehicle actuation | Không claim |
| Production reliability / long-run | Không claim từ E-24 |

## AI Engineering alignment

Phần AI Engineering của dự án không bắt external consumer dùng raw model output trực tiếp. AI/local telemetry được đóng gói thành contract, API, report và artifact để các consumer khác dùng được:

| External consumer | Capability họ dùng | Interface / artifact | Evidence locator |
|---|---|---|---|
| SE Backend engineer | Nhận AI safety event theo contract | `DecisionEvent`, `/api/v1/alerts`, `/api/v1/alerts/snapshot` | `evidence/E-03/`, `SE/BE/tests/test_ai_alerts.py` |
| CarSky integration engineer | Publish AI/DMS safety state sang CarSky | `carsky_phase05.py`, CarSky mapper/client/service | `evidence/E-24/`, `SE/BE/app/integrations/carsky/` |
| Fleet Manager / reviewer | Xem trip, ranking, insights, reports | Fleet Dashboard + Copilot Report + DOC export | `evidence/E-15/`, `evidence/E-19/`, `evidence/E-20/` |
| AI/SE maintainer | Kiểm tra compatibility khi AI output đổi | Contract tests + golden payloads | `evidence/E-03/`, `evidence/E-15/` |
| Demo operator / judge | Reproduce demo/evidence flow | Evidence README + scripts + runtime logs | `evidence/E-24/`, `README_RUN_OUTPUT_007_CARSKY_HMI_EVIDENCE.md` nếu có trong repo |

Điểm cần nhấn mạnh khi trình bày: external consumer không consume model raw. Họ consume AI capability qua boundary đã định nghĩa: API, contract, CarSky signal path, report artifact và evidence scripts. Vì vậy capability có thể tích hợp, kiểm thử và audit được.

## Đoạn copy ngắn vào báo cáo

```text
FPTU DMS Vision có CarSky ecosystem alignment ở mức demo-runtime verified. Backend publish DMS safety state qua CarSky Signal API/KUKSA bằng Vehicle.Speed speed-mux; DMS HMI Bridge chạy trong CarSky Script Node forward signal sang VHAL PERF_VEHICLE_SPEED; Android HMI chạy trên Skycraft/AAOS node và đọc dữ liệu qua CarPropertyManager. Evidence gồm command log ok=true/mode=vehicle-speed-mux/sent=14, mapping report, APK artifact/static scan và runtime media evidence nếu attach link Drive.

AI Engineering capability cũng được expose qua interface/artifact thay vì raw model output: DecisionEvent/API cho Backend, CarSky mapper/script cho integration engineer, Fleet Dashboard/Copilot Report/DOC export cho Fleet Manager và reviewer, golden payload/tests cho AI/SE maintainer. Điều này chứng minh capability được external consumer sử dụng thực tế qua API, contract, signal path và artifact.

Giới hạn: custom DMS VSS properties chưa production-ready; demo path hiện dùng Vehicle.Speed speed-mux fallback. Hệ thống không claim physical vehicle actuation hoặc production long-run reliability từ evidence này.
```

