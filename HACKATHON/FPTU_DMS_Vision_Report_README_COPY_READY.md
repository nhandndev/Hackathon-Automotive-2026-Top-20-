# README Copy-Ready Cho `FPTU_DMS_Vision_Report.md`

## Cách Dùng File Này

File này là bản hướng dẫn **copy-paste ready** để sửa report `FPTU_DMS_Vision_Report.md`.

Mình đã đối chiếu với code hiện tại của các phần chính:

- `Fleet Dashboard`: `SE/FE`
- `AI Copilot / Bedrock`: `SE/FE/server.ts`, `CopilotFleetReportPage.tsx`
- `Saved trips / JSON local AI`: `SE/FE/src/data/saved_trips`, `btcTripData.ts`, `App.tsx`
- `Backend CarSky publisher`: `SE/BE/app/integrations/carsky`
- `Android HMI APK`: `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java`
- `CarSky / KUKSA / VHAL`: blueprint + bridge runtime

Ngôn ngữ nên dùng trong report:

- Phần giải thích: tiếng Việt.
- Keyword kỹ thuật: giữ tiếng Anh, ví dụ `Fleet Dashboard`, `AI Copilot`, `Bedrock`, `KUKSA`, `VHAL`, `CarPropertyManager`, `PERF_VEHICLE_SPEED`, `speed-mux`.

Lưu ý quan trọng:

- Trong workspace hiện tại chưa thấy file `FPTU_DMS_Vision_Report.md`; chỉ thấy `FPTU_DMS_VISION_REPORT_REWRITE_CHANGE_REQUESTS.md`. Vì vậy các mục bên dưới viết theo heading phổ biến trong report. Nếu file report nằm ngoài repo, chỉ cần copy đúng block vào mục tương ứng.
- Không nên claim `custom DMS CarProperty` là production-ready. Đường HMI đã verify cho demo hiện tại là `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`.
- Không nên claim `PDF export` nữa. Report export hiện nên ghi là `Word/DOC export`.
- Không nên ghi `AI Copilot` lấy token từ `SE/FE/.env.local`. Source of truth hiện tại là `SE/BE/.env`.

---

# 1. Executive Summary Nên Thay

## Đoạn Copy Vào Report

```text
FPTU DMS Vision là hệ thống Driver Monitoring & Fleet Safety platform, kết hợp AI perception, backend runtime, Fleet Dashboard và connected-car HMI.

Hệ thống có hai luồng chính:

1. Scored AI flow: tạo kết quả C1/C2/C3 theo format evaluator, không bị thay đổi bởi dashboard hoặc HMI.
2. Product demonstration flow: sử dụng output AI đã chuẩn hóa để hiển thị realtime trên Fleet Dashboard và Driver HMI trong môi trường CarSky.

Fleet Dashboard đã implemented các chức năng vận hành như fleet overview, trip detail, ranking, performance insights, safety report, maintenance report, AI Copilot và Word/DOC export. Dashboard hiển thị metric từ JSON/local AI trước; Bedrock chỉ được dùng làm explanation layer khi user mở report và phản hồi AI hợp lệ.

Connected-Car / Android HMI đã verified cho demo bằng đường `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`. Backend publish DMS values lên CarSky, HMI Bridge forward qua VHAL, APK đọc bằng Android `CarPropertyManager` và decode thành risk, severity, driver state, alertness, TTC, recommended action, real speed và safe score.

Điểm cần ghi rõ trong report: HMI hiện là verified demo path, phụ thuộc deployment/runtime CarSky. Custom DMS Android CarProperty IDs không được claim là production-ready vì AAOS runtime hiện không expose ổn định các property này.
```

---

# 2. Thay Mục System Architecture / Overall Flow

## Đoạn Copy Vào Report

