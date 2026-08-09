# FPTU_DMS_Vision_Report.md — Section Fix Guide Copy-Ready

File này chỉ rõ **mục số bao nhiêu trong `FPTU_DMS_Vision_Report.md` cần thay đổi gì**, kèm đoạn **copy-paste full**.

Trọng tâm đã đối chiếu với code hiện tại:

- `Fleet Dashboard`: `SE/FE`
- `AI Copilot / Bedrock`: `SE/FE/server.ts`, `CopilotFleetReportPage.tsx`
- `Saved trips / JSON local AI`: `SE/FE/src/data/saved_trips`, `btcTripData.ts`, `App.tsx`
- `Backend -> CarSky`: `SE/BE/app/integrations/carsky`
- `Android HMI APK`: `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java`
- `VHAL / CarSky / KUKSA`: verified demo path bằng `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`

Nguyên tắc wording:

- Tiếng Việt cho phần giải thích.
- Keyword kỹ thuật giữ tiếng Anh: `Fleet Dashboard`, `AI Copilot`, `Bedrock`, `KUKSA`, `VHAL`, `CarPropertyManager`, `PERF_VEHICLE_SPEED`, `speed-mux`.
- Không claim quá mức: không ghi `custom DMS CarProperty production-ready`, không ghi `PDF export completed`, không ghi Bedrock lấy token từ `SE/FE/.env.local`.

---

# A. Danh Sách Mục Cần Thay Nhanh

| Mục trong report | Việc cần làm |
|---|---|
| Đoạn Executive Summary đầu report | Thay status Connected-Car/HMI cho đúng hiện tại |
| `3.1.4 Integration Baseline` | Thay bảng boundary |
| `3.1.5 Fleet Dashboard and AI Copilot Status` | Thay danh sách feature + trạng thái |
| `4.3 Phạm vi MVP dự thi` | Sửa MVP scope: DOC export, lazy Bedrock, speed-mux HMI |
| `5.1 Ranh giới trách nhiệm` | Thêm trách nhiệm của Frontend/HMI và AI Copilot |
| `5.2 Contract chuẩn` | Thêm rule `Infinity`, saved JSON, canonical metrics |
| `6. Hai nhánh vận hành và chiến lược demo` | Sửa Connected-car demo output/status |
| `6.1 Storyline 7-10 phút` | Sửa bước 5-6 để phản ánh report + HMI verified demo |
| `12.1 Năng lực hiện có` | Thêm CarSky publisher queue và speed-mux contract |
| `12.3.3 Latency Evidence` | Ghi rõ Bedrock latency khác safety-event latency |
| `12.3.4 Backpressure Evidence` | Ghi đúng CarSky queue transition priority |
| `12.3.6 Observability Evidence` | Thêm Copilot audit + thiếu correlation ID full |
| `13 Fleet Dashboard` | Thay toàn bộ mục 13 hoặc bổ sung block mới |
| `14 AI Copilot` | Thay/bổ sung guardrail Bedrock đúng hiện tại |
| `14.3.4 Fallback Scenarios` | Thay toàn bộ phần fallback |
| `15 Báo cáo tự động và export` | Thay PDF thành Word/DOC export |
| `16 Connected-Car, CarSky và Driver HMI` | Thay toàn bộ mục 16 |
| `16.1 Giá trị business của connected-car delivery` | Thay câu status cũ |
| `19 Trạng thái triển khai và ma trận bằng chứng` | Thay các dòng Fleet Dashboard, AI Copilot, CarSky, Android HMI |
| `22 Ma trận cạnh tranh` | Sửa dòng Connected-car HMI |
| `29 Rủi ro dự án` | Sửa risk VHAL/HMI và Copilot |
| `30 Roadmap` | Sửa P0 VHAL correlation + report export |
| `32.1 Narrative đề xuất` | Sửa honesty và proof |
| `32.2 Câu hỏi hội đồng` | Sửa câu trả lời “HMI đã end-to-end chưa?” |
| `33 Kết luận` | Thay kết luận cho đúng trạng thái hiện tại |
| `33.1.2 Hỗ trợ xử lý / xác nhận VHAL-CarProperty boundary` | Thay bằng boundary statement mới |

---

# 1. Đoạn Executive Summary Đầu Report

## Cần thay gì

Trong đoạn đầu report hiện có câu:

```text
Backend/REST → KUKSA và KUKSA → HMI Bridge: VERIFIED. VHAL multiplex transport: IMPLEMENTED. Android VHAL → APK live correlation: PARTIAL / verification pending...
```

Nếu demo hiện tại đã có APK V2.2 nhận update qua `CarPropertyManager`, hãy thay bằng block dưới.

## Copy-Paste Thay Vào

```text
AI Challenge 1/2/3, Decision Engine, FastAPI Backend và Fleet Dashboard có đường chạy demo; các claim định lượng trong báo cáo được gắn với Evidence ID tương ứng. [E-01][E-03][E-13][E-15][E-22]

Backend/REST → CarSky REST Signal API → KUKSA / DMS Signal Broker → HMI Bridge đã VERIFIED qua Signal Watch/API response và bridge log. Android HMI đã VERIFIED FOR DEMO bằng đường `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`: APK V2.2 đọc Android `CarPropertyManager`, decode mux groups và render risk, severity, driver state, alertness, TTC, AI status, action, real speed và safe score. Trạng thái này vẫn là deployment-dependent vì CarSky runtime mới có thể cần init lại route/relay. [E-24]

AI Copilot, Driver Ranking Report và Fleet Safety Executive Report đã có giao diện/endpoint phục vụ demo và export Word/DOC. Bedrock latency chỉ áp dụng cho Copilot generation, không đại diện cho safety-event latency. JSON/local AI là baseline deterministic; Bedrock chỉ bổ sung validated insight khi phản hồi hợp lệ. Factual audit, cost/governance và long-term stability còn cần evidence. [E-19][E-20][E-21]
```

---

# 2. Mục `3.1.4 Integration Baseline`

## Cần thay gì

Thay bảng hiện tại của mục `3.1.4` bằng bảng dưới. Bảng cũ đang ghi `HMI Bridge -> Android HMI IMPLEMENTED / PARTIAL`; nên đổi thành rõ hơn theo boundary mới.

## Copy-Paste Thay Vào

