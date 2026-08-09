# Evidence Outputs — FleetDashboard, AI Copilot, Report Export, Android HMI

File này viết theo đúng format bạn yêu cầu:

```text
Output #xxx - Tên output
Claim / outcome
Điều kiện xác định đạt
Kết quả quan sát
Trạng thái
Evidence locator
Video timestamp
Caveat / giới hạn
```

Keyword kỹ thuật giữ tiếng Anh. Phần giải thích dùng tiếng Việt.

---

# Output #004 - FleetDashBoard

## Claim / outcome

Fleet Dashboard đã implemented ở mức demo vận hành cho Fleet Manager. Dashboard hiển thị saved/live trip context, trip detail, ranking, ranking analysis, performance insights, safety/maintenance reports và Word/DOC export. Dashboard sử dụng JSON/local AI làm baseline số liệu canonical, không tự bịa `Risk Score`, `Ranking Score`, `TTC/headway`, event count hoặc maintenance KPI ở frontend.

## Điều kiện xác định đạt

- Frontend build được bằng production build command.
- TypeScript/lint không lỗi.
- Dashboard đọc được saved trip JSON trong `SE/FE/src/data/saved_trips`.
- Saved trips được normalize thành completed trip context.
- Các view chính tồn tại trong source/UI flow:
  - Fleet Map / list.
  - Trip Detail.
  - Ranking.
  - Ranking Analysis.
  - Performance Insights.
  - Copilot Report Page.
- Report/Dashboard không dùng mock static insight khi data hoặc Bedrock chưa sẵn sàng.

## Kết quả quan sát

- `npm run lint` chạy thành công với exit code `0`.
- `npm run build` chạy thành công với exit code `0`.
- Build output tạo `dist/index.html`, bundle JS/CSS và `dist/server.cjs`.
- Source dự án ghi nhận các file chính:
  - `SE/FE/server.ts`
  - `SE/FE/src/App.tsx`
  - `SE/FE/src/data/btcTripData.ts`
  - `SE/FE/src/components/CopilotFleetReportPage.tsx`
- Saved trip loading và `Infinity` normalization có evidence source-level trong `btcTripData.ts`, `App.tsx`, `server.ts`.

## Trạng thái

`IMPLEMENTED / SOURCE AND BUILD VERIFIED`

## Evidence locator

- `SE/FE/package.json`
- `SE/FE/server.ts`
- `SE/FE/src/App.tsx`
- `SE/FE/src/data/btcTripData.ts`
- `SE/FE/src/components/CopilotFleetReportPage.tsx`

## Video timestamp

`TBD`

Gợi ý capture:

```text
00:00-00:10 Fleet Dashboard mở được
00:10-00:25 saved trips/list hiển thị
00:25-00:45 mở Trip Detail
00:45-01:05 mở Ranking / Ranking Analysis
01:05-01:25 mở Performance Insights
01:25-01:50 mở Copilot Report
```

## Caveat / giới hạn

Fleet Dashboard evidence hiện có source/build evidence. Cần bổ sung video workflow để chứng minh thao tác người dùng thật từ list -> trip -> evidence -> report/export. Usability baseline, accessibility audit, auth/RBAC và long-run reliability chưa phải production evidence.

---

# Output #005 - Saved Trips / JSON Local AI Baseline

## Claim / outcome

Saved trip JSON được dùng làm completed trip context cho demo và audit. JSON/local AI là nguồn số liệu canonical cho Dashboard và Copilot Report khi live AI runtime hoặc Bedrock không sẵn sàng.

## Điều kiện xác định đạt

- FE có cơ chế đọc saved trips từ `SE/FE/src/data/saved_trips`.
- Saved trips được normalize thành `runtime_status: completed`.
- Legacy JSON có `Infinity` không làm browser parse lỗi.
- Dashboard/Copilot dùng saved trip data làm baseline, không tự tạo số liệu giả.

## Kết quả quan sát

- Source evidence ghi nhận `saved_trips` trong `btcTripData.ts`.
- `server.ts` có saved trip endpoint/parser và logic normalize legacy JSON.
- `App.tsx` có normalization flow cho saved trip.
- Các file dự án liên quan nằm trực tiếp trong `SE/FE`.

## Trạng thái

`IMPLEMENTED / SOURCE VERIFIED`

## Evidence locator

- `SE/FE/src/data/btcTripData.ts`
- `SE/FE/src/App.tsx`
- `SE/FE/server.ts`

## Video timestamp

`TBD`

Gợi ý capture:

