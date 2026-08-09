# README Copy-Ready: Các Mục Cần Thay Trong FPTU DMS Vision Report

## Cách Dùng

File này viết sẵn các đoạn **copy-paste ready** để thay vào report `FPTU_DMS_VISION_REPORT_REWWRITEN`.

Ngôn ngữ:

- Nội dung giải thích: tiếng Việt.
- Keyword kỹ thuật: giữ tiếng Anh, ví dụ `Fleet Dashboard`, `AI Copilot`, `Bedrock`, `KUKSA`, `VHAL`, `CarPropertyManager`, `PERF_VEHICLE_SPEED`, `speed-mux`.

Trọng tâm thay đổi:

- Fleet Dashboard.
- AI Copilot / Bedrock fallback.
- Saved trips / JSON local AI.
- CarSky / KUKSA / VHAL.
- Android HMI APK.
- Boundary Status.

---

# 1. Thay Mục 2.7 — Từ AI Output Đến System Demonstration

## Đoạn Nên Thay

Thay đoạn mô tả flow runtime/product demo bằng đoạn dưới đây:

```text
Sau khi tạo kết quả C1/C2/C3, một nhánh thứ hai sử dụng các signal này cho system demonstration. Luồng này không thay đổi scored CSV và không ảnh hưởng đến evaluator của BTC.

Luồng runtime/product demonstration:

C1/C2/C3 Outputs
↓
Decision Engine
↓
Canonical DecisionEvent / Live Telemetry Snapshot
↓
FastAPI Backend
↓
Fleet Dashboard

Với event dành cho tài xế, luồng connected-car tiếp tục:

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

Decision Engine không thay thế Challenge 3 và không thay đổi scored CSV. Đây là lớp runtime riêng sử dụng temporal quality gate, persistence, hysteresis, cooldown và event lifecycle để chuyển prediction theo frame thành event có thể dùng trong demo.

Một DecisionEvent có thể chứa event_id, severity, reason, evidence, recommended_action, audience và lifecycle. Nhờ tách hai layer, evaluator của BTC vẫn đánh giá prediction thuần túy, trong khi system demo thể hiện cách kết quả AI được sử dụng trong Fleet Dashboard và Driver HMI.
```

---

# 2. Thay Mục 2.8 — Component Boundaries

## Bảng Component Boundaries Nên Dùng

Thay bảng component boundary cũ bằng bảng dưới đây:

```text
Component | Input chính | Output chính | Vai trò
C1 TTC Pipeline | Stereo road image + calibration | predicted_ttc | Ước lượng collision risk
C2 Driver State Pipeline | Driver image | predicted_driver_state | Nhận diện trạng thái tài xế
C3 Risk Pipeline | Kinematics + TTC | predicted_risk_score | Tổng hợp risk cấp frame/trip
CSV Generator | C1/C2/C3 results | Scored CSV | Submission contract
Decision Engine | AI outputs + context | DecisionEvent / lifecycle event | Runtime event generation
Backend | DecisionEvent + telemetry snapshot | REST/WebSocket data + CarSky payload | Event distribution
Fleet Dashboard | Backend REST/WebSocket + saved trip JSON | Fleet/trip views, ranking, insight, report | System demonstration cho fleet manager
AI Copilot | JSON/local AI canonical metrics + report context | Validated Bedrock insight khi có | Explanation layer, không tạo canonical metrics
CarSky / KUKSA | Backend-published DMS values | Vehicle signal state | Connected-car demonstration
DMS HMI Bridge | KUKSA Vehicle.Speed / DMS signal state | VHAL PERF_VEHICLE_SPEED speed-mux | Bridge từ CarSky signal sang Android VHAL
Android HMI APK | Android CarPropertyManager PERF_VEHICLE_SPEED | Driver alert + risk/TTC/status/action/speed UI | Driver-facing HMI, verified for demo
```

## Đoạn Kết Luận Boundary Nên Dùng

Đặt ngay dưới bảng:

```text
Ranh giới implementation hiện tại: AI -> Decision Engine và Decision Engine -> Backend đã implemented. Backend -> Fleet Dashboard đã implemented với REST/WebSocket, saved trip loading, ranking, trip detail, report và AI Copilot. Backend -> CarSky REST Signal API, CarSky -> KUKSA / DMS Signal Broker và KUKSA -> DMS HMI Bridge đã verified qua Signal Watch/API response và bridge log.

Đường HMI Android đã verified cho demo theo hướng VHAL PERF_VEHICLE_SPEED speed-mux. Custom DMS Android CarProperty IDs không được dùng làm đường chính vì AAOS runtime hiện không expose ổn định các property này. APK V2.2 đọc Android CarPropertyManager, decode speed-mux và hiển thị risk, severity, driver state, alertness, TTC, AI status, recommended action, real speed và safe score.
```