```text
3.1.4 Integration Baseline

Integration boundary
Current status
Current evidence

AI → Decision Engine
IMPLEMENTED
Event và inference artifact; AI output được chuẩn hóa thành runtime DecisionEvent / telemetry snapshot.

Decision Engine → Backend
IMPLEMENTED
API contract và backend tests; Backend nhận normalized alert/snapshot data.

Backend → Fleet Dashboard
IMPLEMENTED
REST/WebSocket, saved trip loading, snapshot và frontend build; Dashboard render map, trip detail, ranking, insights và reports.

Saved trip JSON → Fleet Dashboard
IMPLEMENTED
Saved completed trips được load từ `SE/FE/src/data/saved_trips`; legacy `Infinity` được normalize thành JSON hợp lệ trước khi browser đọc.

Fleet Dashboard → AI Copilot / Bedrock
IMPLEMENTED WITH GRACEFUL FALLBACK
Report render JSON/local AI baseline trước; Bedrock lazy-call theo report đang xem; chỉ replace UI khi payload hợp lệ.

Backend/REST → CarSky REST Signal API
VERIFIED
Backend publish DMS speed-mux values lên CarSky signal endpoint; Signal Watch/API response xác nhận `Vehicle.Speed` thay đổi. [E-24]

CarSky REST → KUKSA / DMS Signal Broker
VERIFIED
CarSky signal node lưu `Vehicle.Speed` values và expose cho bridge.

KUKSA / Signal Broker → DMS HMI Bridge
VERIFIED
HMI Bridge subscribe `Vehicle.Speed` và log speed-mux forwarding khi Backend publish telemetry. [E-24]

DMS HMI Bridge → Android VHAL
VERIFIED FOR DEMO WITH SPEED-MUX
Bridge forward qua `PERF_VEHICLE_SPEED` (`0x11600207`). Custom DMS CarProperty IDs không được dùng làm final path vì AAOS runtime hiện không expose ổn định.

Android VHAL → Android CarPropertyManager
VERIFIED WITH DEPLOYMENT HOTFIX
APK nhận updates bằng callback + polling fallback. Runtime phụ thuộc deployment/route/relay hiện tại của CarSky.

Android CarPropertyManager → DMS Android HMI APK
VERIFIED FOR DEMO
APK V2.2 decode speed-mux groups và cập nhật HMI UI cho risk, severity, driver state, alertness, TTC, AI status, action, speed và safe score.

Integration hiện tại: Fleet Dashboard và AI Copilot đã implemented cho demo. Connected-Car / Driver HMI đã verified bằng đường `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`. Đây là đường truyền thực tế phù hợp với giới hạn hiện tại của CarSky AAOS runtime. Custom DMS Android CarProperty IDs không được claim là production-ready trong bản báo cáo này. [E-24]
```

---

# 3. Mục `3.1.5 Fleet Dashboard and AI Copilot Status`

## Cần thay gì

Mục này hiện ghi chung chung và còn nói `Coaching Report và Fleet AI Copilot prototype/đang hoàn thiện`. Với trạng thái hiện tại nên thay bằng block rõ feature + guardrail.

## Copy-Paste Thay Vào

```text
3.1.5 Fleet Dashboard and AI Copilot Status

Fleet Dashboard hiện đã có các thành phần phục vụ demo:

- Live event và snapshot.
- Multi-trip registry.
- Saved trip loading từ JSON/local AI.
- Fleet Map / list.
- Trip Detail.
- Vehicle Live View / synchronized camera frame area.
- Risk Score, Ranking Score và Trip Safety Risk.
- Driver Ranking và Ranking Analysis.
- Performance Insights.
- Event log và trip-level evidence.
- Fleet Safety Executive Report.
- Safety Detail Report.
- Safety Overview Report.
- Maintenance Detail Report.
- Maintenance Overview Report.
- Word/DOC report export.
- Fleet AI Copilot drawer.

Dashboard không tạo lại canonical metric ở frontend. Các số liệu như Ranking Score, Risk Score, TTC/headway, behavior flags, harsh event, near miss, event log và maintenance triage lấy từ JSON/local AI hoặc Backend normalized data.

AI Copilot được dùng làm explanation layer. Report render JSON/local AI baseline trước để đảm bảo UX không bị chặn. Bedrock chỉ được gọi lazy khi user mở report hoặc yêu cầu AI insight. Nếu Bedrock trả payload hợp lệ, UI cập nhật insight và hiển thị trạng thái validated; nếu timeout/token lỗi/payload sai, UI giữ local report và không hiển thị insight giả.

Trạng thái phù hợp để ghi: Fleet Dashboard IMPLEMENTED for demo; AI Copilot IMPLEMENTED WITH GRACEFUL FALLBACK; production factual audit, RBAC, long-run reliability và governance vẫn là backlog.
```

---

# 4. Mục `4.3 Phạm vi MVP dự thi`

## Cần thay gì

Thay danh sách bullet hiện tại để thêm đúng report 4 loại, DOC export và speed-mux HMI.

## Copy-Paste Thay Vào

```text
4.3 Phạm vi MVP dự thi

- Submission pipeline: đọc dataset, sinh đúng CSV 5 cột và chạy evaluator.
- Product demo pipeline: AI/replay -> DecisionEvent -> Backend -> Fleet Dashboard -> CarSky/HMI.
- Fleet operations: live snapshot, trip detail, event log, ranking, ranking analysis, performance insights và coaching/safety review priority.
- Automated reporting: Safety Detail, Safety Overview, Maintenance Detail, Maintenance Overview và Driver Ranking Report.
- Export: Word/DOC export cho report đầy đủ; PDF không nằm trong final demo scope vì browser PDF rendering có thể lỗi style hoặc xuất trang trắng.
- AI Copilot: truy vấn ngôn ngữ tự nhiên trên context đã tổng hợp; không thay core risk engine và không tạo canonical metrics.
- Bedrock fallback: JSON/local AI render trước; Bedrock lazy-call và chỉ replace khi response validated.
- Connected-Car HMI: Backend publish DMS values qua CarSky; Android HMI nhận bằng `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux` và decode trên APK V2.2.
```

---

# 5. Mục `5.1 Ranh giới trách nhiệm`

## Cần thay gì