```text
Kiến trúc tổng thể gồm bốn lớp:

AI / Local Model Layer
↓
Backend Runtime Layer
↓
Fleet Dashboard & AI Copilot Layer
↓
Connected-Car / Android HMI Layer

Scored evaluation flow:

C1 TTC Prediction
↓
C2 Driver State Prediction
↓
C3 Risk Score Prediction
↓
CSV Generator
↓
BTC Evaluator

Product demonstration flow:

AI output / local AI telemetry
↓
Decision Engine
↓
FastAPI Backend
↓
REST API + WebSocket
↓
Fleet Dashboard

Driver-facing connected-car branch:

DecisionEvent / Live Telemetry Snapshot
↓
Backend CarSky Publisher
↓
CarSky REST Signal API
↓
KUKSA / DMS Signal Broker
↓
DMS HMI Bridge
↓
VHAL PERF_VEHICLE_SPEED speed-mux
↓
Android CarPropertyManager
↓
DMS Android HMI APK

Product demonstration flow không thay đổi scored CSV. Nó chỉ dùng AI output sau khi đã chuẩn hóa thành telemetry snapshot hoặc DecisionEvent để demo vận hành thực tế.
```

---

# 3. Thay Mục Component Boundaries

## Bảng Copy Vào Report

```text
Boundary | Status | Ý nghĩa / Evidence
AI -> Decision Engine | IMPLEMENTED | AI outputs được chuẩn hóa thành runtime event/telemetry input.
Decision Engine -> Backend | IMPLEMENTED | Backend nhận normalized event/snapshot qua API contract.
Backend -> Fleet Dashboard | IMPLEMENTED | REST/WebSocket, saved trips, ranking, insights và reports hoạt động từ live/saved data.
Saved trip JSON -> Fleet Dashboard | IMPLEMENTED | Saved JSON được normalize thành completed trips để demo/replay khi runtime không chạy trực tiếp.
Fleet Dashboard -> AI Copilot | IMPLEMENTED | Report render JSON/local AI trước; Bedrock lazy-call và chỉ replace khi payload hợp lệ.
Backend -> CarSky REST Signal API | VERIFIED | Backend publisher gửi speed-mux values lên CarSky signal endpoint.
CarSky REST -> KUKSA / DMS Signal Broker | VERIFIED | Signal Watch/API response cho thấy `Vehicle.Speed` thay đổi.
KUKSA / DMS Signal Broker -> DMS HMI Bridge | VERIFIED | Bridge subscribe KUKSA và forward signal sang VHAL.
DMS HMI Bridge -> Android VHAL | VERIFIED FOR DEMO WITH SPEED-MUX | Bridge forward qua `PERF_VEHICLE_SPEED` / `0x11600207`.
Android VHAL -> Android CarPropertyManager | VERIFIED WITH DEPLOYMENT HOTFIX | APK đọc property bằng callback + polling fallback.
Android CarPropertyManager -> DMS Android HMI APK | VERIFIED | APK V2.2 decode mux groups và render HMI state.
```

## Đoạn Kết Luận Sau Bảng

```text
Connected-Car / Driver HMI path đã verified cho demo qua `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`. Đây là đường truyền thực tế phù hợp với giới hạn hiện tại của CarSky AAOS runtime. Custom DMS CarProperty IDs không được claim là production-ready trong bản báo cáo này.
```

---

# 4. Thay Mục Fleet Dashboard

## Đoạn Copy Vào Report

```text
Fleet Dashboard là lớp vận hành cho Fleet Manager. Dashboard nhận dữ liệu từ Backend qua REST/WebSocket và từ saved trip JSON đã được local AI tính toán trước.

Dashboard không tự bịa metric và không tính lại canonical AI output ở frontend. Các số liệu chính như Ranking Score, Risk Score, TTC/headway, behavior flags, event log, harsh event, near miss và maintenance triage được lấy từ JSON/local AI hoặc Backend normalized data.

Các màn hình chính:

- Fleet Overview / Map: hiển thị danh sách trip, trạng thái risk và thông tin tổng quan.
- Trip Detail: hiển thị frame-level telemetry, synchronized camera frames, TTC, driver state và risk.
- Performance Insights: phân tích risk timeline và contributing factors của trip, đồng thời giữ fleet context.
- Driver Ranking: xếp hạng theo Ranking Score riêng của dashboard.
- Ranking Analysis: giải thích công thức tính điểm, penalty breakdown và lý do thứ bậc.
- AI Copilot Drawer: trợ lý hỏi đáp fleet bằng tiếng Việt.
- Copilot Report Page: safety detail, safety overview, maintenance detail và maintenance overview.
- Word/DOC Export: xuất report đầy đủ ở định dạng Word-compatible `.doc`.

Ranking trong Dashboard dùng canonical Ranking Score từ JSON/local AI risk và behavior fields. Average Risk được hiển thị để audit mức độ rủi ro trung bình nhưng không quyết định vị trí xếp hạng.
```

