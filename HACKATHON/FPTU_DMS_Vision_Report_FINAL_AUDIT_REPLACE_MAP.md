# Final Audit Replace Map Cho `FPTU_DMS_Vision_Report.md`

File này là bản audit sau khi đọc lại toàn bộ report đính kèm ngày 09/08/2026 và quét lại project hiện tại, tập trung vào:

- `Fleet Dashboard`
- `AI Copilot / Bedrock`
- `Saved trips / JSON local AI`
- `Android HMI APK`
- `VHAL`
- `CarSky / KUKSA / HMI Bridge`

Kết luận nhanh: report đã được sửa đúng rất nhiều phần, nhưng vẫn còn một số mục lệch với project thật hoặc còn câu cũ chưa thay hết. Dưới đây là **mục số nào cần thay**, **lý do**, và **block full để copy-paste**.

---

# 0. Những Mục Đã Ổn, Không Cần Thay Lớn

Các mục này nhìn chung đã khớp với project hiện tại:

- `3.1.4 Integration Baseline`: đã đúng hướng speed-mux, chỉ cần đồng bộ lại Executive Summary và Summary Table.
- `3.1.5 Fleet Dashboard and AI Copilot Status`: đã đúng.
- `4.3 Phạm vi MVP dự thi`: đã đúng.
- `5.1 Ranh giới trách nhiệm`: đã đúng.
- `5.2 Contract chuẩn`: đã đúng.
- `6 Hai nhánh vận hành và chiến lược demo`: đã đúng.
- `6.1 Storyline 7-10 phút`: đã đúng.
- `12.1 Năng lực hiện có`: đã đúng.
- `12.3.3`, `12.3.4`, `12.3.6`: đã đúng về hướng reliability.
- `13 Fleet Dashboard`: đã đúng logic chính.
- `16 Connected-Car, CarSky và Driver HMI`: nội dung chính đúng, nhưng cần thêm caveat về bridge script evidence.
- `19 Trạng thái triển khai`: đã đúng phần Dashboard/Copilot/CarSky/HMI.
- `22`, `29`, `30`, `32`, `33`: phần lớn đã đúng, nhưng còn vài dòng stale trong `30.1` và appendix.

---

# 1. Executive Summary / Trạng Thái Hiện Tại

## Lỗi Còn Lệch

Đầu report vẫn còn câu cũ:

```text
Backend/REST → KUKSA và KUKSA → HMI Bridge: VERIFIED. VHAL multiplex transport: IMPLEMENTED. Android VHAL → APK live correlation: PARTIAL / verification pending...
```

Câu này lệch với các mục sau trong chính report, vì mục `16` và `19` đã ghi Android HMI `VERIFIED FOR DEMO / DEPLOYMENT-DEPENDENT`.

## Thay Đoạn `Trạng thái hiện tại` Bằng Block Này

```text
Trạng thái hiện tại

AI Challenge 1/2/3, Decision Engine, FastAPI Backend và Fleet Dashboard có đường chạy demo; các claim định lượng trong báo cáo được gắn với Evidence ID tương ứng. [E-01][E-03][E-13][E-15][E-22]

Backend/REST -> CarSky REST Signal API -> KUKSA / DMS Signal Broker -> HMI Bridge đã VERIFIED qua Signal Watch/API response và bridge log. Android HMI đã VERIFIED FOR DEMO bằng đường `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`: APK V2.2 đọc Android `CarPropertyManager`, decode mux groups và render risk, severity, driver state, alertness, TTC, AI status, action, real speed và safe score. Trạng thái này vẫn là deployment-dependent vì CarSky runtime mới có thể cần init lại route/relay. [E-24]

AI Copilot, Driver Ranking Report và Fleet Safety Executive Report đã có giao diện/endpoint phục vụ demo và Word/DOC export. Bedrock latency chỉ áp dụng cho Copilot generation, không đại diện cho safety-event latency. JSON/local AI là baseline deterministic; Bedrock chỉ bổ sung validated insight khi phản hồi hợp lệ. Factual audit, cost/governance và long-term stability còn cần evidence. [E-19][E-20][E-21]

CARLA hiện được ghi nhận ở phạm vi synthetic C1 collector/configuration. Chưa có full-dataset manifest E-11, vì vậy số trip, retained frame và coverage không được công bố như actual; chỉ cập nhật khi có manifest đóng băng. [E-11][E-12]
```