Thay bảng trách nhiệm hiện tại hoặc thêm các dòng cụ thể hơn cho `Frontend/HMI`, `AI Copilot`, `CarSky/HMI Bridge`.

## Copy-Paste Thay Vào

```text
5.1 Ranh giới trách nhiệm

Thành phần
Sở hữu quyết định
Không được làm

AI Challenge 1/2/3
Prediction theo contract từng challenge
Tự đổi schema nộp bài hoặc dùng UI value thay prediction

Decision Engine
Alert type, severity, evidence, action, lifecycle, audience
Ghi đè CSV submission hoặc tạo event thiếu evidence

Backend
Validate, deduplicate, recent state, broadcast, adapter, CarSky publisher queue
Tự tính lại risk để “làm đẹp” dashboard hoặc bịa signal không có trong AI/local telemetry

Fleet Dashboard
Trình bày trạng thái, evidence, ranking, report và action workflow
Tự bịa trip, score, event count hoặc response AI

AI Copilot
Tóm tắt/diễn giải context được cấp; tạo validated insight khi provider phản hồi hợp lệ
Trở thành nguồn số liệu gốc hoặc thay quyết định safety/ranking/maintenance

CarSky / HMI Bridge
Chuyển signal từ KUKSA sang VHAL transport đã thống nhất
Claim custom DMS CarProperty production-ready nếu runtime chưa expose ổn định

Android HMI APK
Đọc Android CarPropertyManager và render driver-facing state
Gọi trực tiếp Bedrock hoặc tự suy diễn risk/score ngoài payload đã nhận
```

---

# 6. Mục `5.2 Contract chuẩn`

## Cần thêm gì

Thêm đoạn này cuối mục `5.2`.

## Copy-Paste Thêm Vào

```text
Với Fleet Dashboard, saved trip JSON là completed trip context. Legacy JSON có thể chứa `Infinity` cho no-collision TTC; server/frontend phải normalize thành JSON hợp lệ nhưng vẫn giữ semantics là không có TTC nguy hiểm tức thời, không chuyển thành risk bằng 0 một cách sai nghĩa.

Với AI Copilot, canonical metrics luôn đến từ JSON/local AI hoặc Backend normalized data. Bedrock chỉ được dùng để diễn giải report context. Response Bedrock phải được validate theo report type, trip/report signature và không được thay đổi score/risk/event count canonical.

Với Android HMI, contract final demo dùng `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`. Custom DMS CarProperty IDs được xem là explored path, không phải primary runtime path trong bản demo hiện tại.
```

---

# 7. Mục `6. Hai nhánh vận hành và chiến lược demo`

## Cần thay gì

Thay bảng của mục 6 bằng bảng dưới.

## Copy-Paste Thay Vào

```text
6. HAI NHÁNH VẬN HÀNH VÀ CHIẾN LƯỢC DEMO

Nhánh
Input
Output
Tiêu chí thành công

Submission
Dataset BTC theo trip/frame
CSV 5 cột cho scored trips
Schema đúng, evaluator chạy, artifact khóa

Dataset-fleet demo
Road/cabin/telemetry từ dataset hoặc saved trip JSON
Dashboard multi-trip, event history, ranking, insights, reports
Không hard-code trip; truy vết event/frame/timestamp; local JSON giữ canonical metrics

Hybrid-live demo
Road/telemetry BTC + webcam driver
DMS live + TTC/risk + Backend/FE
Clock đúng, profile tùy chọn, fallback rõ

AI Copilot report demo
JSON/local AI report context + optional Bedrock response
Validated insight hoặc local baseline nếu Bedrock lỗi
Lazy-call đúng report đang xem; không mock insight; không đổi canonical metrics

Connected-car demo
DecisionEvent hoặc live telemetry snapshot có audience driver_display
CarSky signals, KUKSA, HMI Bridge, VHAL speed-mux, Android HMI
Cùng severity/reason/action; `Vehicle.Speed` mux `41.xxx-50.xxx` được APK decode; boundary status trung thực
```

---

# 8. Mục `6.1 Storyline 7-10 phút`

## Cần thay gì

Thay danh sách 7 bước hiện tại bằng bản dưới.

## Copy-Paste Thay Vào

```text
6.1 Storyline 7-10 phút

1. Chứng minh dữ liệu đầu vào và output của ba challenge trên cùng frame.
2. Sinh CSV chuẩn BTC và mở evaluator/log thay vì chỉ trình chiếu UI.
3. Đưa DecisionEvent qua Backend; đối chiếu event_id tại API và Dashboard.
4. Mở Trip Detail/Live View để chỉ ra evidence, lifecycle, driver state, TTC/headway và risk timeline.
5. Mở Driver Ranking / Ranking Analysis để giải thích công thức xếp hạng, penalty breakdown và lý do thứ bậc.
6. Mở Fleet Safety Executive Report hoặc Maintenance Report để chứng minh JSON/local AI render trước, Bedrock chỉ bổ sung validated insight khi có.
7. Chứng minh CarSky Signal Watch/Bridge và Android HMI APK: `Vehicle.Speed` mux thay đổi, bridge forward, APK decode thành risk/severity/TTC/action/speed/safe score.
8. Kết thúc bằng KPI, evidence gap, deployment-dependent limitations và kế hoạch khóa artifact.
```

---

# 9. Mục `12.1 Năng lực hiện có`

## Cần thêm gì

Thêm vào cuối mục `12.1`.

## Copy-Paste Thêm Vào

```text
Backend hiện có CarSky publisher theo mô hình non-blocking single-worker queue. Telemetry update có thể drop queued telemetry cũ để giảm lag, trong khi transition event được ưu tiên để không mất lifecycle quan trọng. Đây là cơ chế phù hợp demo realtime nhưng chưa thay thế durable outbox/acknowledgement production.

Backend CarSky mapper hiện dùng `vehicle-speed-mux`: các DMS logical values được publish qua `Vehicle.Speed` với decimal mux groups `41.xxx` đến `50.xxx`. APK V2.2 decode contract này ở Android side.
```

---

# 10. Mục `12.3.3 Latency Evidence`

## Cần thay gì

Giữ ý chính nhưng chỉnh wording rõ hơn. Copy thay đoạn mô tả latency.

## Copy-Paste Thay Vào

