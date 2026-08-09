# Evidence Checklist — Fleet Dashboard, AI Copilot, Android HMI, VHAL, CarSky

File này gom riêng phần `Evidence_Checklist` liên quan đến:

- `Fleet Dashboard`
- `AI Copilot / Bedrock report`
- `Report export`
- `Saved trips / JSON local AI`
- `Android HMI APK`
- `VHAL`
- `CarSky / KUKSA / HMI Bridge`

Mục tiêu: khi viết report hoặc bị BTC hỏi evidence, mình có thể chỉ ra **evidence ID nào**, **cần bằng chứng gì**, **source file nào**, **lệnh nào chạy**, và **artifact nào phải lưu**.

---

## 1. Evidence ID Liên Quan

| Evidence ID | Phạm vi | Trạng thái nên claim | Artifact cần có |
|---|---|---|---|
| `E-19` | AI Copilot factual safety | `PENDING FORMAL AUDIT` | Golden questions, canonical input, raw Bedrock output, validator result |
| `E-20` | Copilot latency/cost/failure behavior | `DEMO SAMPLE / PENDING PRODUCTION SLO` | Copilot latency log, timeout/failure sample, token usage nếu provider trả |
| `E-21` | Word/DOC report export | `IMPLEMENTED / VISUAL REVIEW REQUIRED` | 3 sample DOC reports, screenshots hoặc review note |
| `E-22` | Fleet Dashboard workflow | `IMPLEMENTED / WORKFLOW VERIFIED BY SCREEN RECORDING` | Video/screenshot: list -> trip -> event -> evidence -> report/action |
| `E-23` | Dashboard fails honestly | `PARTIAL / TEST REQUIRED` | Empty data, API down, WebSocket reconnect, stale/invalid state screenshots |
| `E-24` | CarSky/KUKSA/VHAL/APK path | `VERIFIED FOR DEMO / DEPLOYMENT-DEPENDENT` | Signal Watch, bridge log, Android logcat, APK UI video for same event |

---

## 2. Source Of Truth Trong Project

### Fleet Dashboard / Saved Trips

| Claim | Source file |
|---|---|
| Saved trips load từ JSON/local AI | `SE/FE/src/data/btcTripData.ts` |
| Runtime trips được normalize thành completed trips | `SE/FE/src/App.tsx` |
| FE server đọc saved trip JSON và normalize `Infinity` | `SE/FE/server.ts` |
| Copilot report page render safety/maintenance reports | `SE/FE/src/components/CopilotFleetReportPage.tsx` |
| FE build/lint scripts | `SE/FE/package.json` |

### AI Copilot / Bedrock

| Claim | Source file |
|---|---|
| Bedrock env source từ `SE/BE/.env` | `SE/FE/server.ts` |
| Payload status `validated / unavailable / pending` | `SE/FE/server.ts`, `CopilotFleetReportPage.tsx` |
| Validated Bedrock insight không bị fallback ghi đè | `SE/FE/src/components/CopilotFleetReportPage.tsx` |
| Word/DOC export | `SE/FE/src/components/CopilotFleetReportPage.tsx` |

### CarSky / VHAL / Android HMI

| Claim | Source file |
|---|---|
| Backend emits `vehicle-speed-mux` | `SE/BE/app/integrations/carsky/mapper.py` |
| CarSky client pulses speed-mux values | `SE/BE/app/integrations/carsky/client.py` |
| CarSky publisher has bounded queue/drop old telemetry | `SE/BE/app/integrations/carsky/service.py` |
| Android APK reads `PERF_VEHICLE_SPEED` | `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java` |
| Android APK decodes `41.xxx` to `50.xxx` groups | `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java` |
| APK install/logcat instructions | `SE/HMI/README.md` |
| VSOCK relay instructions | `SE/HMI/vhal-vsock-relay/README.md` |
| Bridge scripts | `SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua`, deployed bridge runtime log |

Important caveat:

```text
Final report should not point to legacy bridge scripts as the final HMI path.
Final demo contract is Vehicle.Speed / PERF_VEHICLE_SPEED decimal speed-mux.
If repo still has legacy custom Vehicle.ADAS bridge scripts, call them legacy/experimental unless the exact deployment used them and was re-verified.
```

---

## 3. Cách Tạo Evidence Tự Động

Chạy script gom evidence:

```bash
python3 scripts/collect_fleetdashboard_android_hmi_evidence.py
```