## Đoạn Về Saved Trips

```text
Saved trips được lưu tại `SE/FE/src/data/saved_trips`. Đây là completed trip context để test dashboard, report và AI Copilot khi không chạy live AI runtime.

Một số saved JSON legacy có thể chứa giá trị `Infinity` cho TTC khi không có nguy cơ va chạm tức thời. FE server normalize giá trị này thành JSON hợp lệ trước khi browser đọc, giúp saved trips vẫn hiển thị đúng trên Fleet Dashboard và Copilot Report.
```

---

# 5. Thay Mục AI Copilot / Bedrock

## Đoạn Copy Vào Report

```text
AI Copilot là explanation layer cho report, không phải nguồn tạo canonical metric.

Luồng xử lý report:

1. User mở report safety detail, safety overview, maintenance detail hoặc maintenance overview.
2. UI render ngay report deterministic từ JSON/local AI để không chặn trải nghiệm người dùng.
3. Frontend lazy-call Bedrock cho đúng report đang xem.
4. Nếu Bedrock trả payload hợp lệ, UI cập nhật insight AI và hiển thị trạng thái validated.
5. Nếu Bedrock timeout, lỗi token, lỗi provider hoặc trả payload không hợp lệ, UI giữ report JSON/local AI và không hiển thị insight giả.

Bedrock chỉ được dùng để diễn giải, tổng hợp và viết nhận xét theo context report. Bedrock không được phép ghi đè canonical metric như Ranking Score, Risk Score, TTC, số frame, harsh event, near miss hoặc maintenance KPI nếu các số này đã có trong JSON/local AI.
```

## Đoạn Về Fallback

```text
Hệ thống dùng Graceful AI Fallback:

JSON/local AI report là baseline deterministic.
Bedrock insight là enhancement khi có phản hồi hợp lệ.
UI không dùng mock/static insight thay thế khi Bedrock lỗi.
Validated Bedrock result được giữ lại và không bị local fallback ghi đè lại trong cùng context report.
Nếu user đóng report hoặc đổi context, request AI của context cũ không nên tiếp tục chiếm ưu tiên UI.
```

## Đoạn Về Env

```text
Bedrock configuration được đọc từ `SE/BE/.env`.

Các biến chính:

AWS_BEARER_TOKEN_BEDROCK
AWS_REGION hoặc AWS_DEFAULT_REGION
BEDROCK_MODEL_ID

FE server không dùng `SE/FE/.env.local` làm source of truth cho Bedrock token. Sau khi thay token trong `SE/BE/.env`, cần restart FE server để Express server đọc lại env mới.
```

## Trạng Thái UI Nên Ghi

```text
Khi đang chờ Bedrock, UI hiển thị trạng thái "Đang chờ Bedrock..." hoặc "Đang chờ Bedrock phản hồi hợp lệ".

Khi Bedrock trả payload hợp lệ, UI hiển thị trạng thái xanh:

AI Copilot đã trả về insight hợp lệ từ Bedrock.

Nội dung AI chỉ được đưa lên UI sau khi response được validate. Nếu response không hợp lệ, report giữ JSON/local AI baseline và không tạo insight giả.
```

---

# 6. Thay Mục Report Types

## Đoạn Copy Vào Report