```text
Core safety-event delivery chưa có benchmark end-to-end đóng băng. Bedrock latency thuộc Copilot generation (§14), không đại diện cho AI → Decision Engine → Backend → Dashboard/CarSky safety-event latency. [E-14][E-20]

Core latency phải đo riêng theo các boundary: input → AI output; AI output → Decision Engine; Decision Engine → Backend; Backend → Dashboard; Backend → CarSky/HMI. Khi chưa có artifact đo lặp lại, trạng thái là PENDING. [E-09][E-14]
```

---

# 11. Mục `12.3.4 Backpressure Evidence`

## Copy-Paste Thay Vào

```text
WebSocket/recent-state path chưa có durable consumer acknowledgement và backpressure policy hoàn chỉnh. CarSky publisher đã có bounded queue với telemetry-drop để giảm lag và transition-priority để bảo vệ event lifecycle; claim phải phản ánh đúng giới hạn này. [I6][E-14]

`deque(maxlen=1000)` chỉ giữ recent-state trong RAM và mất qua restart. CarSky queue có trạng thái degraded khi timeout nhưng chưa durable và chưa chứng minh per-event acknowledgement end-to-end. [I6][E-14]
```

---

# 12. Mục `12.3.6 Observability Evidence`

## Copy-Paste Thay Vào

```text
Observability hiện tại: FE server ghi Copilot audit log vào `copilot_audit_logs.json`; FastAPI Backend log event/runtime status ra console; CarSky publisher có delivery_status và last_error để phân biệt ready/degraded. Android HMI có logcat tag `DMS_HMI` cho CarProperty callback, polling fallback và mux decode.

Khoảng trống còn lại: chưa có Correlation ID xuyên suốt từ AI Engine → Decision Engine → Backend → WebSocket → Dashboard → CarSky → HMI cho cùng một event trong mọi flow. Đây là backlog cần bổ sung trước production/pilot.
```

---

# 13. Mục `13. FLEET DASHBOARD - TỪ FEATURE ĐẾN QUYẾT ĐỊNH`

## Cần thay gì

Nên thay toàn bộ mục 13 bằng block dưới để bám đúng trạng thái Dashboard hiện tại.

## Copy-Paste Thay Vào

```text
13. FLEET DASHBOARD - TỪ FEATURE ĐẾN QUYẾT ĐỊNH

Fleet Dashboard là lớp vận hành cho Fleet Manager. Dashboard nhận dữ liệu từ Backend qua REST/WebSocket và từ saved trip JSON đã được local AI tính toán trước.

Dashboard không tự bịa metric và không tính lại canonical AI output ở frontend. Các số liệu chính như Ranking Score, Risk Score, TTC/headway, behavior flags, event log, harsh event, near miss và maintenance triage được lấy từ JSON/local AI hoặc Backend normalized data.

Hình 4. Phần đầu Fleet Safety Executive Report: score, ranking, risk level và hành động xem chi tiết. [S1]

13.1 Các quyết định được hỗ trợ

Màn hình/Năng lực
Câu hỏi quản lý
Hành động
Giá trị cần đo

Fleet Map / list
Trip nào đang có rủi ro cao?
Mở live view, xem trip detail, ưu tiên safety review
Time-to-identify critical trip

Vehicle Live View
Nguy cơ do tài xế, đường hay traffic context?
Cảnh báo, yêu cầu nghỉ, theo dõi, hoặc review frame
Time-to-acknowledge; false escalation

Trip Detail
Sự kiện xảy ra khi nào và bằng chứng gì?
Audit, coaching, điều tra, review frame/timestamp
Time-to-review; evidence completeness

Driver Ranking
Trip/driver nào cần review trước?
Lập lịch coaching/review và ghi nhận benchmark tương đối
Coaching prioritization precision

Ranking Analysis
Vì sao trip đứng thứ bậc này?
Audit công thức, penalty breakdown, trace về frame/event
Traceability success

Performance Insights
Yếu tố rủi ro nào nổi bật trong trip/fleet?
Điều chỉnh policy/route/shift
Repeat-event rate; exposure normalized

Copilot Reports
Tình hình safety/maintenance tổng quan và chi tiết là gì?
Xuất report, phân công review, theo dõi action
Report lead time; action closure

13.2 Giá trị không nằm ở số lượng widget

Dashboard phải gắn mỗi card với quyết định vận hành: definition, data source, timestamp, quality status, threshold policy, owner và next action. Số lượng chart/widget không tự tạo business value.

Ranking trong Dashboard dùng canonical Ranking Score từ JSON/local AI risk và behavior fields. Average Risk được hiển thị để audit mức độ rủi ro trung bình nhưng không quyết định vị trí xếp hạng.

Saved trips trong `SE/FE/src/data/saved_trips` là completed trip context để test và demo khi live runtime không chạy. Legacy JSON có `Infinity` cho TTC được normalize thành JSON hợp lệ nhưng không làm mất semantics “không có TTC nguy hiểm tức thời”.

13.3 Nguyên tắc thiết kế cho môi trường vận hành

- Severity không chỉ dựa vào màu; luôn kèm nhãn chữ, icon và recommended action.
- Mọi score đều mở được audit trail về event/frame/timestamp và formula version.
- Trạng thái camera/connection/data coverage phải hiển thị để tránh hiểu dữ liệu thiếu là an toàn.
- Danh sách critical ưu tiên theo urgency, exposure và ranking score, không chỉ theo số event thô.
- Intervention cần owner, confirmation, timestamp, outcome và khả năng hủy/đóng.
- Report overview phải phân biệt rõ relative rank và review priority.
- Nếu Bedrock chưa trả về hợp lệ, UI giữ JSON/local AI baseline và không hiển thị insight giả.

13.4 Kiểm thử trải nghiệm cần bổ sung

Bài test
KPI

Tìm trip critical trong fleet
Time-to-identify + error rate

Giải thích vì sao score bị trừ
Traceability success

Tạo và export fleet report DOC
Completion time + formatting defects

Xử lý camera/data offline
Correct degraded-state interpretation

Can thiệp và đóng event
Time-to-acknowledge/close

Bedrock timeout hoặc token hết hạn
Không mock insight; local report vẫn đọc được
```

---

# 14. Mục `14. AI COPILOT - VAI TRÒ, GIÁ TRỊ VÀ GUARDRAIL`

