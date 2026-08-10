# 6. Platform Utilization / Ecosystem Alignment - Answer Pack

File này dùng để trả lời mục **6. Platform utilization / ecosystem alignment**. Nội dung được viết theo hướng có thể copy vào báo cáo, nhưng vẫn giữ đúng trạng thái evidence hiện có: có CarSky runtime evidence, có source/test/artifact evidence, và có một số phần cần bổ sung video/link Drive nếu muốn chốt hoàn toàn.

---

## 6.1. Tóm Tắt Trả Lời Ngắn Gọn

FPTU DMS Vision sử dụng CarSky như một **connected-car runtime** thật, không chỉ dùng để host UI. Backend publish trạng thái an toàn DMS vào CarSky qua **Signal API/KUKSA** bằng cơ chế `Vehicle.Speed speed-mux`. Trên blueprint, **DMS Signal Broker** giữ signal state, **DMS HMI Bridge** chạy bằng Script Node để subscribe `Vehicle.Speed` và forward sang **VHAL `PERF_VEHICLE_SPEED`**, còn **DMS Android HMI** chạy trên Skycraft/AAOS node và đọc data qua Android **CarPropertyManager**.

Luồng đã có evidence thật: command CarSky trả `ok=true`, `mode=vehicle-speed-mux`, `sent=14`; mapping report mô tả Backend -> KUKSA -> Bridge -> VHAL -> Android HMI; APK artifact có SHA256 và static scan cho thấy APK dùng `DMS_HMI`, `PERF_VEHICLE_SPEED`, `CarPropertyManager`, `TTC`, `km/h`, `SAFE`, `CRITICAL`. Fleet Dashboard và AI Copilot Report là consumer phía vận hành: dùng JSON/local AI làm canonical baseline, Bedrock chỉ là explanation layer có fallback.

Điểm cần nói thẳng: bản demo hiện dùng `Vehicle.Speed speed-mux` như fallback vì custom VSS properties chưa phải production path. Đây là demo alignment hợp lệ với CarSky Signal/KUKSA/VHAL, nhưng chưa claim production-grade custom VSS, long-run reliability hay physical actuator control.

---

## 6.2. CarSky Mapping: Component Nào Chạy Ở Đâu?

| Component / workload | Chạy ở đâu | Giao tiếp qua cơ chế nào | Vai trò trong flow | Evidence |
|---|---|---|---|---|
| Backend CarSky publisher | Backend service / demo runner | CarSky REST Signal API | Publish DMS safety state thành `Vehicle.Speed speed-mux` | `evidence/E-24/raw/carsky_scenario_critical_command.json`, `evidence/E-24/raw/carsky_scenario_critical_parsed.json` |
| DMS Signal Broker / KUKSA | CarSky blueprint node | KUKSA signal state, `Vehicle.Speed` | Lưu và phát signal state cho blueprint | `evidence/E-24/reports/mapping.md` |
| DMS HMI Bridge | CarSky Script Node | Lua `pins.kuksa:on_change`, `pins.vhal:push(...)` | Forward `Vehicle.Speed` sang VHAL property | `evidence/E-24/reports/mapping.md`, `SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua` |
| Android VHAL path | Skycraft/AAOS runtime | VHAL `PERF_VEHICLE_SPEED` | Đưa signal vào Android Automotive property layer | `evidence/E-24/reports/mapping.md`, `evidence/E-24/raw/hmi_apk_static_scan.log` |
| DMS Android HMI | Skycraft / AAOS node | Android `CarPropertyManager` | Driver-facing HMI hiển thị risk, safe score, TTC, speed, driver state | `evidence/E-24/derived/hmi_apk_artifact_from_E15.json`, `SE/HMI/release/dms-hmi-realtime-vhal.apk` |
| Fleet Dashboard | Web dashboard ngoài CarSky runtime | Backend API, saved/live trip JSON, report API | Fleet manager view: saved trips, ranking, insights, reports, export | `evidence/E-21/`, `evidence/E-22/`, `evidence/E-23/` |

**Cách nói khi demo:**  
CarSky được dùng ở đoạn runtime connected-car: Signal API/KUKSA nhận signal, Script Node bridge sang VHAL, Skycraft/AAOS chạy APK HMI. Fleet Dashboard là operational consumer bổ sung, không phải node trong CarSky blueprint.