---

# 2. Mục `3.1.11 Baseline Summary Table`

## Lỗi Còn Lệch

Mục này vẫn ghi:

```text
Fleet Dashboard: MVP implemented
Android realtime through VHAL: VHAL multiplex implemented; Android live correlation PARTIAL / verification pending
Coaching Report: Prototype/under development
```

Nên sửa cho đồng bộ với các mục đã cập nhật:

- Fleet Dashboard hiện nên là `IMPLEMENTED`.
- Android HMI là `VERIFIED FOR DEMO / DEPLOYMENT-DEPENDENT`.
- Coaching/report không còn ghi prototype chung chung; đổi thành safety/maintenance report implemented with fallback.

## Thay Toàn Bộ Bảng `3.1.11` Bằng Block Này

```text
3.1.11 Baseline Summary Table

Baseline area
Current status

C1 model evaluation
Practice result: C1 composite 65.5/100; Critical MAE 0.876 s; Danger F1 69.9% [E-01][E-13]

C2 model evaluation
Production candidate_013, model_version 4, legacy_59; current metrics require E-27

C3 evaluator
Có kết quả nhưng bị saturation; cần recalibration/final evaluation để làm quality baseline có ý nghĩa

Backend
Implemented demo; final frozen source 28/28 tests passed [E-15]; persistent store/outbox production vẫn là backlog

Frontend / Fleet Dashboard
IMPLEMENTED; map/list, trip detail, saved trips, ranking, ranking analysis, insights, safety/maintenance reports và Word/DOC export

Decision Engine
IMPLEMENTED

Fleet Dashboard
IMPLEMENTED FOR DEMO; chưa có formal usability baseline hoặc long-run reliability benchmark

AI Copilot / Bedrock
IMPLEMENTED WITH GRACEFUL FALLBACK; JSON/local AI baseline, Bedrock lazy-call, payload validation, validated insight cache; golden-set factual audit pending [E-19][E-20]

CarSky KUKSA integration
VERIFIED; Backend/REST -> CarSky Signal API -> KUKSA / DMS Signal Broker -> HMI Bridge [E-24]

Android realtime through VHAL
VERIFIED FOR DEMO / DEPLOYMENT-DEPENDENT; APK V2.2 nhận `PERF_VEHICLE_SPEED` speed-mux qua Android `CarPropertyManager` callback + polling fallback [E-24]

Report export
Word/DOC export implemented; PDF export is out of final demo scope

CARLA dataset extension
PENDING / MANIFEST REQUIRED; actual inventory must come from E-11 [E-11][E-12]

Long-duration runtime benchmark
PENDING JETSON LONG-RUN BENCHMARK
```

---

# 3. Mục `12.2 Reliability backlog`

## Lỗi Còn Lệch

Trong report vẫn có dòng:

```text
Độ trễ truyền dẫn từ AI Decision Engine đến Fleet Dashboard Consumer: p50 < 100ms, p95 < 350ms, p99 < 800ms...
```

Dòng này dễ bị hỏi vì mục `12.3.3` đã nói core safety-event delivery chưa có benchmark end-to-end đóng băng.

## Thay Dòng Latency Trong `12.2` Bằng Block Này

```text
Latency backlog

Core safety-event latency chưa có benchmark end-to-end đóng băng. Các số Bedrock p50/p95 trong mục 14 chỉ đại diện cho Copilot generation latency, không đại diện cho AI -> Decision Engine -> Backend -> Dashboard/CarSky safety-event latency.

Latency cần đo riêng theo boundary:

- Input -> AI output.
- AI output -> Decision Engine.
- Decision Engine -> Backend.
- Backend -> Fleet Dashboard.
- Backend -> CarSky/HMI.

Khi chưa có artifact đo lặp lại, trạng thái latency end-to-end là PENDING. [E-09][E-14][E-20]
```