## Cần thay gì

Thêm đoạn này ngay sau đoạn mở đầu mục 14.

## Copy-Paste Thêm Vào

```text
AI Copilot là explanation layer, không phải nguồn tạo canonical metric.

Nguyên tắc hiện tại:

- Copilot nhận structured context: trip_id, metadata, risk summary, behavior flags, event log, ranking summary và maintenance context.
- Copilot không tạo Safety Score, Ranking Score, Risk Score, TTC, event count hoặc maintenance KPI mới.
- JSON/local AI là baseline deterministic.
- Bedrock chỉ được gọi lazy khi user mở report hoặc yêu cầu AI insight.
- Nếu Bedrock trả payload hợp lệ, UI cập nhật insight và hiển thị trạng thái validated.
- Nếu Bedrock timeout, lỗi token, lỗi provider hoặc payload sai format, UI giữ JSON/local AI report và không hiển thị insight giả.

Bedrock configuration được đọc từ `SE/BE/.env`, không lấy từ `SE/FE/.env.local`. Sau khi thay token trong `SE/BE/.env`, cần restart FE server để Express server đọc lại env mới.
```

---

# 15. Mục `14.3.4 Kịch Bản Dự Phòng & Quản Lý Timeout`

## Cần thay gì

Thay toàn bộ mục `14.3.4` bằng block này. Mục hiện tại có bảng loading chi tiết, nhưng cần sửa wording cho đúng: loading không được hiểu là insight thật.

## Copy-Paste Thay Vào

```text
14.3.4 Kịch Bản Dự Phòng & Quản Lý Timeout (Fallback Scenarios)

Hệ thống dùng Graceful AI Fallback để đảm bảo UI không bịa số liệu khi Bedrock chậm, lỗi token hoặc trả payload không hợp lệ.

Layer 1: JSON / Local AI Telemetry Baseline

Đây là tầng dữ liệu gốc.

Nguồn dữ liệu:

- Saved trip JSON.
- Local AI telemetry.
- Ranking Score.
- Risk Score.
- TTC / headway.
- Behavior flags.
- Event log.
- Maintenance triage rule-based.

Vai trò:

- Render báo cáo ngay lập tức.
- Không phụ thuộc Bedrock.
- Không bịa số liệu.
- Là dữ liệu canonical để audit.

Layer 2: Bedrock Lazy Request

Bedrock không được gọi ồ ạt.

Nguyên tắc:

- Chỉ gọi khi user mở report hoặc yêu cầu AI insight.
- Safety Detail chỉ gửi trip đang xem.
- Maintenance Detail chỉ gửi trip đang xem.
- Safety Overview chỉ gửi số liệu tổng hợp fleet.
- Maintenance Overview chỉ gửi số liệu tổng hợp fleet.
- Nếu user rời report, request cũ không được tiếp tục update UI context mới.

Mục tiêu:

- Giảm nghẽn Bedrock.
- Tăng tốc UX.
- Ưu tiên màn hình user đang thật sự xem.

Layer 3: Timeout / Abort Guard

Nếu Bedrock phản hồi chậm hoặc user rời trang:

- Abort request đang chờ nếu runtime cho phép.
- Không tiếp tục update UI của trang đã rời.
- Không làm nghẽn request khác.
- Giữ local report đang hiển thị.

Layer 4: Payload Validation

Bedrock chỉ được dùng nếu payload hợp lệ.

Điều kiện validation:

- `ai_status === validated`.
- Đúng report type, không lẫn safety và maintenance.
- Đúng trip/report đang yêu cầu.
- Không bịa event khi metric bằng 0.
- Không thay đổi score/risk/event count canonical.
- Không thay thế JSON/local AI bằng nội dung chung chung.
- Tuân thủ prompt contract của từng report type.

Nếu fail validation:

- Không apply Bedrock.
- Giữ JSON/local AI.
- UI hiển thị trạng thái chờ/fallback hợp lệ.
- Không hiển thị insight giả.

Layer 5: Validated Insight Cache / Restore

Khi Bedrock trả về hợp lệ:

- Lưu insight theo inputSignature.
- Hiển thị trạng thái màu xanh: "AI Copilot đã trả về insight hợp lệ từ Bedrock."
- Giữ kết quả Bedrock đã xác thực.
- Không cho local fallback ghi đè ngược nếu input không đổi.

Trạng thái UI:

- Khi đang chờ: "Đang chờ Bedrock phản hồi hợp lệ."
- Khi hợp lệ: "AI Copilot đã trả về insight hợp lệ từ Bedrock."
- Khi lỗi/timeout: giữ JSON/local AI baseline, không hiển thị AI insight thay thế.
```

---

# 16. Mục `15. BÁO CÁO TỰ ĐỘNG VÀ KHẢ NĂNG EXPORT`

## Cần thay gì

Thay mục 15.3 và sửa các chỗ nhắc PDF.

## Copy-Paste Thay Mục `15.3 Export và hồ sơ kiểm toán`

```text
15.3 Export và hồ sơ kiểm toán

Mỗi bản export cần report_id, generation time, date range, data snapshot ID và model/config versions.

Nêu rõ dữ liệu demo, dữ liệu practice hay dữ liệu pilot; không trộn các môi trường.

Có phần “Data quality and limitations” tự động khi thiếu frame, camera offline hoặc AI confidence thấp.

Report export hiện hỗ trợ Word-compatible DOC export. DOC export chứa:

- Report title và report type.
- Date range theo ngày hiện tại khi export.
- Fleet/trip summary metrics.
- Trip cards hoặc selected trip detail.
- Safety KPI context hoặc maintenance KPI context.
- Event evidence / statistical evaluation.
- JSON/local AI baseline evaluation.
- Validated Bedrock insight nếu đã có phản hồi hợp lệ.

PDF export không nằm trong final demo scope vì browser PDF rendering có thể mất style hoặc xuất trang trắng trong một số môi trường. Nhóm ưu tiên DOC export để đảm bảo report đầy đủ nội dung, có thể mở bằng Microsoft Word hoặc công cụ tương thích, sau đó người dùng có thể export PDF từ Word nếu cần.

Nên hỗ trợ export machine-readable CSV/JSON cho audit trong roadmap sau demo.
```