---

## 6.3. CarSky Capability Nào Được Tái Sử Dụng?

| CarSky capability | Nhóm dùng như thế nào | Vì sao là ecosystem alignment | Evidence |
|---|---|---|---|
| Blueprint / node orchestration | Tổ chức 3 node: DMS Signal Broker, DMS HMI Bridge, DMS Android HMI | Không dựng runtime ngoài; flow nằm trên topology của CarSky | `evidence/E-24/reports/mapping.md`, screenshot/video blueprint nếu attach thêm |
| KUKSA Broker / Signal API | Backend publish `Vehicle.Speed` vào signal state | Tái sử dụng vehicle signal layer thay vì tự dựng message bus riêng | `evidence/E-24/raw/carsky_scenario_critical_command.json` |
| Signal Watch | Quan sát `Vehicle.Speed` đổi khi Backend publish | Dùng observability/debug tool của CarSky để chứng minh runtime signal | Link Drive/screenshot cần gắn thêm nếu có |
| Script Node | Lua bridge subscribe KUKSA và push VHAL | Dùng compute node của blueprint thay vì hardcode toàn bộ vào APK | `SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua` |
| Skycraft / AAOS node | Chạy Driver HMI APK trong Android Automotive runtime | Thể hiện connected-car driver-facing HMI trên AAOS | APK artifact + screenshot/video runtime |
| VHAL / CarProperty path | APK đọc `PERF_VEHICLE_SPEED` bằng `CarPropertyManager` | Bám vào Android Automotive vehicle property mechanism | `evidence/E-24/raw/hmi_apk_static_scan.log` |

---

## 6.4. Evidence Chứng Minh Core Flow End-To-End Trên Blueprint

### Core Flow Thực Tế

```text
Backend / AI safety event
  -> CarSky REST Signal API
  -> KUKSA Signal: Vehicle.Speed speed-mux
  -> DMS HMI Bridge Script Node
  -> VHAL PERF_VEHICLE_SPEED
  -> Android CarPropertyManager
  -> DMS Android HMI UI
```

### Evidence Hiện Có

| Evidence | Chứng minh điều gì | Trạng thái |
|---|---|---|
| `evidence/E-24/raw/carsky_scenario_critical_command.json` | Backend command gửi scenario critical lên CarSky thành công | Verified command output |
| `evidence/E-24/raw/carsky_scenario_critical_parsed.json` | Runtime trả `ok=true`, `mode=vehicle-speed-mux`, `sent=14` | Verified command output |
| `evidence/E-24/reports/mapping.md` | Mapping từ Backend -> CarSky/KUKSA -> Bridge -> VHAL -> HMI | Source/runtime mapping verified |
| `evidence/E-24/raw/hmi_apk_static_scan.log` | APK có runtime strings cho `DMS_HMI`, `PERF_VEHICLE_SPEED`, `CarPropertyManager`, `TTC`, `km/h`, `SAFE`, `CRITICAL` | APK artifact verified |
| `evidence/E-24/derived/hmi_apk_artifact_from_E15.json` | APK SHA256 và artifact metadata | Artifact verified |
| `evidence/E-21/` | Copilot Report/export evidence | Source + UI sample evidence |
| `evidence/E-22/` | Fleet Dashboard saved trips/ranking/insights UI evidence | Source + temporary UI screenshot evidence |
| `evidence/E-23/` | Failure/fallback UI evidence | Source + empty/fallback screenshot evidence |
| `evidence/E-03/` | DecisionEvent schema/API boundary | Schema/test evidence |
| `evidence/E-15/` | BE pytest, FE lint/build, APK static artifact checks | Automated test/build evidence |

### Evidence Nên Gắn Thêm Để Chốt Gần Full Điểm

```md
[ADD DRIVE LINK] Same-event CarSky runtime video:
- Backend command chạy `carsky_phase05.py scenario critical`
- Signal Watch thấy `Vehicle.Speed` đổi
- DMS HMI Bridge log forward `DMS_HMI_SPEED_MUX`
- Android HMI UI đổi sang CRITICAL / SAFE / TTC / km/h tương ứng
```

Nếu có video/screenshot này thì phần CarSky end-to-end sẽ mạnh hơn source-only evidence rất nhiều.

---