```text
00:10-00:25 Dashboard hiển thị saved trips
00:25-00:45 mở một saved trip detail
```

## Caveat / giới hạn

Saved trips là demo/replay context, không thay thế live field pilot data. Nếu xóa saved JSON để bàn giao, cần chạy lại AI/demo pipeline để sinh data mới trước khi test Dashboard.

---

# Output #006 - AI Copilot / Bedrock Fallback

## Claim / outcome

AI Copilot là explanation layer, không phải nguồn tạo canonical metrics. Report render JSON/local AI baseline trước; Bedrock chỉ được gọi lazy khi user mở report hoặc yêu cầu AI insight. Nếu Bedrock trả payload hợp lệ, UI apply validated insight; nếu timeout/token lỗi/payload sai, UI giữ local report và không hiển thị insight giả.

## Điều kiện xác định đạt

- Bedrock config đọc từ `SE/BE/.env`, không lấy từ `SE/FE/.env.local`.
- Có status hoặc contract phân biệt `validated`, `pending`, `unavailable`.
- Bedrock payload được validate theo report type/trip context.
- Local fallback không ghi đè ngược validated Bedrock insight khi input không đổi.
- Khi Bedrock lỗi, UI không render mock insight hoặc số liệu fake.

## Kết quả quan sát

- Source dự án có `SE/FE/server.ts` và `CopilotFleetReportPage.tsx`.
- Source snippets ghi nhận các từ khóa:
  - `AWS_BEARER_TOKEN_BEDROCK`
  - `BEDROCK_API_KEY`
  - `ai_status`
  - `validated`
  - `unavailable`
- Report/fallback behavior đã được mô tả trong README evidence và final audit map.

## Trạng thái

`IMPLEMENTED WITH GRACEFUL FALLBACK / FORMAL FACTUAL AUDIT PENDING`

## Evidence locator

- `README_AI_FALLBACK_LAYERS.md`
- `README_EVIDENCE_FLEETDASHBOARD_ANDROID_HMI.md`
- `SE/FE/server.ts`
- `SE/FE/src/components/CopilotFleetReportPage.tsx`

## Video timestamp

`TBD`

Gợi ý capture:

```text
01:25-01:40 mở Copilot Report
01:40-02:00 trạng thái chờ Bedrock hoặc validated Bedrock
02:00-02:20 fallback khi token lỗi/timeout, local report vẫn còn
```

## Caveat / giới hạn

Golden-set factual audit cho Bedrock chưa hoàn tất. Không claim factual accuracy production nếu chưa có bộ câu hỏi chuẩn, raw Bedrock outputs, validator result và reviewer labels. Bedrock latency/cost chỉ là Copilot generation evidence, không đại diện cho safety-event latency.

---

# Output #007 - Report Export Word/DOC

## Claim / outcome

Copilot Report hỗ trợ export Word-compatible DOC. DOC export là final demo scope thay cho PDF, vì browser PDF rendering từng có rủi ro xuất trang trắng hoặc mất style.

## Điều kiện xác định đạt

- UI có command export Word/DOC.
- Source có hàm export `.doc`.
- DOC chứa nội dung report chính:
  - title/report type
  - date range
  - trip/fleet summary metrics
  - KPI context
  - JSON/local AI baseline
  - validated Bedrock insight nếu có
- Không claim PDF export là final scope.

## Kết quả quan sát

- `npm run build` pass, chứng minh source report/export build được.
- Source snippets ghi nhận `handleExportWord`, `.doc`, `Word`.
- `CopilotFleetReportPage.tsx` nằm trong source manifest.

## Trạng thái

`IMPLEMENTED / DOC OUTPUT VISUAL REVIEW REQUIRED`

## Evidence locator

- `SE/FE/src/components/CopilotFleetReportPage.tsx`

## Video timestamp

`TBD`

Gợi ý capture:

```text
02:20-02:35 click Export Report
02:35-02:50 chọn Word/DOC export
02:50-03:10 mở file DOC đã tải
```

## Caveat / giới hạn

Cần bổ sung ít nhất 3 file DOC mẫu: Safety Detail, Safety Overview, Maintenance Detail hoặc Maintenance Overview. PDF export không nằm trong final demo scope. Machine-readable CSV/JSON export nên để roadmap audit sau demo.

---

# Output #008 - Fleet Dashboard Honest Fallback / Degraded State

## Claim / outcome