---

# 3. Thay Mục 2.9 — Phạm Vi Chạy Thật, Replay, Simulated Và Partial

## Bảng Nên Dùng

Thay bảng mode cũ bằng bảng dưới đây:

```text
Mode | Nguồn dữ liệu | Mục đích | Trạng thái
Dataset evaluation | BTC Practice/Scored trips | Tạo prediction và evaluator CSV | Implemented / evaluated trên Practice
CARLA data generation | CARLA Simulator | Bổ sung training/scenario coverage cho C1 | Implemented; reproducibility package đang hoàn thiện
Dataset replay demo | Road + driver + telemetry từ trip | AI -> Backend -> Fleet Dashboard | Implemented / demo scope
Hybrid-live demo | Dataset road/telemetry + webcam driver | DMS live và integration | Demo scope
Fleet Dashboard | Backend REST/WebSocket + saved trip JSON | Map, trip detail, ranking, insights, reports | Implemented
AI Copilot report | JSON/local AI canonical metrics + Bedrock explanation | Safety/Maintenance detail & overview reports | Implemented with graceful fallback
Connected-Car flow | DecisionEvent / telemetry snapshot -> CarSky Signal API | Vehicle signal delivery | Verified to KUKSA / HMI Bridge
Android HMI realtime | VHAL PERF_VEHICLE_SPEED speed-mux -> Android CarPropertyManager -> APK | Hiển thị alert, risk, TTC, AI status, action, speed và safe score trên HMI | Verified for demo / deployment-dependent
Jetson edge runtime | Camera/runtime pipeline | Chạy demo trên edge target | In progress
```

## Note Nên Thêm Sau Bảng

```text
Ghi chú Connected-Car/HMI: Do AAOS runtime trong CarSky hiện expose ổn định PERF_VEHICLE_SPEED hơn các custom DMS CarProperty, nhóm sử dụng cơ chế speed-mux qua Vehicle.Speed để truyền nhiều giá trị DMS như risk score, severity, driver state, alertness, TTC, AI status, recommended action, real speed và safe score. APK V2.2 decode các mux group này và render lên Driver HMI. Đây là workaround đã verified cho demo, không làm thay đổi scored submission flow.
```

---

# 4. Thay Mục CarSky / Android HMI

## Đoạn Kiến Trúc Nên Dùng

```text
Phân hệ CarSky / Android HMI được dùng để chứng minh luồng cảnh báo tới tài xế trong connected-car environment.

Kiến trúc runtime hiện tại:

Backend/AI
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

CarSky Blueprint sử dụng 3 node chính:

1. DMS Signal Broker: KUKSA / signal node nhận giá trị do Backend publish.
2. DMS HMI Bridge: subscribe signal từ KUKSA và forward sang Android VHAL.
3. DMS Android HMI: native Android APK chạy trên Android Automotive OS, đọc CarPropertyManager và render cảnh báo.

Trong runtime hiện tại, hệ thống không phụ thuộc vào custom DMS Android CarProperty IDs. Thay vào đó, các giá trị DMS được multiplex qua property chuẩn PERF_VEHICLE_SPEED vì property này được AAOS runtime expose ổn định.
```

## Bảng Speed-Mux Nên Dùng

```text
Mux Group | Ý nghĩa | Ví dụ
41.xxx | Risk Score | 41.088 nghĩa là risk score 88
42.xxx | Severity | 42.002 nghĩa là CRITICAL
43.xxx | Driver State | 43.004 nghĩa là microsleep
44.xxx | Alertness Score | 44.075 nghĩa là alertness 75
45.xxx | Min TTC | 45.025 nghĩa là TTC 2.5s theo encoder scale
46.xxx | Critical Alert | 46.001 nghĩa là critical alert true
47.xxx | AI Status | 47.000 nghĩa là AI ONLINE
48.xxx | Recommended Action | 48.002 nghĩa là TAKE_BREAK hoặc action mapped tương ứng
49.xxx | Real Speed | 49.048 nghĩa là speed khoảng 48 km/h
50.xxx | Safe Driving Score | 50.083 nghĩa là safe score 83
```