```text
Copilot Report có 4 loại report riêng biệt:

1. Safety Detail
   - Scope: một trip.
   - Mục tiêu: đánh giá an toàn chi tiết của trip.
   - Data chính: Ranking Score, Trip Safety Risk, TTC/headway, driver behavior, harsh event, near miss, risk timeline, event log.
   - Bedrock role: diễn giải nguyên nhân, context và recommendation dựa trên metric có thật.

2. Safety Overview
   - Scope: toàn bộ loaded trips.
   - Mục tiêu: executive fleet safety report.
   - Data chính: fleet status, trips analyzed, safe trips, fleet average ranking score, high-risk frames, review priority, relative rank.
   - Bedrock role: tổng hợp fleet-level insight, không phân tích lần lượt từng trip như detail report.

3. Maintenance Detail
   - Scope: một trip.
   - Mục tiêu: đánh giá ưu tiên kiểm tra kỹ thuật/bảo trì của trip.
   - Data chính: maintenance priority, brake/tire stress, DTC availability, harsh behavior, risk exposure và action order.
   - Bedrock role: diễn giải kỹ thuật và đề xuất maintenance action.

4. Maintenance Overview
   - Scope: toàn bộ loaded trips.
   - Mục tiêu: fleet maintenance priority report.
   - Data chính: priority order, total maintenance exposure, stress summary, work order recommendation.
   - Bedrock role: tổng hợp ưu tiên bảo trì cấp fleet.

Mỗi report có prompt riêng và format riêng. Không dùng cùng một prompt cho cả safety và maintenance, cũng không dùng detail prompt cho overview report.
```

---

# 7. Thay Mục Export Report

## Đoạn Copy Vào Report

```text
Report export hiện hỗ trợ Word-compatible DOC export.

DOC export chứa:

- Report title và report type.
- Date range theo ngày hiện tại khi export.
- Fleet/trip summary metrics.
- Trip cards hoặc selected trip detail.
- Safety KPI context hoặc maintenance KPI context.
- Event evidence / statistical evaluation.
- JSON/local AI baseline evaluation.
- Validated Bedrock insight nếu đã có phản hồi hợp lệ.

PDF export không nằm trong final demo scope vì browser PDF rendering có thể mất style hoặc xuất trang trắng trong một số môi trường. Nhóm ưu tiên DOC export để đảm bảo report đầy đủ nội dung, có thể mở bằng Microsoft Word hoặc công cụ tương thích, sau đó người dùng có thể export PDF từ Word nếu cần.
```

---

# 8. Thay Mục CarSky / Android HMI

## Đoạn Kiến Trúc Copy Vào Report

```text
Phân hệ CarSky / Android HMI được dùng để chứng minh luồng cảnh báo tới tài xế trong connected-car environment.

Runtime architecture:

Backend / AI telemetry
↓
CarSky REST Signal API
↓
KUKSA / DMS Signal Broker
↓
DMS HMI Bridge
↓
VHAL `PERF_VEHICLE_SPEED` speed-mux
↓
Android `CarPropertyManager`
↓
DMS Android HMI APK

CarSky Blueprint sử dụng 3 node chính:

1. DMS Signal Broker: KUKSA / signal node nhận giá trị do Backend publish.
2. DMS HMI Bridge: subscribe signal từ KUKSA và forward sang Android VHAL.
3. DMS Android HMI: native Android APK chạy trên Android Automotive OS, đọc `CarPropertyManager` và render cảnh báo.

Trong runtime hiện tại, hệ thống không phụ thuộc vào custom DMS Android CarProperty IDs. Thay vào đó, các giá trị DMS được multiplex qua property chuẩn `PERF_VEHICLE_SPEED` vì property này được AAOS runtime expose ổn định hơn.
```

## Bảng Speed-Mux Copy Vào Report

```text
Mux Group | Meaning | Example
41.xxx | Risk Score | 41.088 = risk score 88
42.xxx | Severity | 42.000 = SAFE, 42.001 = WARNING, 42.002 = CRITICAL
43.xxx | Driver State | 43.000 = alert, 43.001 = drowsy, 43.003 = distracted, 43.004 = microsleep
44.xxx | Alertness Score | 44.075 = alertness 75%
45.xxx | Min TTC | 45.025 = TTC 2.5s
46.xxx | Critical Alert | 46.001 = critical alert true
47.xxx | AI Status | 47.000 = ONLINE, 47.001 = DEGRADED, 47.002 = OFFLINE
48.xxx | Recommended Action | 48.001 = FOCUS_FORWARD, 48.002 = TAKE_BREAK, 48.003 = BRAKE_SAFE
49.xxx | Real Speed | 49.048 = speed khoảng 48 km/h
50.xxx | Safe Driving Score | 50.083 = safe score 83/100
```