---

# 17. Mục `16. CONNECTED-CAR, CARSKY VÀ DRIVER HMI`

## Cần thay gì

Thay toàn bộ mục 16 bằng block dưới. Đây là phần quan trọng nhất.

## Copy-Paste Thay Vào

```text
16. CONNECTED-CAR, CARSKY VÀ DRIVER HMI

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

Boundary
Current Status
Meaning

AI -> Decision Engine
IMPLEMENTED
Local AI/model output is converted into decision events and live telemetry snapshots.

Decision Engine -> Backend
IMPLEMENTED
Backend receives normalized alert/snapshot data through the project API contract and tests.

Backend -> Fleet Dashboard
IMPLEMENTED
Dashboard receives live state through REST/WebSocket and renders map, trip detail, ranking, insights and reports.

Backend -> CarSky REST Signal API
VERIFIED
Backend can publish DMS multiplex values into the CarSky signal node; Signal Watch/API response confirms updates.

CarSky REST -> KUKSA / DMS Signal Broker
VERIFIED
CarSky signal node stores the published `Vehicle.Speed` values and exposes them to the bridge.

KUKSA / Signal Broker -> DMS HMI Bridge
VERIFIED
HMI Bridge subscribes to `Vehicle.Speed` and logs speed-mux forwarding when Backend publishes telemetry.

DMS HMI Bridge -> Android VHAL
VERIFIED FOR DEMO WITH SPEED-MUX
Bridge forwards data through `PERF_VEHICLE_SPEED` (`0x11600207`) because the AAOS image reliably exposes this property. Custom DMS CarProperty IDs are not relied on as final path.

Android VHAL -> Android CarPropertyManager
VERIFIED WITH DEPLOYMENT HOTFIX
APK receives updates from `CarPropertyManager` using callback plus polling fallback. Runtime depends on the current CarSky/AAOS deployment and VHAL relay/route configuration.

Android CarPropertyManager -> DMS Android HMI APK
VERIFIED FOR DEMO
APK V2.2 decodes speed-mux groups and updates the HMI UI for risk, severity, driver state, alertness, TTC, AI status, action, speed and safe score.

Speed-mux contract:

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

Lý do dùng speed-mux: khi kiểm tra Android CarService trong CarSky AAOS runtime, property chuẩn `PERF_VEHICLE_SPEED` được expose ổn định, trong khi các custom DMS CarProperty như Risk, AIStatus, Alertness, DriverState hoặc TTC không xuất hiện ổn định trong `CarPropertyService`.

Vì vậy, để bảo đảm demo end-to-end chạy được, nhóm sử dụng `Vehicle.Speed / PERF_VEHICLE_SPEED` làm transport đã verified, sau đó APK V2.2 decode lại thành state HMI.

APK đọc `PERF_VEHICLE_SPEED` bằng hai cơ chế:

- Callback: nhận event từ `CarPropertyManager`.
- Polling fallback: đọc lại property định kỳ để tránh trường hợp callback không ổn định trong runtime demo.

APK V2.2 render driver-facing UI bằng tiếng Anh:

- AI status.
- Driver state.
- Alertness.
- TTC.
- Risk Score.
- Safe Score.
- Real speed km/h.
- Recommended action.
- ECU reaction.
- Voice alert state.

Khi không có data, APK hiển thị waiting/offline state thay vì hiển thị số liệu giả.
```

---

# 18. Mục `16.1 Giá trị business của connected-car delivery`

## Cần thay gì

Thay đoạn hiện tại đang ghi Android pending bằng đoạn này.

## Copy-Paste Thay Vào

```text
16.1 Giá trị business của connected-car delivery

Connected-Car delivery giúp biến risk intelligence thành cảnh báo có thể nhìn thấy trực tiếp trên driver-facing HMI. Giá trị business không nằm ở việc điều khiển xe, mà nằm ở advisory warning, shared situational awareness và khả năng chứng minh cùng một severity/reason/action đi từ Backend đến Fleet Dashboard và HMI.

Trạng thái hiện tại: Backend/REST -> CarSky REST Signal API -> KUKSA / DMS Signal Broker -> HMI Bridge đã VERIFIED. Android HMI đã VERIFIED FOR DEMO bằng `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`, với APK V2.2 đọc `CarPropertyManager` bằng callback + polling fallback. Runtime vẫn deployment-dependent vì deploy CarSky mới có thể cần init lại route/relay/hotfix.

Đây là advisory delivery, không phải vehicle actuation. Report không claim hệ thống tự phanh, tự điều khiển hoặc thay thế driver responsibility. [E-17][E-24]
```

---

# 19. Mục `19. TRẠNG THÁI TRIỂN KHAI VÀ MA TRẬN BẰNG CHỨNG`

## Cần thay gì

Trong bảng mục 19, thay các dòng sau.

## Copy-Paste Thay Các Dòng Liên Quan

```text
Fleet Dashboard
IMPLEMENTED
Build, live views, saved trips, ranking, ranking analysis, insights, safety/maintenance reports và Word/DOC export
Long-run reliability, accessibility, auth, formal usability baseline

AI Copilot/report
IMPLEMENTED WITH GRACEFUL FALLBACK / PRODUCTION AUDIT PENDING
JSON/local AI baseline; Bedrock lazy-call; validated insight; fallback không mock insight [E-19][E-20]
Golden-set factual audit, RBAC, cost governance, long-run stability

CarSky/KUKSA/Bridge
VERIFIED
Backend/REST -> CarSky Signal API -> KUKSA -> HMI Bridge; Signal Watch/API response và bridge log [E-24]
Repeatable package, deployment script và long-run test

Android HMI realtime
VERIFIED FOR DEMO / DEPLOYMENT-DEPENDENT
APK V2.2 nhận `PERF_VEHICLE_SPEED` speed-mux qua Android CarPropertyManager callback + polling fallback [E-24]
Route/relay/hotfix automation, same-event trace package, custom property decision

Custom DMS CarProperty
NOT FINAL PATH
Custom property path đã khảo sát nhưng không dùng làm primary runtime path
Nếu BTC/OEM xác nhận hỗ trợ custom vendor properties, có thể đưa vào roadmap production
```

---

# 20. Mục `22. MA TRẬN CẠNH TRANH VÀ KHOẢNG TRẮNG`