---

# 4. Mục `13.4 Kiểm thử trải nghiệm cần bổ sung`

## Lỗi Nhỏ

Bảng vẫn ghi:

```text
Tìm xe critical trong fleet
```

Trong dự án hiện tại user đã yêu cầu tránh gọi là `xe/driver` nếu dữ liệu là trip/sample. Nên đổi thành `trip`.

## Thay Bảng `13.4` Bằng Block Này

```text
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

# 5. Mục `14.3.1 Response Latency`

## Lỗi Cần Chỉnh

Report đang ghi:

```text
Chỉ số được đo lường thực tế thông qua benchmark chạy trực tiếp trên AWS Bedrock.
```

Câu này hơi mạnh. Nên nói đây là `Copilot generation latency sample`, không phải benchmark production.

## Thay Câu Mở Đầu `14.3.1` Bằng Block Này

```text
14.3.1 Thời Gian Phản Hồi (Response Latency: p50 / p95)

Các số trong bảng này là Copilot generation latency sample khi gọi AWS Bedrock cho query/report. Chúng không đại diện cho core safety-event latency và chưa phải production SLO. Core safety-event latency cần benchmark riêng theo boundary Input -> AI output -> Decision Engine -> Backend -> Dashboard/CarSky. [E-09][E-14][E-20]
```

Giữ bảng latency bên dưới nếu số liệu đó có evidence E-20. Nếu chưa có raw log E-20, đổi `Measured` thành `Sampled / pending formal benchmark`.

---

# 6. Mục `14.3.2 Ước Tính Token & Chi Phí`

## Lỗi Có Thể Bị Hỏi

Report ghi đơn giá cụ thể:

```text
Input ~$0.0008 / 1,000 tokens | Output ~$0.0016 / 1,000 tokens
```

Nếu không có nguồn/quote chính thức trong evidence, nên tránh claim giá cụ thể như actual.

## Thay Câu Giá Bằng Block Này

```text
14.3.2 Ước Tính Token & Chi Phí

Cấu hình mô hình demo: AWS Bedrock — deepseek.v3.2 tại `ap-southeast-2`, đọc từ `SE/BE/.env`.

Token/cost trong bảng là estimate phục vụ demo và capacity planning. Đơn giá thực tế phụ thuộc provider pricing, region, model version và thời điểm sử dụng; cần khóa nguồn pricing chính thức trước khi đưa vào business case production.
```

---

# 7. Mục `14.3.4 Fallback Scenarios`

## Lỗi Còn Lệch Nhẹ

Mục này còn giữ đoạn code line cũ:

```text
// CopilotFleetReportPage.tsx – L1257
const isAiLoading = isLoadingInsight && !tripAi;
```

Line number có thể không còn đúng sau khi code thay đổi. Ngoài ra bảng loading text có thể bị hiểu là các field thật bị thay thế bằng text AI. Với project hiện tại, cách nói đúng là:

- JSON/local AI baseline vẫn render.
- Chỉ các vùng `AI narrative/insight` mới chờ Bedrock.
- Không ghi “AI đang...” vào field deterministic đã có số liệu.

## Thay Phần Đầu `14.3.4` Đến Trước `Layer 1` Bằng Block Này

```text
14.3.4 Kịch Bản Dự Phòng & Quản Lý Timeout (Fallback Scenarios)

Trạng thái giao diện:

Trong thời gian chờ Bedrock, UI vẫn render report deterministic từ JSON/local AI. Các metric canonical như Ranking Score, Risk Score, TTC/headway, event count, harsh event, near miss và maintenance KPI không được thay bằng text loading nếu đã có dữ liệu.

Chỉ các vùng AI narrative/insight mới hiển thị trạng thái chờ, ví dụ:

- Đang chờ Bedrock phản hồi hợp lệ.
- AI Copilot đang tổng hợp insight cho report đang xem.
- AI Copilot đã trả về insight hợp lệ từ Bedrock.