## Đoạn Giải Thích Vì Sao Dùng Speed-Mux

```text
Lý do dùng speed-mux: khi kiểm tra Android CarService trong CarSky AAOS runtime, property chuẩn `PERF_VEHICLE_SPEED` được expose ổn định, trong khi các custom DMS CarProperty như Risk, AIStatus, Alertness, DriverState hoặc TTC không xuất hiện ổn định trong `CarPropertyService`.

Vì vậy, để bảo đảm demo end-to-end chạy được, nhóm sử dụng `Vehicle.Speed / PERF_VEHICLE_SPEED` làm transport đã verified, sau đó APK V2.2 decode lại thành state HMI.
```

## Đoạn Về APK

```text
DMS Android HMI APK là native Android app chạy trên Android Automotive / CarSky Skycraft runtime.

APK đọc `PERF_VEHICLE_SPEED` bằng hai cơ chế:

- Callback: nhận event từ `CarPropertyManager`.
- Polling fallback: đọc lại property định kỳ để tránh trường hợp callback không ổn định trong runtime demo.

APK V2.2 render hoàn toàn bằng tiếng Anh để phù hợp Driver HMI:

- AI status
- Driver state
- Alertness
- TTC
- Risk Score
- Safe Score
- Real speed km/h
- Recommended action
- ECU reaction
- Voice alert state

Khi không có data, APK hiển thị waiting/offline state thay vì hiển thị số liệu giả.
```

---

# 9. Thay Mục VHAL / Custom Properties

## Đoạn Copy Vào Report

```text
Ban đầu nhóm thử hướng custom DMS VHAL properties cho các metric như FinalRiskScore, CriticalAlert, AlertnessScore, MinTTC, AIStatus, RecommendedAction, Severity và DriverState.

Tuy nhiên, trong CarSky AAOS runtime hiện tại, custom DMS CarProperty IDs không được expose ổn định qua Android `CarPropertyService`. Vì vậy nhóm chuyển sang đường verified hơn:

`Vehicle.Speed` trên KUKSA
↓
`PERF_VEHICLE_SPEED` trên VHAL
↓
Android `CarPropertyManager`
↓
APK decode speed-mux

Đường này vẫn truyền đủ logical DMS values cần cho demo, nhưng chỉ dùng một property chuẩn làm transport.

Trong report final, không nên ghi rằng custom DMS properties đã fully implemented production-ready. Cách ghi đúng là:

"Custom DMS properties were evaluated, but the final demo uses `PERF_VEHICLE_SPEED` speed-mux because it is the verified path in the current CarSky AAOS runtime."
```

---

# 10. Thay Mục Implementation Status / KPI Table

## Bảng Copy Vào Report

```text
Feature | Status nên ghi | Ghi chú
C1/C2/C3 scored AI flow | IMPLEMENTED | Tách riêng khỏi dashboard/HMI demo flow.
Backend API | IMPLEMENTED | FastAPI REST/WebSocket cho dashboard và runtime events.
Fleet Dashboard | IMPLEMENTED | Map, trip detail, ranking, insights, reports, saved trips.
Saved trips replay | IMPLEMENTED | Completed trip JSON được normalize để test/demo.
AI Copilot / Bedrock | IMPLEMENTED WITH GRACEFUL FALLBACK | JSON/local AI baseline; Bedrock lazy-call và validated insight.
Safety Detail Report | IMPLEMENTED | Một trip, dùng safety prompt riêng.
Safety Overview Report | IMPLEMENTED | Fleet-level summary, không phân tích từng trip như detail.
Maintenance Detail Report | IMPLEMENTED | Một trip, maintenance priority/rule-based baseline + Bedrock explanation.
Maintenance Overview Report | IMPLEMENTED | Fleet-level maintenance priority.
Word/DOC Export | IMPLEMENTED | Export đầy đủ report content sang `.doc`.
PDF Export | OUT OF FINAL SCOPE | Không claim final do browser PDF có thể lỗi style/trang trắng.
Backend -> CarSky Signal API | VERIFIED | Publish speed-mux signals lên CarSky.
KUKSA -> HMI Bridge | VERIFIED | Bridge nhận signal và forward.
HMI Bridge -> Android VHAL | VERIFIED FOR DEMO | Dùng `PERF_VEHICLE_SPEED` speed-mux.
Android HMI APK | VERIFIED FOR DEMO / DEPLOYMENT-DEPENDENT | Cần đúng blueprint/deployment/relay runtime khi deploy mới.
Custom DMS CarProperty | NOT FINAL PATH | Đã khảo sát, nhưng không dùng làm primary path.
```