## Cần thay gì

Trong dòng `Connected-car HMI`, thay status cũ.

## Copy-Paste Thay Dòng Connected-Car HMI

```text
Connected-car HMI
Hardware ecosystem riêng
In-cab alert riêng
CarSky/KUKSA/Bridge verified; Android HMI verified for demo via `PERF_VEHICLE_SPEED` speed-mux; deployment-dependent runtime route [E-24]
```

## Copy-Paste Thay Mục `22.1`

```text
22.1 Khoảng trắng hợp lý để định vị

Định vị đề xuất: explainable, event-centric reference architecture cho Driver & Fleet Risk Intelligence, kết hợp stereo TTC, DMS, telemetry, Fleet Dashboard, AI Copilot report và connected-car HMI trong một proof chain truy vết được.

Khác biệt nằm ở integration/transparency: cùng một AI/local telemetry context có thể đi tới Dashboard, report và Driver HMI. Hệ thống không claim vượt vendor thương mại về accuracy, scale, durability hoặc production certification. [E-02][E-03][E-04][E-22][E-24]
```

---

# 21. Mục `29. RỦI RO DỰ ÁN VÀ KẾ HOẠCH GIẢM THIỂU`

## Cần thay gì

Thay dòng rủi ro `VHAL HMI không hoàn tất` và `Copilot phụ thuộc key/network`.

## Copy-Paste Thay Các Dòng Liên Quan

```text
VHAL/HMI deployment route mất sau khi deploy mới
Trung/Cao
APK waiting/offline hoặc Signal Watch có data nhưng HMI không đổi
Giữ final path là `PERF_VEHICLE_SPEED` speed-mux; tự động hóa init route/relay/hotfix; lưu checklist logcat/bridge log cho same-event trace
Embedded Lead

Custom DMS CarProperty không expose ổn định
Trung/Trung-Cao
CarPropertyService không thấy property custom hoặc permission bị chặn
Không claim custom property production-ready; dùng `Vehicle.Speed / PERF_VEHICLE_SPEED` speed-mux làm verified demo path; đưa custom properties vào roadmap nếu BTC/OEM xác nhận
Embedded Lead

Copilot phụ thuộc key/network
Trung/Trung
Timeout/401/429 hoặc Bedrock payload không hợp lệ
Graceful AI Fallback: JSON/local AI baseline, lazy request, timeout/abort, payload validation, validated insight cache; không hiển thị insight giả
FE/BE
```

---

# 22. Mục `30. ROADMAP ĐẾN CODE FREEZE VÀ SAU HACKATHON`

## Cần thay gì

Thay các dòng P0 liên quan rehearsal/report/HMI.

## Copy-Paste Thay Các Dòng Liên Quan

```text
P0
Rehearsal end-to-end
AI -> Decision Engine -> Backend -> Fleet Dashboard -> CarSky -> Android HMI có cùng event/severity/action; video backup; nếu CarSky runtime đổi, chạy lại init route/relay/hotfix

P0
Report export freeze
Safety Detail, Safety Overview, Maintenance Detail, Maintenance Overview và Driver Ranking Report export được Word/DOC đầy đủ; PDF không nằm trong final demo scope

P0
Bedrock fallback validation
Token từ `SE/BE/.env`; report render JSON/local AI trước; Bedrock lazy-call; validated insight không bị fallback ghi đè; timeout không làm UI hiển thị mock insight

P0
VHAL speed-mux runtime correlation
Capture same-event runtime trace: Backend publish mux -> CarSky Signal Watch `Vehicle.Speed` -> HMI Bridge log -> Android logcat `DMS_HMI` -> APK UI update
```

---

# 23. Mục `32.1 Narrative đề xuất`

## Cần thay gì

Thay danh sách 8 ý bằng bản dưới.

## Copy-Paste Thay Vào

```text
32.1 Narrative đề xuất

1. Problem: rủi ro hình thành từ nhiều tín hiệu nhưng fleet thường nhìn rời rạc.
2. Insight: cảnh báo đơn lẻ chưa đủ; cần risk intelligence có context, evidence và action.
3. Solution: C1/C2/C3 -> DecisionEvent -> Backend -> Fleet Dashboard / AI Copilot Report / Driver HMI. Product Context Fusion diễn ra sau challenge outputs và không sửa scored CSV. [E-01][E-03][E-04]
4. Proof: chạy output, event_id, evidence, report Word/DOC export và CarSky/HMI boundary thật.
5. Fleet value: giảm thời gian nhận biết/đánh giá/coaching; ưu tiên nguồn lực; tạo audit trail.
6. Driver value: HMI hiển thị advisory warning với risk, severity, TTC, action, speed và safe score qua Android CarPropertyManager.
7. Differentiation: stereo TTC + DMS + event lifecycle + Fleet Dashboard + AI Copilot + connected-car HMI trong kiến trúc mở, traceable.
8. Honesty: nêu C1 frozen metric, C2 current-model provenance, Bedrock fallback, DOC export, HMI verified for demo/deployment-dependent, CARLA manifest-required, edge benchmark pending và ROI chưa field-validated. [E-09][E-10][E-11][E-19][E-24]
9. Ask: hỗ trợ pilot/hardware/data/validation để chuyển prototype thành field evidence.
```

---

# 24. Mục `32.2 Câu hỏi hội đồng có thể đặt`

## Cần thay gì

Thay câu trả lời cho 3 câu: AI Copilot, export, HMI end-to-end. Có thể thêm câu mới về speed-mux.

## Copy-Paste Thay/Thêm Vào