Nếu Bedrock lỗi, timeout hoặc payload không hợp lệ, UI giữ JSON/local AI baseline và không hiển thị insight giả.

Hạn chế treo kết nối (Timeout Guardrail):

Cơ chế: request Bedrock được quản lý bằng timeout/abort guard để tránh treo request vô hạn. Nếu user rời report hoặc đổi context, response cũ không được phép cập nhật UI context mới.
```

Giữ lại các phần `Layer 1` đến `Layer 5` phía sau vì phần đó đã đúng.

---

# 8. Mục `14.3.5 Quản Lý Nhật Ký, Bảo Mật & Quyền Truy Cập`

## Lỗi Có Thể Bị Hỏi

Mục này ghi:

```text
verifyCopilotAuth Middleware
COPILOT_API_TOKEN
90-Day Cleanup Filter
Driver Name Masking
```

Cần chắc chắn code có đủ. Nếu chưa muốn bị hỏi sâu, đổi wording thành “đã hỗ trợ / planned guardrail”, phân biệt implemented vs backlog.

## Thay Mục `14.3.5` Bằng Block An Toàn Hơn

```text
14.3.5 Quản Lý Nhật Ký, Bảo Mật & Quyền Truy Cập

Hạng mục
Trạng thái
Mô tả

Bedrock secret source
IMPLEMENTED
Bedrock configuration đọc từ `SE/BE/.env`, không dùng `SE/FE/.env.local` làm source of truth. Không đưa token/API key vào report hoặc public repo.

Copilot request audit
IMPLEMENTED / DEMO SCOPE
FE server ghi Copilot audit log cho request report/chat, gồm timestamp, request type, latency và token/cost fields nếu provider trả usage.

Payload validation
IMPLEMENTED
Bedrock insight chỉ được apply khi đúng report type, đúng trip/report signature và không thay đổi canonical metrics từ JSON/local AI.

Access control
CONFIGURABLE / PILOT BACKLOG
Nếu `COPILOT_API_TOKEN` được cấu hình, API có thể yêu cầu bearer token. RBAC theo vai trò fleet manager/admin vẫn là backlog pilot.

PII minimization
PARTIAL / POLICY REQUIRED
Report demo ưu tiên trip/sample ID và structured context. Chính sách production cần xác định rõ driver identity, retention, redaction và quyền truy cập raw media.

Retention
PILOT BACKLOG
Cần chốt thời gian lưu audit log, report export và raw media theo yêu cầu privacy/governance của pilot.
```

---

# 9. Mục `15.1 Fleet Safety Executive Report`

## Lỗi Nhỏ

Bảng vẫn có:

```text
Vehicle/driver cards
Business KPI table
best driver
```

Vì data demo là trip/sample, nên đổi thành `Trip cards`, `Safety KPI Context`, `highest-ranked trip`.

## Thay Bảng `15.1` Bằng Block Này

```text
15.1 Fleet Safety Executive Report

Khối
Giá trị quản trị
Điều kiện tin cậy

Fleet Summary
Nhìn nhanh fleet status, số trip, safe trips, fleet average score và high-risk frames
Date range đúng, data source rõ, không trộn demo/practice/pilot

Trip cards
Nhìn nhanh trip_id, Ranking Score, Trip Safety Risk, relative rank, max risk và high-risk frames
Score definition, exposure, period, data completeness

Review Priority
Ưu tiên safety review theo mức rủi ro/thứ tự cần kiểm tra
Phân biệt rõ relative rank và review priority

Safety KPI Context
So sánh fleet average và highest-ranked trip tương đối
Không dùng demo sample làm benchmark production

Event logs
Audit theo thời gian và severity
Episode dedup; timezone; immutable ID