Dashboard và Copilot Report fail honestly: khi thiếu data, Bedrock lỗi, API down hoặc camera/live frame offline, UI hiển thị loading/degraded/fallback state thay vì hiển thị số liệu giả hoặc kết luận SAFE sai.

## Điều kiện xác định đạt

- Bedrock token lỗi/timeout không làm UI render AI insight giả.
- Không có saved trips thì UI báo empty/no data rõ ràng.
- Camera/live frames offline thì UI báo waiting/offline.
- API down hoặc WebSocket reconnect không làm Dashboard tự sinh trip/số liệu.

## Kết quả quan sát

- Source dự án cho fallback/validation đã có.
- Manual capture cho các tình huống lỗi vẫn cần bổ sung.

## Trạng thái

`PARTIAL / SOURCE-SUPPORTED / MANUAL CAPTURE REQUIRED`

## Evidence locator

- `README_AI_FALLBACK_LAYERS.md`
- `SE/FE/server.ts`
- `SE/FE/src/components/CopilotFleetReportPage.tsx`

## Video timestamp

`TBD`

Gợi ý capture:

```text
03:10-03:30 Bedrock unavailable: report giữ JSON/local AI
03:30-03:50 no saved trips/API down: UI empty/degraded
03:50-04:10 live camera offline: waiting/offline state
```

## Caveat / giới hạn

Source-level fallback không thay thế được user-facing proof. Cần video/screenshot cho ít nhất Bedrock lỗi và no-data state trước khi claim E-23 hoàn tất.

---

# Output #009 - Backend CarSky Publisher / Vehicle Speed-Mux

## Claim / outcome

Backend có mapper và publisher cho CarSky HMI path. DMS logical values được publish qua `Vehicle.Speed` bằng decimal `vehicle-speed-mux` groups `41.xxx` đến `50.xxx`, phù hợp với APK V2.2.

## Điều kiện xác định đạt

- Backend mapper tạo payload `transport: vehicle-speed-mux`.
- Signal path chính là `Vehicle.Speed`.
- Mux groups gồm:
  - `41.xxx`: Risk Score
  - `42.xxx`: Severity
  - `43.xxx`: Driver State
  - `44.xxx`: Alertness
  - `45.xxx`: Min TTC
  - `46.xxx`: Critical Alert
  - `47.xxx`: AI Status
  - `48.xxx`: Recommended Action
  - `49.xxx`: Real Speed
  - `50.xxx`: Safe Score
- Publisher queue không block core runtime khi CarSky chậm/lỗi.

## Kết quả quan sát

- Source dự án có:
  - `SE/BE/app/integrations/carsky/mapper.py`
  - `SE/BE/app/integrations/carsky/client.py`
  - `SE/BE/app/integrations/carsky/service.py`
- Source snippets ghi nhận `vehicle-speed-mux`, `Vehicle.Speed`, `_mux`, `41`, `50`.

## Trạng thái

`IMPLEMENTED / SOURCE VERIFIED`

## Evidence locator

- `SE/BE/app/integrations/carsky/mapper.py`
- `SE/BE/app/integrations/carsky/client.py`
- `SE/BE/app/integrations/carsky/service.py`

## Video timestamp

`TBD`

Gợi ý capture:

```text
04:10-04:25 Backend publish scenario
04:25-04:40 CarSky Signal Watch thấy Vehicle.Speed 41.xxx-50.xxx
```

## Caveat / giới hạn

Source evidence chứng minh mapper/publisher contract, nhưng E-24 cần cùng một event được chứng minh qua Signal Watch, bridge log, Android logcat và APK UI. Không dùng Signal Watch đơn lẻ để claim Android HMI đã update.

---

# Output #010 - Android HMI APK Artifact / Runtime Decoder

## Claim / outcome

Android HMI có APK artifact riêng cho Driver HMI. Evidence của mục này phải ưu tiên chứng minh từ chính file APK đã build/cài: APK package có `classes.dex`, chữ ký `META-INF`, class `vn.fpt.dms.hmi.MainActivity`, log tag `DMS_HMI`, Android `CarPropertyManager`, `PERF_VEHICLE_SPEED` và decoder mux trong DEX. Source code chỉ dùng để đối chiếu, không thay thế APK evidence.

## Điều kiện xác định đạt

- File APK tồn tại và có SHA-256 để định danh đúng artifact.
- APK chứa `classes.dex`, `AndroidManifest.xml`, `resources.arsc` và metadata chữ ký `META-INF`.
- `classes.dex` trích được các chuỗi runtime quan trọng:
  - `DMS_HMI`
  - `vn/fpt/dms/hmi/MainActivity`
  - `PERF_VEHICLE_SPEED`
  - `CarPropertyManager`
  - `Registered DMS VHAL transport`
  - `mux raw` hoặc `mux decimal raw`
  - `SAFE`, `CRITICAL`, `TTC`, `km/h`