```text
AI Copilot có hallucinate không?
Copilot không tạo score và không thay canonical metrics. Report render JSON/local AI baseline trước; Bedrock chỉ được apply khi payload validated đúng report type/trip context. Nếu Bedrock lỗi hoặc timeout, UI giữ local report và không hiển thị insight giả. Golden-set factual audit vẫn là backlog trước production.

Export report có ổn không?
Final demo scope dùng Word/DOC export vì browser PDF rendering có thể mất style hoặc xuất trang trắng. DOC export chứa summary metrics, trip cards/detail, KPI context, event evidence, JSON/local AI baseline và validated Bedrock insight nếu có.

HMI đã end-to-end chưa?
Backend -> CarSky Signal API -> KUKSA -> HMI Bridge đã verified. Android HMI đã verified for demo bằng `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`: APK V2.2 đọc `CarPropertyManager` bằng callback + polling fallback và decode risk/severity/TTC/action/speed/safe score. Runtime vẫn deployment-dependent vì deploy mới có thể cần init lại route/relay/hotfix. [E-24]

Vì sao dùng `Vehicle.Speed` để truyền nhiều giá trị?
Trong CarSky AAOS runtime hiện tại, `PERF_VEHICLE_SPEED` được expose ổn định qua Android `CarPropertyService`, còn custom DMS CarProperty IDs chưa expose ổn định. Vì vậy nhóm dùng speed-mux làm verified demo transport, không claim đây là thiết kế production cuối cùng.
```

---

# 25. Mục `33. KẾT LUẬN`

## Cần thay gì

Thay 2 đoạn kết luận hiện tại bằng bản dưới.

## Copy-Paste Thay Vào

```text
33. KẾT LUẬN

FPTU DMS Vision mở rộng submission CSV thành chuỗi frame prediction -> risk intelligence có lifecycle, evidence, Fleet Dashboard, AI Copilot report và connected-car Driver HMI. Capability được trình bày theo verified boundary; các phép đo/pilot còn thiếu không được suy diễn. [E-01][E-03][E-04]

Khác biệt chính của dự án là integration và explainability. Dashboard dùng JSON/local AI làm baseline deterministic, hỗ trợ trip detail, ranking, ranking analysis, insights, safety/maintenance reports và Word/DOC export. AI Copilot dùng Bedrock như explanation layer với graceful fallback, không tạo canonical metrics và không hiển thị insight giả khi provider lỗi.

Connected-Car / Android HMI đã verified cho demo qua CarSky bằng `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`. Đây là phương án phù hợp với giới hạn runtime hiện tại của CarSky AAOS, nơi property chuẩn speed expose ổn định hơn custom DMS CarProperty. APK V2.2 decode mux values và hiển thị driver-facing alert bằng tiếng Anh.

Các giới hạn còn lại chủ yếu nằm ở production/pilot evidence: C2 current-model provenance, long-term reliability, CARLA full manifest, Bedrock factual audit/governance, route/relay automation cho CarSky deployment mới, privacy governance và field ROI. Những giới hạn này đã có fallback hoặc boundary statement minh bạch trước khi commercialization. [E-11][E-14][E-19][E-24][E-27][E-34]
```

---

# 26. Mục `33.1.2 Hỗ trợ xử lý / xác nhận VHAL–CarProperty boundary`

## Cần thay gì

Thay toàn bộ mục này bằng block dưới.

## Copy-Paste Thay Vào

```text
33.1.2 Hỗ trợ xử lý / xác nhận VHAL–CarProperty boundary

Backend/REST -> CarSky Signal API -> KUKSA / DMS Signal Broker -> HMI Bridge: VERIFIED. Android HMI đã verified for demo qua `PERF_VEHICLE_SPEED` speed-mux với callback/polling fallback trên APK V2.2. Runtime vẫn deployment-dependent: nếu CarSky blueprint/pod được tạo lại, route/relay/hotfix có thể cần init lại. [I6][E-24]

Vấn đề cần xác nhận
Đầu ra hỗ trợ mong muốn

Custom vendor VHAL properties
Xác nhận Skycraft/AAOS có hỗ trợ custom vendor properties cho use case DMS hay không; nếu có, cung cấp cơ chế registration/configuration đúng.

KUKSA/Bridge -> VHAL mapping
Xác nhận cách signal/value từ Bridge được publish vào VHAL và trở thành property mà `CarPropertyService` có thể expose cho APK.

Permission / application privilege
Xác nhận APK có cần privileged/system permission, platform signature hoặc allowlist property để subscribe DMS signals.

Runtime verification
Cung cấp hoặc xác nhận checklist/log tối thiểu để chứng minh property tồn tại, có giá trị thay đổi và được `CarPropertyManager` nhận đúng.

Fallback transport
Nếu custom VHAL không được hỗ trợ trong sandbox, xác nhận `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux` là transport thay thế được chấp nhận để chứng minh Connected-Car delivery một cách trung thực.

Đầu ra yêu cầu: integration path được xác nhận hoặc boundary statement chính thức, phân biệt rõ verified/deployment-dependent/pending và không dùng mock thay runtime evidence.
```

---

# 27. Checklist Cuối Cùng Trước Khi Nộp

```text
[ ] Mục Executive Summary: đổi Android HMI từ PARTIAL sang VERIFIED FOR DEMO / deployment-dependent nếu đã có APK update thật.
[ ] Mục 3.1.4: thay bảng Integration Baseline.
[ ] Mục 3.1.5: cập nhật Fleet Dashboard + AI Copilot status.
[ ] Mục 4.3: thêm Word/DOC export, lazy Bedrock, speed-mux HMI.
[ ] Mục 5.1: thêm responsibility rõ cho Fleet Dashboard, AI Copilot, CarSky/HMI Bridge, Android HMI.
[ ] Mục 5.2: thêm contract saved JSON, Bedrock validation, HMI speed-mux.
[ ] Mục 6 và 6.1: sửa demo strategy/storyline.
[ ] Mục 12.1, 12.3.3, 12.3.4, 12.3.6: sửa reliability/latency/backpressure/observability.
[ ] Mục 13: thay Fleet Dashboard section.
[ ] Mục 14 và 14.3.4: thay AI Copilot fallback section.
[ ] Mục 15.3: đổi PDF thành Word/DOC export.
[ ] Mục 16 và 16.1: thay Connected-Car / CarSky / Driver HMI section.
[ ] Mục 19: sửa status matrix.
[ ] Mục 22: sửa Connected-car HMI positioning.
[ ] Mục 29: sửa risk table.
[ ] Mục 30: sửa roadmap P0.
[ ] Mục 32.1 và 32.2: sửa pitch + Q&A.
[ ] Mục 33 và 33.1.2: sửa conclusion + support ask.
[ ] Tìm toàn report các cụm `SE/FE/.env.local`, `PDF export`, `custom DMS CarProperty fully`, `Android live correlation pending`, `Vehicle.ADAS.FinalRiskScore path chính` và thay theo guide này.
```