---

# 11. Thay Mục Demo Runbook

## Đoạn Copy Vào Report

```text
Demo end-to-end được chia thành hai nhánh:

1. Fleet Dashboard demo
   - Chạy Backend.
   - Chạy Frontend.
   - Load saved trips hoặc replay dataset.
   - Kiểm tra Map, Trip Detail, Ranking, Insights và Copilot Reports.
   - Mở report để trigger Bedrock lazy-call nếu có token hợp lệ.

2. CarSky / Android HMI demo
   - Deploy CarSky blueprint gồm DMS Signal Broker, DMS HMI Bridge và DMS Android HMI.
   - Cài APK V2.2 lên Android node.
   - Đảm bảo bridge script dùng `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`.
   - Nếu runtime yêu cầu, chạy VSOCK relay/hotfix sau deployment.
   - Backend publish telemetry snapshot lên CarSky.
   - Signal Watch thấy `Vehicle.Speed` thay đổi trong range mux `41.xxx` đến `50.xxx`.
   - APK hiển thị risk, severity, TTC, action, speed và safe score.

Khi deploy CarSky blueprint mới, route/relay có thể phải init lại vì runtime/pod có thể được tạo lại.
```

---

# 12. Thay Mục Troubleshooting

## Bảng Copy Vào Report

```text
Issue | Nguyên nhân thường gặp | Cách xử lý
Dashboard báo no trip | Saved JSON chưa load hoặc JSON legacy có Infinity | Kiểm tra `SE/FE/src/data/saved_trips`, restart FE server.
Bedrock stuck ở waiting | Token hết hạn, sai region/model hoặc request cũ chưa validate | Thay token trong `SE/BE/.env`, restart FE server, mở lại đúng report.
Bedrock trả sai format | LLM không tuân thủ prompt hoặc payload thiếu field | UI giữ JSON/local AI baseline, không render insight giả.
Report bị JSON fallback ghi đè Bedrock | State/cache chưa giữ validated payload | Chỉ replace khi payload `validated`; giữ validated result theo report signature.
Export PDF lỗi/trang trắng | Browser PDF render không ổn định | Dùng Word/DOC export trong final demo scope.
CarSky Signal Watch có data nhưng APK không đổi | VHAL bridge/relay/APK chưa cùng contract | Kiểm tra mux group `41.xxx-50.xxx`, bridge log và APK logcat.
APK chỉ hiện speed hoặc risk thiếu field | Backend/bridge chỉ publish một mux group | Publish đầy đủ mux groups 41-50 hoặc kiểm tra mapper.
APK waiting/offline | Chưa có VHAL data hoặc CarService không expose property | Kiểm tra `PERF_VEHICLE_SPEED`, CarProperty log, relay route.
Deploy CarSky mới xong mất HMI realtime | Runtime/pod mới làm mất relay/hotfix | Init lại relay/hotfix và restart route theo hướng dẫn deployment.
```

---

# 13. Những Câu Không Nên Ghi Trong Report

## Xóa Hoặc Thay Các Claim Này