Output mặc định:

```text
evidence/fleetdashboard_android_hmi/
```

Nếu muốn chạy thêm FE lint/build:

```bash
python3 scripts/collect_fleetdashboard_android_hmi_evidence.py --run-checks
```

Script sẽ tạo:

| File output | Nội dung |
|---|---|
| `EVIDENCE_SUMMARY.md` | Summary theo E-19 đến E-24 |
| `SOURCE_MANIFEST.txt` | Danh sách source file và SHA-256 |
| `FE_CHECKS.txt` | Kết quả `npm run lint/build` nếu dùng `--run-checks` |
| `SOURCE_SNIPPETS.md` | Snippet tìm thấy trong code cho saved trips, Bedrock, DOC export, speed-mux |
| `HMI_APK_ARTIFACTS.txt` | APK/script release nếu tồn tại + hash |
| `MANUAL_CAPTURE_TODO.md` | Những evidence phải chụp/quay thủ công từ browser/CarSky |

---

## 4. Evidence Cần Chụp Thủ Công

### E-21 — Word/DOC Report Export

Cần lưu:

- 1 DOC Safety Detail.
- 1 DOC Safety Overview.
- 1 DOC Maintenance Detail hoặc Maintenance Overview.
- Screenshot file mở được trong Word/Pages/LibreOffice.

Checklist:

```text
[ ] Report title đúng.
[ ] Date range là ngày hiện tại hoặc range thật.
[ ] Có JSON/local AI baseline metrics.
[ ] Có validated Bedrock insight nếu Bedrock trả về.
[ ] Không còn PDF claim trong final demo scope.
```

### E-22 — Fleet Dashboard Workflow

Quay video hoặc chụp sequence:

```text
Dashboard list/map
-> Trip Detail
-> Event/evidence/timeline
-> Ranking / Ranking Analysis
-> Copilot Report
-> Word/DOC Export
```

Checklist:

```text
[ ] Saved trips hiển thị.
[ ] Không còn "no trip" khi saved JSON tồn tại.
[ ] Ranking có score/risk/avg risk rõ.
[ ] Report overview khác report detail.
[ ] AI Copilot không hiển thị fake insight khi Bedrock lỗi.
```

### E-23 — Dashboard Fails Honestly

Tạo/chụp các tình huống:

```text
API down
No saved trips
Bedrock token expired
Invalid Bedrock payload
Camera/live frame offline
```

Expected:

```text
UI hiện loading/fallback/degraded state.
Không hiện số liệu giả.
Không gọi lỗi là SAFE nếu thiếu data.
```

### E-24 — CarSky / VHAL / APK Correlation

Cần cùng một event/scenario:

```text
1. Backend publish speed-mux payload.
2. CarSky Signal Watch thấy Vehicle.Speed đổi, ví dụ 41.088, 42.002, 45.025, 49.048, 50.083.
3. HMI Bridge log có forward Vehicle.Speed -> PERF_VEHICLE_SPEED.
4. Android logcat `DMS_HMI` có mux decimal raw/group/payload.
5. APK UI đổi risk/severity/TTC/action/speed/safe score.
```

Logcat command:

```bash
logcat -d -s DMS_HMI:I AndroidRuntime:E CarPropertyManager:E | tail -160
```

Expected log patterns:

```text
Registered DMS VHAL transport with speed-mux
mux decimal raw=41.xxx group=41 payload=...
prop 0x11600207=...
```

---

## 5. Copy-Paste Evidence Wording Cho Report

### Fleet Dashboard

```text
Fleet Dashboard evidence is based on source-level implementation, successful FE build/lint, saved trip loading, and workflow screenshots/video. Dashboard uses JSON/local AI as the canonical metric baseline and does not create risk/ranking metrics in the UI.
```

### AI Copilot

```text
AI Copilot evidence is limited to demo integration and fallback behavior. Bedrock is an explanation layer; JSON/local AI remains the deterministic baseline. Golden-set factual audit remains pending before production claims.
```

### Report Export

```text
Report export evidence is based on Word/DOC output generated from canonical report data. PDF export is out of final demo scope.
```

### Android HMI / CarSky

```text
Android HMI evidence is based on the Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux path. Required proof is a same-event chain: Backend publish -> CarSky Signal Watch -> HMI Bridge log -> Android DMS_HMI logcat -> APK UI update. Custom DMS CarProperty IDs are treated as explored path, not the final demo transport.
```