## 6.5. Phần Nào Là Generic, Wrapper, Mock Hoặc Planned?

| Phần | Trạng thái thật | Cách nói đúng |
|---|---|---|
| `Vehicle.Speed speed-mux` | Demo fallback đang dùng thật | Đây là pragmatic integration fallback để truyền nhiều DMS values qua một VSS property có sẵn |
| Custom DMS VSS properties | Chưa phải production-ready path | Không claim đã hoàn tất custom VSS production mapping |
| Android HMI APK | Artifact thật, đã có static scan và runtime screenshot/video ngoài nếu gắn | Claim APK/HMI demo runtime, không claim production-certified HMI |
| Physical vehicle actuation | Không có actuator path thật | Intervention là human workflow/safety review, không tự động phanh hoặc can thiệp xe |
| Fleet Dashboard saved trips | Demo/replay context thật trong project | Saved trips không thay thế live field pilot data |
| Bedrock Copilot | Explanation layer có fallback | Không dùng Bedrock làm nguồn canonical metrics; không hiển thị insight giả khi provider lỗi |
| Human factors improvement | Chưa có user study | Không claim giảm alert fatigue/reaction time nếu chưa có study |
| Long-run/multi-instance readiness | Chưa chốt production evidence | Để caveat/roadmap, không claim full production reliability |

### 6.5.1. Evidence Cho Từng Caveat / Boundary Claim

| Phần | Evidence locator | Evidence chứng minh gì? | Kết luận nên ghi |
|---|---|---|---|
| `Vehicle.Speed speed-mux` | `evidence/E-24/raw/carsky_scenario_critical_command.json`, `evidence/E-24/raw/carsky_scenario_critical_parsed.json`, `evidence/E-24/derived/speed_mux_values.csv`, `evidence/E-24/reports/mapping.md` | CarSky command chạy thật với `mode=vehicle-speed-mux`, `sent=14`; mapping mô tả các mux values đi qua `Vehicle.Speed` | Đây là fallback integration path đang dùng thật trong demo |
| Custom DMS VSS properties | `evidence/E-24/reports/mapping.md`, `evidence/E-24/raw/carsky_scenario_critical_parsed.json` | Parsed command có fallback reason cho custom path bị CarSky reject, ví dụ `Unknown signal path: Vehicle.Driver.State` | Không claim custom DMS VSS production-ready |
| Android HMI APK | `SE/HMI/release/dms-hmi-realtime-vhal.apk`, `evidence/E-24/derived/hmi_apk_artifact_from_E15.json`, `evidence/E-24/raw/hmi_apk_static_scan.log`, `evidence/E-24/screenshots/` | APK artifact tồn tại, có SHA/static scan; strings có `DMS_HMI`, `PERF_VEHICLE_SPEED`, `CarPropertyManager`, `SAFE`, `CRITICAL`, `TTC`, `km/h`; screenshots có runtime UI | Claim APK/HMI demo runtime và artifact verified |
| Physical vehicle actuation | `evidence/E-17/`, `SE/BE/app/modules/ai_alerts/router.py`, `SE/FE/src/components/CopilotFleetReportPage.tsx` | Evidence/wording của intervention là review/coaching/human workflow; không có actuator command path được claim | Không claim automatic braking hoặc tự động can thiệp xe |
| Fleet Dashboard saved trips | `evidence/E-22/`, `SE/FE/src/data/btcTripData.ts`, `SE/FE/server.ts`, `SE/FE/src/App.tsx` | Source/UI evidence cho saved trip parser, completed trip context, dashboard/ranking/insights views | Saved trips là demo/replay context thật, không phải pilot field data |
| Bedrock Copilot | `evidence/E-20/`, `evidence/E-23/raw/bedrock_403_during_tmp_capture.log`, `SE/FE/server.ts`, `SE/FE/src/components/CopilotFleetReportPage.tsx` | Có fallback/status handling; provider failure log tồn tại; report giữ JSON/local baseline khi Bedrock lỗi | Bedrock là explanation layer, không phải canonical metrics |
| Human factors improvement | `evidence/E-39/reports/source_report.md`, `evidence/E-39/derived/human_factors_claim_register.json` | E-39 ghi rõ human-factors outcome chưa được đo bằng user study/pilot | Không claim giảm alert fatigue, reaction time hoặc acceptance nếu chưa có study |
| Long-run/multi-instance readiness | `evidence/E-36/`, `evidence/E-41/`, `evidence/tasks/Task_Nhan.md` | Các evidence này đang là partial/not-ready hoặc cần load-test/multi-instance architecture thêm | Đưa vào roadmap/caveat, không claim production reliability |