## Đoạn Giải Thích Vì Sao Dùng Speed-Mux

```text
Lý do dùng speed-mux: khi kiểm tra Android CarService trong CarSky AAOS runtime, property chuẩn PERF_VEHICLE_SPEED được expose ổn định, trong khi các custom DMS CarProperty như Risk, AIStatus, Alertness, DriverState hoặc TTC không xuất hiện ổn định trong CarPropertyService. Vì vậy, để bảo đảm demo end-to-end chạy được, nhóm sử dụng Vehicle.Speed / PERF_VEHICLE_SPEED làm transport đã verified, sau đó APK decode lại thành state HMI.
```

---

# 5. Thay Mục Boundary Status Cho Connected-Car

## Bảng Boundary Status Nên Dùng

```text
Boundary | Trạng thái | Ý nghĩa / evidence
AI -> Decision Engine | IMPLEMENTED | AI outputs được chuyển thành runtime event/telemetry input.
Decision Engine -> Backend | IMPLEMENTED | Backend nhận normalized event/snapshot qua API contract.
Backend -> Fleet Dashboard | IMPLEMENTED | REST/WebSocket views, saved trips, ranking, insights và reports hoạt động từ live/saved data.
Backend -> CarSky REST Signal API | VERIFIED | Backend publisher gửi speed-mux values lên CarSky signal endpoint.
CarSky REST -> KUKSA / DMS Signal Broker | VERIFIED | Signal Watch/API response cho thấy Vehicle.Speed thay đổi.
KUKSA / DMS Signal Broker -> DMS HMI Bridge | VERIFIED | Bridge subscribe KUKSA và log forwarding khi Backend publish telemetry.
DMS HMI Bridge -> Android VHAL | VERIFIED FOR DEMO WITH SPEED-MUX | Bridge forward qua PERF_VEHICLE_SPEED 0x11600207.
Android VHAL -> Android CarPropertyManager | VERIFIED WITH DEPLOYMENT HOTFIX | APK đọc property bằng callback + polling fallback.
Android CarPropertyManager -> DMS Android HMI APK | VERIFIED | APK V2.2 decode mux groups và render HMI state.
```

## Đoạn Kết Luận Cho Boundary Status

```text
Kết luận boundary: Connected-Car / Driver HMI path đã verified cho demo qua Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux. Đây là đường truyền thực tế phù hợp với giới hạn hiện tại của CarSky AAOS runtime. Custom DMS CarProperty IDs không được claim là production-ready trong bản báo cáo này.
```

---

# 6. Thay Mục Fleet Dashboard

## Đoạn Mô Tả Fleet Dashboard Nên Dùng

```text
Fleet Dashboard là lớp vận hành cho Fleet Manager, nhận dữ liệu từ Backend qua REST/WebSocket và từ saved trip JSON đã được local AI tính toán trước. Dashboard không tạo lại canonical metric mà hiển thị và audit các giá trị đã có từ JSON/local AI như Ranking Score, Risk Score, TTC/headway, behavior flags, event log và maintenance triage.

Các màn hình chính gồm:

- Fleet Overview / Map: hiển thị danh sách trip, trạng thái risk và thông tin tổng quan.
- Trip Detail: hiển thị frame-level telemetry, synchronized camera frames, TTC, driver state và risk.
- Performance Insights: phân tích risk timeline và contributing factors của trip trong context fleet.
- Driver Ranking: xếp hạng theo Ranking Score riêng của dashboard; Average Risk được hiển thị để audit nhưng không quyết định thứ hạng.
- Ranking Analysis: giải thích công thức tính điểm, penalty breakdown và lý do thứ bậc.
- AI Copilot Drawer: trợ lý hỏi đáp fleet bằng tiếng Việt.
- Copilot Report Page: safety detail, safety overview, maintenance detail và maintenance overview.
```

## Đoạn Về Saved Trips Nên Dùng

```text
Dashboard hỗ trợ saved trips trong `SE/FE/src/data/saved_trips`. Các file này là completed trip context để test và demo khi AI runtime không chạy trực tiếp. FE server normalize legacy JSON có giá trị `Infinity` thành JSON hợp lệ trước khi browser đọc, giúp saved trips vẫn hiển thị đúng trên Dashboard và Report.
```

## Đoạn Về Ranking Nên Dùng

```text
Ranking trong Dashboard không còn dùng BTC safe score cũ làm cột sort. Hệ thống dùng canonical Ranking Score được tính từ JSON/local AI risk và behavior fields. Average Risk được thêm để audit mức độ nguy hiểm trung bình của trip nhưng không quyết định vị trí xếp hạng.
```