AI narrative
Giảm thời gian đọc và tổng hợp
Chỉ dùng validated Bedrock insight; traceable to JSON/local AI inputs; human review
```

---

# 10. Mục `15.3 Export và hồ sơ kiểm toán`

## Lỗi Cần Chỉnh

Kiểm tra nếu đoạn cuối vẫn còn:

```text
PDF/print phải giữ...
Nên hỗ trợ export machine-readable...
```

Với code hiện tại, final demo scope là DOC, PDF bỏ.

## Thay Toàn Bộ `15.3` Bằng Block Này

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

Machine-readable CSV/JSON export nên nằm ở roadmap audit sau demo.
```

---

# 11. Mục `16 Connected-Car, CarSky và Driver HMI`

## Lỗi Cần Ghi Rõ

Nội dung mục 16 hiện đúng theo trạng thái demo, nhưng có một lệch với repo:

- Report nói bridge subscribe `Vehicle.Speed` và forward speed-mux.
- Trong repo vẫn còn file legacy `SE/BE/carsky/dms_hmi_bridge.lua` có mapping custom `Vehicle.ADAS.*` và kiểu encode cũ.
- Repo cũng có `SE/BE/carsky/dms_hmi_bridge_dual_push.lua` và deployed script/hotfix có thể là bản đúng.

Nếu BTC hỏi bằng chứng code, cần tránh trỏ nhầm vào file legacy. Thêm đoạn caveat này vào cuối mục 16.

## Copy-Paste Thêm Vào Cuối Mục `16`

```text
Implementation note:

Final demo contract for Android HMI is the decimal `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux` contract (`41.xxx` to `50.xxx`). Repository may still contain legacy bridge scripts for earlier custom VSS/custom property experiments. Final evidence should point to the deployed bridge script/runtime log that forwards `Vehicle.Speed` mux values, Backend mapper `SE/BE/app/integrations/carsky/mapper.py`, and Android APK decoder `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java`.

Do not use legacy `10000 + value` bridge encoding or custom `Vehicle.ADAS.*` path as the claimed final Android HMI path unless that exact deployment is verified again.
```

---

# 12. Mục `20 KPI Framework`

## Lỗi Có Thể Bị Hỏi

Dashboard KPI có target:

```text
report generation/export ≤ 30 s
```

Do Bedrock có thể chậm, nên tách local report render và Bedrock insight.

## Thay Dòng Dashboard KPI Bằng Block Này

```text
Dashboard
Time-to-identify; acknowledge; review; report render/export time
Fleet Dashboard implemented; chưa có formal usability baseline
Time-to-identify ≤ 15 s; time-to-acknowledge ≤ 20 s; event review ≤ 30 s; JSON/local AI report render ≤ 3 s; Word/DOC export ≤ 30 s; Bedrock insight latency đo riêng và không chặn local report
PENDING CONTROLLED WORKFLOW TEST
[E-22][E-40]
```

---

# 13. Mục `24.2 Offering hypothesis`

## Lỗi Nhỏ

Trong offering có:

```text
CarSky/OEM API, custom signal, deployment
```

Nên sửa `custom signal` thành `vehicle signal integration / speed-mux demo path`, vì custom properties không phải final path.

## Thay Dòng Đó Bằng

```text
CarSky/OEM integration
Vehicle signal integration, `PERF_VEHICLE_SPEED` speed-mux demo path, deployment support
```

---

# 14. Mục `30.1 Milestone placeholders`

## Lỗi Còn Lệch

`Report freeze` vẫn ghi:

```text
status = Bridge verified / VHAL mux implemented / Android correlation pending
```

Nên đổi cho khớp với mục 16 và 19.

## Thay Dòng `Report freeze` Bằng Block Này

```text
Report freeze
9/8/2026
Report owner
Update C1 final metrics; C2 production provenance; Backend 28/28 [E-15]; remove stale CarSky provisioning wording; status = CarSky/KUKSA/HMI Bridge verified, Android HMI verified for demo via `PERF_VEHICLE_SPEED` speed-mux, deployment-dependent route/relay noted; CARLA exact inventory only from E-11.
```

---

# 15. Evidence Register / Appendix E-04

## Lỗi Nhỏ

E-04 đang ghi:

```text
Same trip/frame/event/score at AI, orchestrator, API, WebSocket, Dashboard and HMI if available
```