- Version tag trong APK phải khớp source nếu muốn claim đúng bản deploy.
- Runtime cần logcat từ Android cho thấy APK nhận VHAL value và UI đổi theo event.

## Kết quả quan sát

- APK artifact hiện có:
  - `SE/HMI/release/dms-hmi-realtime-vhal.apk`
  - `SE/HMI/app/build/outputs/apk/debug/app-debug.apk`
- APK SHA-256 hiện tại:
  - `51a44e1570551c16abc83db7fa9f167f3ae40a62cd1b57bde5dc465adb91cbb0`
- APK ZIP entries quan sát được:
  - `AndroidManifest.xml`
  - `resources.arsc`
  - `classes.dex`
  - `META-INF/ANDROIDD.SF`
  - `META-INF/ANDROIDD.RSA`
  - `META-INF/MANIFEST.MF`
- `classes.dex` có các chuỗi chứng minh HMI runtime:
  - `DMS_HMI`
  - `vn/fpt/dms/hmi/MainActivity`
  - `PERF_VEHICLE_SPEED`
  - `CarPropertyManager`
  - `Registered DMS VHAL transport with custom properties + speed-mux fallback`
  - `mux raw=`
  - `mux speed=`
  - `SAFE`
  - `CRITICAL`
  - `TTC`
  - `km/h`
- Phát hiện cần chú ý:
  - Source `MainActivity.java` hiện ghi `BUILD_TAG = "V2.2 SPEED MUX"`.
  - APK release hiện scan từ `classes.dex` ra tag `V2.1 CUSTOM VHAL`.
  - Vì vậy không được claim APK hiện tại là V2.2 nếu chưa rebuild và reinstall đúng APK mới.

## Trạng thái

`APK ARTIFACT VERIFIED / VERSION CONSISTENCY NEEDS REBUILD CHECK / RUNTIME VIDEO REQUIRED`

## Evidence locator

- `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java`
- `SE/HMI/app/src/main/AndroidManifest.xml`
- `SE/HMI/README.md`
- `SE/HMI/release/dms-hmi-realtime-vhal.apk`
- `SE/HMI/app/build/outputs/apk/debug/app-debug.apk`
- APK internal entries: `AndroidManifest.xml`, `classes.dex`, `META-INF/ANDROIDD.SF`, `META-INF/ANDROIDD.RSA`, `META-INF/MANIFEST.MF`
- Runtime command locator: `logcat -d -s DMS_HMI:I AndroidRuntime:E CarPropertyManager:E | tail -160`

## Video timestamp

`TBD`

Gợi ý capture:

```text
04:35-04:45 APK version/build tag hiển thị trên UI hoặc logcat
04:45-05:00 Android logcat DMS_HMI nhận mux
05:00-05:20 APK UI đổi risk/severity/TTC/action/speed/safe score
```

## Caveat / giới hạn

APK static evidence chứng minh artifact có HMI runtime code, nhưng chưa chứng minh runtime đang nhận event thật. Cần cùng một event có logcat và video UI. Nếu source tag và APK tag lệch, phải rebuild APK, cài lại APK và lấy lại hash trước khi chốt evidence.

---

# Output #011 - CarSky / KUKSA / HMI Bridge / APK Runtime Chain

## Claim / outcome

Connected-Car path được verified cho demo khi có cùng một event đi xuyên suốt từ Backend đến APK đang chạy:

```text
Backend publish
-> CarSky REST Signal API
-> KUKSA / DMS Signal Broker
-> DMS HMI Bridge
-> VHAL PERF_VEHICLE_SPEED speed-mux
-> Android CarPropertyManager
-> DMS Android HMI APK
```

Riêng Android HMI không được chứng minh bằng source code đơn lẻ; phải có APK-derived evidence và logcat/UI runtime.

## Điều kiện xác định đạt

Cùng một event/scenario phải có đủ:

- Backend publish payload.
- CarSky Signal Watch thấy `Vehicle.Speed` mux values.
- HMI Bridge log forward sang `PERF_VEHICLE_SPEED`.
- Android logcat `DMS_HMI` từ APK đã cài nhận `prop 0x11600207`, `mux raw`, `mux decimal raw` hoặc `mux speed`.
- APK UI đổi đúng state.
- APK SHA/version trong evidence trùng với APK đã cài trong Android node.