**Câu dùng khi bị hỏi:**  
Nhóm có evidence để chứng minh demo path hiện tại đang chạy qua CarSky và Android HMI, nhưng cũng ghi rõ boundary: speed-mux là fallback demo path; custom VSS, physical actuation, human-factors improvement và production long-run readiness chưa được claim nếu chưa có evidence tương ứng.

---

## 6.6. AI Engineering + CarSky: External Consumer Sử Dụng Capability Qua Interface / Artifact

Rubric yêu cầu chứng minh capability được **external consumer** sử dụng thực tế qua **interface** hoặc **artifact**. Với FPTU DMS Vision, phần chính không phải là “AI tự nói trong UI”, mà là **AI output được đóng gói thành capability có boundary rõ ràng** để nhiều consumer khác nhau dùng được.

Dự án có 2 lớp consumer chính:

1. **CarSky / Connected-car consumer:** CarSky runtime, KUKSA Signal Watch, Script Node, VHAL và Android HMI consume safety state qua signal/property interface.
2. **AI Engineering / Operational consumer:** Backend engineer, Fleet Manager, AI Copilot user, AI/SE maintainer và judge consume AI capability qua API contract, dashboard/report artifact, DOC export, tests và evidence scripts.

### 6.6.1. CarSky Consumer: AI/DMS State Được Consume Qua Signal + VHAL

| External consumer | Họ consume gì? | Interface / artifact | Evidence thật đang có | Ý nghĩa với rubric |
|---|---|---|---|---|
| CarSky Signal API / KUKSA Broker | DMS safety state được publish thành vehicle signal | `Vehicle.Speed` speed-mux | `evidence/E-24/raw/carsky_scenario_critical_command.json`, `evidence/E-24/raw/carsky_scenario_critical_parsed.json` | Chứng minh nhóm không tự dựng message bus riêng, mà dùng signal layer của CarSky |
| CarSky Signal Watch | Giá trị `Vehicle.Speed` thay đổi khi backend bắn scenario | Signal Watch UI screenshot | `evidence/E-24/screenshots/` | Chứng minh runtime observability trên platform, không chỉ source code |
| DMS HMI Bridge Script Node | Signal từ KUKSA được forward sang VHAL | Lua bridge: `pins.kuksa:on_change` -> `pins.vhal:push` | `SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua`, `evidence/E-24/reports/mapping.md` | Chứng minh reuse Script Node của CarSky để glue KUKSA với VHAL |
| Android VHAL / CarProperty path | Android nhận DMS state qua property layer | `PERF_VEHICLE_SPEED`, `CarPropertyManager` | `evidence/E-24/raw/hmi_apk_static_scan.log`, `evidence/E-24/derived/hmi_apk_artifact_from_E15.json` | Chứng minh APK bám vào Android Automotive mechanism, không chỉ polling REST |
| DMS Android HMI | Driver-facing UI hiển thị risk/safe score/TTC/speed/state | APK runtime UI artifact | `SE/HMI/release/dms-hmi-realtime-vhal.apk`, `evidence/E-24/screenshots/` | Chứng minh connected-car UI consume capability trong AAOS node |

**Câu chốt cho CarSky:**  
AI/DMS state được external runtime consumer của CarSky sử dụng qua chain `REST Signal API -> KUKSA Vehicle.Speed -> Script Node Bridge -> VHAL PERF_VEHICLE_SPEED -> Android CarPropertyManager -> HMI UI`. Đây là ecosystem alignment thực tế, vì flow dùng signal, node, bridge và AAOS/VHAL capability của platform.

### 6.6.2. AI Engineering Consumer: AI Capability Được Đóng Gói Thành API / Contract / Report / Evidence