---

# 7. Thay Mục AI Copilot / Bedrock

## Đoạn Mô Tả AI Copilot Nên Dùng

```text
Fleet AI Copilot là explanation layer cho dữ liệu đã được JSON/local AI tính toán. AI Copilot không phải nguồn tạo canonical metric. Các chỉ số như Ranking Score, Risk Score, TTC, event count, maintenance priority và safe score đều lấy từ JSON/local AI hoặc rule-based triage của hệ thống.

Bedrock chỉ được dùng để diễn giải insight khi user mở report hoặc yêu cầu AI. Nếu Bedrock chưa trả về, timeout hoặc trả payload không hợp lệ, UI vẫn render deterministic report từ JSON/local AI và không hiển thị insight giả.
```

## Đoạn Về 4 Loại Report Nên Dùng

```text
AI Copilot Report hiện hỗ trợ 4 loại:

1. Safety Detail Report: đánh giá an toàn chi tiết cho một trip.
2. Safety Overview Report: tổng hợp an toàn toàn fleet / nhiều trip.
3. Maintenance Detail Report: đánh giá ưu tiên kiểm tra kỹ thuật cho một trip.
4. Maintenance Overview Report: tổng hợp ưu tiên kiểm tra kỹ thuật toàn fleet / nhiều trip.

Safety report tập trung vào risk, TTC/headway, behavior flags, event log và ranking. Maintenance report là inspection triage dựa trên safety telemetry, DTC thật nếu có và stress estimate; không tự kết luận hỏng hóc, không tự tạo work order và không tự báo giá nếu thiếu dữ liệu xưởng.
```

## Đoạn Về Bedrock Fallback Nên Dùng

```text
Cơ chế fallback của AI Copilot là Graceful AI Fallback with Local AI Telemetry Baseline.

Luồng hoạt động:

User mở report
↓
JSON/local AI report render ngay lập tức
↓
Bedrock được gọi lazy cho report đang xem
↓
Nếu Bedrock trả payload hợp lệ: UI cập nhật insight AI và hiển thị trạng thái đã validated
↓
Nếu Bedrock lỗi, timeout hoặc payload không hợp lệ: UI giữ JSON/local AI report và không hiển thị fake insight

Hệ thống có validation để chặn Bedrock bịa số liệu, trộn sai loại report hoặc mô tả metric bằng 0 như một rủi ro đang xảy ra.
```

## Đoạn Về Env Nên Dùng

```text
AI Copilot đọc Bedrock configuration từ `SE/BE/.env`. FE server không dùng `SE/FE/.env.local` làm source of truth cho Bedrock token. Sau khi thay token Bedrock trong `SE/BE/.env`, cần restart FE server để Express server đọc lại env.
```

---

# 8. Thay Mục Export Report

## Đoạn Nên Dùng

```text
Copilot Report hỗ trợ export dạng Word-compatible DOC. File DOC chứa đầy đủ summary metrics, trip cards, KPI context, technical data availability, recommendations, event evidence và validated Bedrock insight nếu có.

PDF export không được đưa vào final demo scope vì đường export PDF trên browser dễ lỗi style/render. Nhóm ưu tiên DOC export để đảm bảo nội dung báo cáo đầy đủ và có thể mở/chỉnh sửa/in lại bằng Microsoft Word hoặc công cụ tương thích.
```

---

# 9. Thay Mục KPI / Benchmark

## Bảng Claim Nên Điều Chỉnh

```text
Claim cũ | Claim nên dùng
Bedrock latency < 1.8s / 100% success | Bedrock integration đã verified với token/model hiện tại; latency phụ thuộc provider, token và kích thước report.
CarSky HMI fully production ready | CarSky HMI verified for demo through PERF_VEHICLE_SPEED speed-mux; deployment-specific route/hotfix có thể cần chạy lại.
PDF export passed | DOC export supported.
Custom DMS properties are registered | DMS values are transported through PERF_VEHICLE_SPEED speed-mux.
All reports are AI-generated | Reports render JSON/local AI first; Bedrock adds validated explanation only when available.
```

## Đoạn KPI Nên Dùng

```text
Các KPI demo nên được hiểu là evidence trên môi trường hiện tại, không phải cam kết production tuyệt đối. Với Bedrock, token có hạn dùng và latency phụ thuộc dịch vụ AWS. Với CarSky/HMI, đường truyền đã verified qua speed-mux, nhưng deployment mới có thể cần init lại VHAL route/relay theo runtime của CarSky.
```