## Kết quả quan sát

- Source dự án đã có cho Backend mapper, CarSky client và publisher service.
- APK artifact trong dự án đã có hash, ZIP entries, signing metadata và DEX strings.
- APK/source version hiện cần kiểm tra lại vì APK artifact scan ra `V2.1 CUSTOM VHAL`, trong khi source hiện là `V2.2 SPEED MUX`.
- Manual capture same-event chain vẫn cần bổ sung.

## Trạng thái

`PARTIALLY VERIFIED BY ARTIFACT / DEPLOYMENT-DEPENDENT / SAME-EVENT CAPTURE REQUIRED`

## Evidence locator

- `SE/BE/app/integrations/carsky/mapper.py`
- `SE/BE/app/integrations/carsky/client.py`
- `SE/BE/app/integrations/carsky/service.py`
- `SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua`
- `SE/BE/carsky/dms_hmi_bridge.lua`
- `SE/BE/carsky/dms_hmi_bridge_dual_push.lua`
- `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java`
- `SE/HMI/app/src/main/AndroidManifest.xml`
- `SE/HMI/release/dms-hmi-realtime-vhal.apk`
- `SE/HMI/app/build/outputs/apk/debug/app-debug.apk`
- Runtime locator cần capture: CarSky Signal Watch `Vehicle.Speed`, HMI Bridge deployed log, Android `logcat -d -s DMS_HMI:I AndroidRuntime:E CarPropertyManager:E | tail -160`

## Video timestamp

`TBD`

Gợi ý capture:

```text
04:10-04:25 Backend publish scenario
04:25-04:40 Signal Watch Vehicle.Speed
04:40-04:55 HMI Bridge log
04:55-05:10 Android logcat DMS_HMI from installed APK
05:10-05:25 APK UI update with same risk/severity/TTC/speed values
```

## Caveat / giới hạn

Repo còn chứa legacy/custom bridge scripts. Final demo evidence phải trỏ vào deployed bridge script/runtime log đúng contract `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux`, không trỏ nhầm legacy `Vehicle.ADAS.*` custom path. Nếu chỉ có Signal Watch mà không có APK hash/version + logcat + APK UI, chỉ được claim tới mức Backend -> CarSky/KUKSA, chưa được claim Android HMI end-to-end. Custom DMS CarProperty IDs là explored path, không phải final demo transport.

---

# Output #012 - Evidence Package Generator

## Claim / outcome

Project có script tạo evidence package tự động cho phần FleetDashboard + Android HMI, giúp gom source manifest, SHA-256, source snippets, APK artifacts và FE lint/build result.

## Điều kiện xác định đạt

- Script chạy được bằng Python.
- Script tạo folder evidence.
- Script tạo summary, manifest, snippets, APK artifacts, FE checks và manual capture TODO.
- FE checks có thể chạy bằng option `--run-checks`.

## Kết quả quan sát

Script đã chạy thành công:

```bash
python3 scripts/collect_fleetdashboard_android_hmi_evidence.py --run-checks
```

Output:

```text
evidence/fleetdashboard_android_hmi/
```

Generated files:

- `EVIDENCE_SUMMARY.md`
- `SOURCE_MANIFEST.md`
- `SOURCE_SNIPPETS.md`
- `HMI_APK_ARTIFACTS.md`
- `FE_CHECKS.md`
- `MANUAL_CAPTURE_TODO.md`

## Trạng thái

`IMPLEMENTED / GENERATED`

## Evidence locator

- `scripts/collect_fleetdashboard_android_hmi_evidence.py`
- `evidence/fleetdashboard_android_hmi/EVIDENCE_SUMMARY.md`
- `evidence/fleetdashboard_android_hmi/FE_CHECKS.md`
- `evidence/fleetdashboard_android_hmi/SOURCE_MANIFEST.md`
- `evidence/fleetdashboard_android_hmi/SOURCE_SNIPPETS.md`
- `evidence/fleetdashboard_android_hmi/HMI_APK_ARTIFACTS.md`
- `evidence/fleetdashboard_android_hmi/MANUAL_CAPTURE_TODO.md`

## Video timestamp

`N/A`

## Caveat / giới hạn

Script chỉ gom source/build evidence. Nó không tự tạo được screenshot/video từ browser hoặc CarSky runtime. E-21/E-22/E-23/E-24 vẫn cần capture thủ công trước khi claim fully verified.