| External consumer | Họ bấm/chạy/đọc gì? | Capability AI được consume là gì? | Interface / artifact | Evidence thật đang có |
|---|---|---|---|---|
| SE Backend engineer | Gửi/nhận alert payload qua backend | Canonical AI safety event đi qua backend boundary | `DecisionEvent`, `/api/v1/alerts`, `/api/v1/alerts/snapshot` | `evidence/E-03/`, `SE/BE/app/modules/ai_alerts/router.py`, `SE/BE/tests/test_ai_alerts.py` |
| CarSky integration engineer | Chạy `carsky_phase05.py scenario critical` | AI/DMS state được map sang CarSky signal transport | mapper/client/service + scenario runner | `evidence/E-24/raw/carsky_scenario_critical_command.json`, `SE/BE/app/integrations/carsky/`, `SE/BE/scripts/carsky_phase05.py` |
| Fleet Manager / demo reviewer | Mở Fleet Dashboard: saved trips, trip detail, ranking, insights | JSON/local AI metrics trở thành operational view | Fleet Dashboard UI | `evidence/E-22/`, `SE/FE/src/App.tsx`, `SE/FE/src/components/` |
| Report user | Mở safety/maintenance report và export DOC | AI/local telemetry được trình bày thành report artifact | Copilot Report UI + Word/DOC export | `evidence/E-21/`, `SE/FE/src/components/CopilotFleetReportPage.tsx` |
| AI Copilot user | Yêu cầu report/insight khi cần | Bedrock explanation layer có fallback, không thay canonical metrics | `/api/copilot`, `/api/copilot/report` | `evidence/E-20/`, `SE/FE/server.ts` |
| AI/SE maintainer | Chạy contract/factuality/failure checks | Compatibility guard khi model output hoặc provider thay đổi | golden payloads, contract tests, benchmark/fallback logs | `evidence/E-03/`, `evidence/E-19/`, `evidence/E-20/` |
| Demo operator / judge | Chạy runbook hoặc xem video evidence | Reproduce capability mà không cần vào model internals | README runbook, command logs, screenshots | `README_RUN_OUTPUT_007_CARSKY_HMI_EVIDENCE.md`, `evidence/E-24/README_PLATFORM_UTILIZATION_CARSKY_EVIDENCE.md`, `evidence/E-24/screenshots/` |

**Câu chốt cho AI Engineering:**  
External consumer không consume raw model trực tiếp. Họ consume AI capability qua boundary có thể kiểm thử và audit được: API contract, CarSky signal transport, Fleet Dashboard, Copilot Report, DOC artifact, golden payloads, benchmark/fallback logs và evidence scripts. Cách đóng gói này biến output AI thành engineering capability có thể tích hợp, reproduce và review.

### 6.6.3. Boundary Từ AI Core Ra External Consumer

```text
AI/local model output / telemetry JSON
  -> canonical DecisionEvent + trip metrics
  -> Backend API boundary
     - /api/v1/alerts
     - /api/v1/alerts/snapshot
  -> downstream consumers
     - Fleet Dashboard
     - AI Copilot Report + DOC export
     - CarSky Signal API / KUKSA
     - HMI Bridge / VHAL
     - Android HMI
     - tests / evidence scripts
```

### 6.6.4. Điều Không Claim Để Tránh Bị Bắt Bẻ

| Không claim | Lý do |
|---|---|
| Không claim external consumer dùng raw model trực tiếp | Consumer dùng contract/API/artifact, không dùng model internals |
| Không claim Bedrock là nguồn số liệu canonical | JSON/local AI telemetry là baseline; Bedrock chỉ diễn giải |
| Không claim custom VSS production-ready | Demo hiện dùng `Vehicle.Speed speed-mux` fallback |
| Không claim Android HMI tự gọi AI | APK consume VHAL property, không gọi AI trực tiếp |
| Không claim autonomous intervention | Intervention là human workflow/safety review |

### 6.6.5. Đoạn Copy Ngắn Vào Report

Về AI Engineering, capability của nhóm không dừng ở model output. AI/local telemetry được chuẩn hóa thành `DecisionEvent`, trip metrics và report contract để nhiều external consumer dùng được: Backend engineer consume qua `/api/v1/alerts`; CarSky integration engineer consume qua mapper và Signal API; Fleet Manager consume qua Dashboard/Report/DOC artifact; AI/SE maintainer consume qua golden payloads, contract tests và fallback benchmark; judge/demo operator consume qua runbook, command logs và screenshots.