---

# 10. Thay Mục Troubleshooting

## Bedrock Troubleshooting

```text
Lỗi Bedrock Authentication Failed:
- Kiểm tra token trong `SE/BE/.env`.
- Đảm bảo region đúng `ap-southeast-2`.
- Đảm bảo model ID đúng theo token hiện tại.
- Strip newline/whitespace nếu copy token từ portal.
- Restart FE server sau khi đổi token vì Express server đọc env lúc startup.
```

## Saved Trips Troubleshooting

```text
Saved trips có file nhưng FE không hiển thị:
- Kiểm tra `/api/trips/saved` có trả danh sách trip không.
- Kiểm tra `/api/trips/saved/<trip_id>` có parse JSON hợp lệ không.
- Legacy saved trip JSON có thể chứa `Infinity`; FE server cần normalize thành `null` trước khi browser đọc.
- Hard refresh browser hoặc restart FE nếu mới thêm/xóa file trong `src/data/saved_trips`.
```

## CarSky / HMI Troubleshooting

```text
HMI không update nhưng Signal Watch có data:
1. Kiểm tra `Vehicle.Speed` có nhận mux value trong range 41.xxx-50.xxx không.
2. Kiểm tra DMS HMI Bridge có log forward sang `PERF_VEHICLE_SPEED` 0x11600207 không.
3. Kiểm tra Android logcat có dòng `Registered DMS VHAL transport with speed-mux` không.
4. Kiểm tra APK đang cài là V2.2 hoặc mới hơn.
5. Nếu vừa deploy CarSky blueprint mới, cần chạy lại init/route/relay step theo runtime hiện tại.
6. Không quay lại custom DMS CarProperty path nếu `dumpsys car_service` chỉ expose `PERF_VEHICLE_SPEED`.
```

---

# 11. Đoạn Kết Luận Connected-Car Nên Dùng

```text
Connected-Car / Driver HMI của FPTU DMS Vision đã được chứng minh theo hướng phù hợp với runtime hiện tại của CarSky. Backend publish AI telemetry qua CarSky Signal API vào KUKSA, DMS HMI Bridge forward qua VHAL PERF_VEHICLE_SPEED speed-mux, và Android HMI APK decode dữ liệu từ CarPropertyManager để hiển thị cảnh báo cho tài xế.

Điểm quan trọng là luồng này không làm thay đổi submission CSV. Nó là nhánh system demonstration sử dụng cùng output AI để thể hiện business value: Fleet Manager thấy rủi ro trên Dashboard, còn tài xế nhận cảnh báo trực tiếp trên HMI trong xe.
```

---

# 12. Đoạn Kết Luận AI Copilot Nên Dùng

```text
Fleet AI Copilot được thiết kế theo nguyên tắc trustworthy AI reporting. JSON/local AI là nguồn canonical cho score, risk, TTC, event count và maintenance triage. Bedrock không được phép tạo số liệu mới hoặc thay thế metric gốc; Bedrock chỉ diễn giải insight khi phản hồi hợp lệ.

Nếu Bedrock không phản hồi, hệ thống vẫn hiển thị báo cáo deterministic từ JSON/local AI. Nếu Bedrock trả payload hợp lệ, UI cập nhật insight và giữ kết quả này bằng cache/input signature để tránh bị fallback ghi đè ngược.
```

---

# 13. Checklist Cuối Trước Khi Chốt Report

```text
[ ] Không còn ghi AI Copilot lấy token từ SE/FE/.env.local.
[ ] Không còn claim PDF export là feature chính.
[ ] Không còn ghi Android HMI là blocked/partial nếu demo speed-mux đã chạy.
[ ] Không còn claim custom DMS CarProperty IDs là đường chính.
[ ] Có giải thích PERF_VEHICLE_SPEED speed-mux.
[ ] Có nói rõ JSON/local AI là canonical baseline.
[ ] Có nói rõ Bedrock chỉ là explanation layer.
[ ] Có tách scored submission flow khỏi product demo flow.
[ ] Có ghi CarSky/HMI là verified for demo / deployment-dependent, không nói quá thành production-ready tuyệt đối.
[ ] Nếu nhắc bridge script, đảm bảo contract đang nói là mux group 41.xxx-50.xxx, không lẫn legacy 10000+ encoding.
```