Nếu report đã claim HMI verified for demo, nên cụ thể hóa HMI evidence.

## Thay Dòng E-04 Bằng

```text
E-04
One event is traceable end-to-end
Same trip/frame/event/score at AI, Decision Engine, API, WebSocket, Dashboard and, when CarSky deployment is active, HMI speed-mux/logcat evidence for the same event
P0. Namespace chuẩn theo Evidence_Checklist.md; trạng thái capability được diễn giải trong thân báo cáo, không suy ra chỉ từ ID.
```

---

# 16. Evidence Register / Appendix E-21

## Lỗi Nhỏ

E-21 đang ghi:

```text
Report exports are accurate/readable
```

Nên nói DOC export, tránh PDF.

## Thay Dòng E-21 Bằng

```text
E-21
Word/DOC report exports are accurate/readable
Three sample DOC reports generated from canonical data and visually reviewed; PDF is out of final demo scope
P1. Namespace chuẩn theo Evidence_Checklist.md; trạng thái capability được diễn giải trong thân báo cáo, không suy ra chỉ từ ID.
```

---

# 17. Evidence Register / Appendix E-24

## Cần Chỉnh

E-24 đang ổn, nhưng nên thêm rõ `Vehicle.Speed` speed-mux.

## Thay Dòng E-24 Bằng

```text
E-24
CarSky/KUKSA/VHAL/APK path is correlated
Platform logs + Signal Watch `Vehicle.Speed` mux values + deployed bridge log + Android `DMS_HMI` logcat/video for the same event
P1 / P0 if platform points depend on it. Namespace chuẩn theo Evidence_Checklist.md; trạng thái capability được diễn giải trong thân báo cáo, không suy ra chỉ từ ID.
```

---

# 18. Mục Owner / Evidence Gap Cuối Report

## Lỗi Nhỏ

Dòng cuối vẫn ghi:

```text
HMI
VHAL status, property IDs, final proof
```

Nên đổi để khớp speed-mux.

## Thay Dòng HMI Bằng

```text
HMI
`PERF_VEHICLE_SPEED` speed-mux status, deployed bridge script/log, Android `DMS_HMI` logcat, APK UI video, custom property decision
Embedded Lead
```

---

# 19. Search-And-Replace Cuối Cùng

Chạy kiểm tra thủ công trong report, nếu còn các cụm này thì thay:

```text
Android live correlation PARTIAL / verification pending
```

Thay bằng:

```text
Android HMI verified for demo / deployment-dependent via `PERF_VEHICLE_SPEED` speed-mux
```

```text
PDF export
```

Thay bằng:

```text
Word/DOC export
```

```text
SE/FE/.env.local
```

Thay bằng:

```text
SE/BE/.env
```

```text
custom DMS CarProperty fully implemented
```

Thay bằng:

```text
custom DMS CarProperty explored; final demo path uses `PERF_VEHICLE_SPEED` speed-mux
```

```text
Vehicle.ADAS.FinalRiskScore là HMI final path
```

Thay bằng:

```text
Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux is the final Android HMI demo transport
```

```text
xe critical
```

Nếu context là saved trip/sample, thay bằng:

```text
trip critical
```

---

# 20. Summary Để Bạn Sửa Nhanh

Các mục bắt buộc sửa trước khi chốt:

1. `Executive Summary / Trạng thái hiện tại`
2. `3.1.11 Baseline Summary Table`
3. `12.2 Reliability backlog`
4. `14.3.1 Response Latency`
5. `14.3.4 Fallback Scenarios`
6. `15.1 Fleet Safety Executive Report`
7. `15.3 Export và hồ sơ kiểm toán`
8. `16 Connected-Car, CarSky và Driver HMI` thêm implementation note
9. `20 KPI Framework`
10. `30.1 Milestone placeholders`
11. Appendix `E-04`, `E-21`, `E-24`
12. Owner/evidence gap dòng `HMI`

Sau khi thay 12 nhóm trên, report sẽ khớp hơn với project hiện tại và ít bị BTC bắt lỗi nhất.