Về CarSky, cùng capability này được đưa vào connected-car runtime bằng chain `Backend -> CarSky Signal API/KUKSA -> DMS HMI Bridge Script Node -> VHAL -> Android CarPropertyManager -> Android HMI`. Evidence hiện có gồm CarSky command output `ok=true`, `mode=vehicle-speed-mux`, `sent=14`, mapping report, APK SHA/static scan và screenshot runtime trong `evidence/E-24/screenshots/`. Như vậy, dự án chứng minh ecosystem alignment bằng interface/artifact thật, không chỉ bằng mô tả kiến trúc.

---

## 6.7. Why This Should Score High

| Rubric question | Câu trả lời ngắn | Evidence backing |
|---|---|---|
| CarSky mapping có rõ không? | Có. Backend -> Signal API/KUKSA -> Script Bridge -> VHAL -> Android HMI | E-24 mapping + command output + APK scan |
| Có reuse CarSky capability không? | Có. Reuse blueprint orchestration, Signal API/KUKSA, Signal Watch, Script Node, Skycraft/AAOS, VHAL path | E-24 |
| Có end-to-end proof không? | Có command/log/artifact proof; cần gắn thêm Drive video same-event để chốt runtime visual | E-24 + external Drive placeholder |
| Có phân biệt generic/planned không? | Có. Speed-mux là fallback demo; custom VSS/production reliability không overclaim | E-24 caveat |
| AI Engineering có external consumer không? | Có. Backend engineer, CarSky engineer, Fleet Manager, Copilot user, maintainer, judge consume qua API/artifact/script | E-03/E15/E20/E21/E22/E24 |

---

## 6.8. Đoạn Copy Vào Báo Cáo

FPTU DMS Vision có platform utilization thực tế trên CarSky. Nhóm không chỉ chạy một UI độc lập, mà đưa DMS safety state qua chain của platform: Backend publish AI/DMS event vào CarSky Signal API/KUKSA dưới dạng `Vehicle.Speed speed-mux`; DMS HMI Bridge trong CarSky Script Node subscribe signal này và forward sang VHAL `PERF_VEHICLE_SPEED`; Android HMI chạy trên Skycraft/AAOS node đọc property bằng `CarPropertyManager` và hiển thị trạng thái tài xế/risk/TTC/speed/safe score.

Những capability của CarSky được tái sử dụng gồm blueprint orchestration, KUKSA signal state, Signal Watch, Script Node, Skycraft/AAOS node và VHAL/CarProperty path. Evidence hiện có gồm command runtime trả `ok=true`, `mode=vehicle-speed-mux`, `sent=14`; mapping report Backend -> KUKSA -> Bridge -> VHAL -> HMI; APK artifact SHA256 và static scan; cùng source/test evidence cho Backend, Fleet Dashboard và AI Copilot fallback.

Về AI Engineering, AI capability không bị nhúng tùy ý vào UI. Các consumer bên ngoài AI core consume capability qua interface/artifact rõ ràng: Backend dùng `DecisionEvent` và `/api/v1/alerts`; CarSky integration dùng mapper/client/script publish signal; Fleet Manager dùng Dashboard/Report/DOC export; AI/SE maintainer dùng contract tests và golden payloads; judge/demo operator dùng runbook, command log và video evidence. Điều này chứng minh output AI đã được đóng gói thành capability có thể tích hợp, kiểm thử và audit.

Giới hạn được ghi nhận trung thực: bản demo đang dùng `Vehicle.Speed speed-mux` như fallback thay vì custom VSS production path; không claim physical actuator control; không claim human-factors improvement hoặc long-run production reliability nếu chưa có pilot/load-test evidence.

---

## 6.9. Checklist Trước Khi Nộp

- [ ] Gắn Drive link same-event runtime video vào E-24 nếu có.
- [ ] Video nên show cùng một event: backend command -> Signal Watch `Vehicle.Speed` đổi -> bridge log -> Android HMI UI đổi.
- [ ] Không ghi “custom VSS production-ready” nếu chưa có evidence.
- [ ] Không ghi “auto intervention” hoặc “automatic braking”; chỉ ghi human workflow / safety review.
- [ ] Không ghi Bedrock là nguồn metric canonical; JSON/local AI mới là baseline metric.
- [ ] Nếu dùng screenshot temporary từ E-21/E-22, ghi rõ là UI/sample evidence, không phải pilot field data.