```text
Sai / không nên ghi:
- AI Copilot token nằm trong SE/FE/.env.local.
- PDF export đã hoàn thiện.
- Android HMI dùng custom DMS CarProperty IDs làm đường chính.
- Custom VHAL properties fully production-ready.
- Toàn bộ report được AI generated.
- Bedrock luôn trả về trong latency cố định.
- HMI realtime không phụ thuộc deployment.
- Vehicle.ADAS.FinalRiskScore là path chính cho APK hiện tại.

Nên ghi:
- AI Copilot đọc Bedrock config từ SE/BE/.env.
- Report export dùng Word/DOC.
- Android HMI dùng Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux.
- Custom properties đã khảo sát nhưng không dùng làm final path.
- Report render JSON/local AI trước; Bedrock chỉ bổ sung validated insight.
- Bedrock latency phụ thuộc provider/token/report size.
- HMI verified for demo / deployment-dependent.
- Vehicle.Speed là transport path chính cho APK V2.2.
```

---

# 14. Evidence Paths Nên Ghi Trong Appendix

## Đoạn Copy Vào Report

```text
Representative implementation evidence:

- Backend CarSky mapper: `SE/BE/app/integrations/carsky/mapper.py`
- Backend CarSky client: `SE/BE/app/integrations/carsky/client.py`
- Backend CarSky publisher queue: `SE/BE/app/integrations/carsky/service.py`
- AI alerts runtime router: `SE/BE/app/modules/ai_alerts/router.py`
- Android HMI native APK: `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java`
- Fleet Dashboard server/env/report API: `SE/FE/server.ts`
- Copilot report UI: `SE/FE/src/components/CopilotFleetReportPage.tsx`
- Saved trip loading: `SE/FE/src/App.tsx`
- Saved trip static fallback parser: `SE/FE/src/data/btcTripData.ts`
```

---

# 15. Final Conclusion Nên Dùng

## Đoạn Copy Vào Report

```text
FPTU DMS Vision đã hoàn thiện demo end-to-end ở mức product demonstration: AI output được đưa vào Backend, Fleet Dashboard, AI Copilot report và connected-car Driver HMI.

Fleet Dashboard là lớp quản trị đội xe, hiển thị deterministic metrics từ JSON/local AI và chỉ dùng Bedrock để diễn giải insight khi response hợp lệ. Điều này giúp report không bị mock, không bịa số liệu và vẫn dùng được khi Bedrock timeout hoặc token hết hạn.

Connected-Car / Driver HMI đã verified qua CarSky bằng `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`. Đây là phương án phù hợp với giới hạn runtime hiện tại của CarSky AAOS, nơi property chuẩn speed expose ổn định hơn custom DMS CarProperty. APK V2.2 decode mux values và hiển thị driver-facing alert bằng tiếng Anh.

Các giới hạn còn lại chủ yếu nằm ở deployment/runtime: Bedrock token có hạn dùng, CarSky deployment mới có thể cần init lại route/relay, và custom DMS CarProperty chưa được claim là production-ready. Những giới hạn này đã có fallback và được ghi rõ trong report để đảm bảo tính minh bạch kỹ thuật.
```

---

# 16. Checklist Trước Khi Nộp Report

```text
[ ] Đổi mọi dòng `SE/FE/.env.local` liên quan Bedrock thành `SE/BE/.env`.
[ ] Đổi `PDF export` thành `Word/DOC export`.
[ ] Xóa claim custom DMS CarProperty fully implemented.
[ ] Ghi rõ HMI final path là `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`.
[ ] Ghi rõ Android HMI status là `Verified for demo / deployment-dependent`.
[ ] Ghi rõ Bedrock là explanation layer, không tạo canonical metrics.
[ ] Ghi rõ report render JSON/local AI trước, Bedrock replace sau khi validated.
[ ] Ghi rõ saved trips là completed trip context để test/demo.
[ ] Ghi rõ Safety Detail, Safety Overview, Maintenance Detail, Maintenance Overview là 4 report type riêng.
[ ] Ghi rõ PDF không nằm trong final demo scope nếu file report cũ còn nhắc PDF.
[ ] Thêm mux table `41.xxx-50.xxx`.
[ ] Thêm evidence paths ở appendix.
```

