# Nhan Selected Evidence - Detailed Packet

Scope này chỉ gồm các mục Nhân thật sự liên quan tới phần đã làm: Fleet Dashboard, AI Copilot, Backend/API, CarSky/KUKSA/HMI Bridge/Android HMI, evidence/release packet. Không bao gồm Market/BOM/ROI/Pilot nếu chưa có dữ liệu thật.

## Evidence Files Đã Sinh

| File | Dùng cho |
|---|---|
| `15_automated_tests/test_command.log` | E-15, E-03, E-14, E-16 |
| `03_decision_event_schema/decision_event_schema_source.log` | E-03 |
| `03_decision_event_schema/api_trace.log` | E-03, E-14 |
| `17_intervention_scope/logs/no_actuator_search.log` | E-17 |
| `18_release_packet/release_manifest.json` | E-18 |
| `18_release_packet/release_manifest.sha256` | E-18 |
| `35_evidence_index/evidence_files.txt` | E-35 |
| `16_failure_handling/fault_matrix.csv` | E-16 |
| `02_as_is_architecture/source_map.csv` | E-02 |
| `19_copilot_grounding/factuality_label_template.csv` | E-19 |

---

## Bảng Rõ: Evidence Nào Đã Làm / Chưa Làm

| ID | Evidence | Trạng thái | Đã có gì thật? | Chưa làm / không claim |
|---|---|---|---|---|
| E-04 | Golden event trace | `LÀM MỘT PHẦN` | Có runtime screenshot CarSky/HMI do user chụp; có lệnh `carsky_phase05.py scenario critical`; có `04_event_trace/trace_index.md` template | Chưa lưu `golden_event.jsonl`, chưa lưu MP4 60-90s vào folder, chưa đủ timed trace nếu không có video |
| E-17 | Intervention human workflow | `ĐÃ LÀM SOURCE/LOG` | Có `17_intervention_scope/intervention_scope_statement.md`; có `17_intervention_scope/logs/no_actuator_search.log` | Cần owner sign-off nếu muốn đóng evidence chính thức |
| E-02 | AS-IS architecture khớp code | `ĐÃ LÀM SOURCE MAP` | Có `02_as_is_architecture/source_map.csv`; có CarSky runtime screenshot; có README platform utilization | Chưa có `as_is_architecture.pdf` final/sign-off từng arrow |
| E-03 | DecisionEvent schema thống nhất | `ĐÃ LÀM TEST/LOG` | Có `03_decision_event_schema/decision_event_schema_source.log`; `03_decision_event_schema/api_trace.log`; test contract pass trong `15_automated_tests/test_command.log` | Chưa export `decision_event.schema.json` machine-readable riêng |
| E-14 | Backend reliability giới hạn đúng thực tế | `LÀM MỘT PHẦN` | Có API/test evidence cho ingestion, idempotency, CarSky forwarding trong `test_command.log` | Chưa làm restart test, WebSocket reconnect trace, durability proof |
| E-15 | Automated test claims traceable | `ĐÃ LÀM` | Có `15_automated_tests/test_command.log`, kết quả `17 passed, 1 warning` | Chưa chạy full AI/FE/HMI clean-room suite, không claim full repo coverage |
| E-16 | Failure handling demonstrated | `LÀM MỘT PHẦN` | Có `16_failure_handling/fault_matrix.csv`; có CarSky fallback runtime output `mode=vehicle-speed-mux`; có Bedrock fallback docs | Chưa quay camera-offline, backend restart, provider-down MP4/log đầy đủ |
| E-18 | Release packet immutable | `ĐÃ LÀM MANIFEST` | Có `18_release_packet/release_manifest.json`; `18_release_packet/release_manifest.sha256` | Nếu sửa file sau manifest thì phải regenerate; chưa có access-check screenshot |
| E-19 | Copilot grounded, không bịa | `LÀM TEMPLATE / CHƯA CLAIM FACTUALITY` | Có `19_copilot_grounding/factuality_label_template.csv`; có fallback docs/evidence package | Chưa có `copilot_golden.jsonl`, raw outputs, reviewer labels, factuality summary |
| E-20 | Copilot latency/failure | `CHƯA LÀM BENCHMARK` | Có lệnh benchmark và nơi lưu expected output | Chưa chạy fixed prompt set 3+ lần, chưa có p50/p95/cost/provider_failure log |
| E-35 | Evidence index | `ĐÃ LÀM` | Có `35_evidence_index/evidence_files.txt` | Chưa có `access_test.csv` nếu evidence nằm trên Drive/external link |

## Kết Luận Ngắn

```text
Đã làm chắc: E-03, E-15, E-18, E-35.
Đã làm source/log nhưng cần sign-off hoặc video để mạnh hơn: E-02, E-04, E-17.
Làm một phần, không nên claim production/reliability/factuality đầy đủ: E-14, E-16, E-19.
Chưa làm benchmark thật: E-20.
```

---

## E-04 - Golden Event Trace

**Trạng thái:** `LÀM MỘT PHẦN`

**Claim / outcome**

Một event critical có thể được trace từ Backend sang CarSky/KUKSA, qua HMI Bridge, tới Android HMI.

**Evidence mạnh nhất hiện có**

- Runtime screenshot CarSky cùng màn hình:
  - Android HMI UI hiển thị `CRITICAL RISK`, `Microsleep`, `TTC 1.2s`, `Risk Score 88`.
  - Signal Watch đang watch `Vehicle.Speed=49.xxx`.
  - Bridge log có `DMS_HMI_SPEED_MUX Vehicle.Speed=... -> 0x11600207=...`.
- Terminal command:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python scripts/carsky_phase05.py scenario critical
```

Expected output:

```json
{
  "ok": true,
  "mode": "vehicle-speed-mux",
  "sent": 14
}
```

**Cần bổ sung nếu muốn chốt full**

- Lưu MP4 60-90s vào `04_event_trace/demo_60_90s.mp4`.
- Lưu screenshots vào `04_event_trace/screenshots/`.
- Ghi timestamp vào `04_event_trace/trace_index.md`.

**Caveat trung thực**

Nếu không có MP4 same-event thì chỉ claim runtime screenshot/source/test, chưa claim full timed trace.

---

## E-17 - Intervention Human Workflow

**Trạng thái:** `ĐÃ LÀM SOURCE/LOG`

**Claim / outcome**

Intervention là workflow cho người vận hành/tài xế, không phải actuator control.

**Evidence đã có**

- Scope statement:

```text
17_intervention_scope/intervention_scope_statement.md
```

- Search log:

```text
17_intervention_scope/logs/no_actuator_search.log
```

**Lệnh reproduce**

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
grep -RInE "actuator|brake_command|steer|throttle|autonomous|control_vehicle|vehicle_control|stop_vehicle" AI SE scripts README* 2>/dev/null
```

**Cách đọc log**

- Nếu match là `recommended_action`, `BRAKE_SAFE`, text UI, report wording: đây là human recommendation.
- Nếu có endpoint thật để phanh/lái/ga xe: không được claim human-only cho đoạn đó.

**Caveat**

Hệ thống có cảnh báo `BRAKE SAFELY`, nhưng đây là HMI/action recommendation, không phải actuator command.

---

## E-02 - AS-IS Architecture Khớp Code

**Trạng thái:** `ĐÃ LÀM SOURCE MAP`

**Claim / outcome**

AS-IS architecture khớp code theo flow hiện tại:

```text
AI/local telemetry
-> DecisionEvent / JSON baseline
-> Backend API
-> Fleet Dashboard / Copilot Report
-> CarSky Signal API
-> KUKSA Vehicle.Speed
-> DMS HMI Bridge
-> VHAL PERF_VEHICLE_SPEED
-> Android HMI APK
```

**Evidence đã có**

```text
02_as_is_architecture/source_map.csv
README_PLATFORM_UTILIZATION_CARSKY_AI_ENGINEERING_ALIGNMENT.md
evidence/platform_ai_engineering/README_PLATFORM_AI_ENGINEERING_EVIDENCE.md
```

**Evidence runtime nên dùng**

- CarSky screenshot có Signal Watch + Bridge log + Android HMI UI.
- Fleet Dashboard video/screenshot cho saved trips, ranking, report.

**Không được vẽ/claim**

- Custom DMS CarProperty production-ready.
- Automatic actuator control.
- Multi-instance durable cluster.
- ROI/pilot validated.

---

## E-03 - DecisionEvent Schema Thống Nhất

**Trạng thái:** `ĐÃ LÀM TEST/LOG`

**Claim / outcome**

AI/SE boundary dùng canonical `DecisionEvent` và Backend API validation.

**Evidence đã có**

```text
03_decision_event_schema/decision_event_schema_source.log
03_decision_event_schema/api_trace.log
15_automated_tests/test_command.log
```

**Lệnh reproduce**

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python -m pytest tests/test_contract.py
```

**Observed**

```text
tests/test_contract.py ........
```

**Caveat**

Schema evidence chứng minh contract-level behavior, không chứng minh model factual accuracy.

---

## E-14 - Backend Reliability Giới Hạn Đúng Thực Tế

**Trạng thái:** `LÀM MỘT PHẦN`

**Claim / outcome**

Backend có API/test coverage cho alert ingestion, idempotency, live snapshot, CarSky forwarding. Tuy nhiên live runtime state hiện không nên claim durable production persistence.

**Evidence đã có**

```text
15_automated_tests/test_command.log
03_decision_event_schema/api_trace.log
```

**Observed**

```text
17 passed, 1 warning
```

**Claim an toàn**

```text
Backend contract and CarSky forwarding are tested. Runtime live state is demo-oriented; restart durability requires separate persistence/restart evidence.
```

**Cần bổ sung nếu muốn claim reliability mạnh**

- `14_backend_reliability/restart_test.md`
- `14_backend_reliability/websocket_trace.jsonl`
- log before/after restart.

---

## E-15 - Automated Test Claims Traceable

**Trạng thái:** `ĐÃ LÀM`

**Claim / outcome**

Automated claims cho BE contract/alerts/CarSky có test traceable.

**Evidence đã có**

```text
15_automated_tests/test_command.log
```

**Observed**

```text
collected 17 items
tests/test_contract.py ........
tests/test_ai_alerts.py ....
tests/test_carsky.py .....
17 passed, 1 warning
```

**Lệnh reproduce**

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python -m pytest tests/test_contract.py tests/test_ai_alerts.py tests/test_carsky.py
```

**Caveat**

Đây là BE contract/alerts/CarSky subset, không phải full AI/FE/HMI clean-room suite.

---

## E-16 - Failure Handling Demonstrated

**Trạng thái:** `LÀM MỘT PHẦN`

**Claim / outcome**

Các failure chính có fallback/safe state, không fabricate data.

**Evidence matrix**

```text
16_failure_handling/fault_matrix.csv
```

**Cases nên quay/chụp**

| Failure | Evidence nên chụp |
|---|---|
| Bedrock invalid/timeout | Report giữ JSON/local baseline, status pending/unavailable |
| Custom CarSky VSS path missing | `fallback_reason` và `mode=vehicle-speed-mux` |
| Camera offline | HMI/Dashboard offline/unknown state |
| Backend restart | Log state nào mất, state nào còn |

**Caveat**

Hiện có fallback evidence cho Bedrock/CarSky path; camera offline và restart cần quay riêng nếu claim.

---

## E-18 - Release Packet Immutable

**Trạng thái:** `ĐÃ LÀM MANIFEST`

**Claim / outcome**

Evidence/release packet có manifest hash tại commit hiện tại.

**Evidence đã có**

```text
18_release_packet/release_manifest.json
18_release_packet/release_manifest.sha256
```

**Current manifest metadata**

```json
{
  "owner": "Nhan",
  "commit": "ab0d7007",
  "scope": ["E-04", "E-17", "E-02", "E-03", "E-14", "E-15", "E-16", "E-18", "E-19", "E-20", "E-35"]
}
```

**Caveat**

Nếu còn sửa file sau manifest, phải regenerate manifest.

---

## E-19 - Copilot Grounded, Không Bịa

**Trạng thái:** `LÀM TEMPLATE / CHƯA CLAIM FACTUALITY`

**Claim / outcome**

AI Copilot là explanation layer. Canonical metrics lấy từ JSON/local AI; Bedrock/Copilot output cần factual review nếu claim accuracy.

**Evidence đã có**

```text
19_copilot_grounding/factuality_label_template.csv
README_AI_FALLBACK_LAYERS.md
evidence/platform_ai_engineering/README_PLATFORM_AI_ENGINEERING_EVIDENCE.md
```

**Evidence cần làm để claim mạnh**

- Tạo fixed prompt set.
- Lưu raw Copilot output.
- Reviewer label:
  - numeric consistency
  - unsupported claim
  - wrong trip context
  - fallback correct

**Caveat**

Hiện có fallback/contract evidence; factuality golden-set chưa hoàn tất nếu chưa label thật.

---

## E-20 - Copilot Latency / Failure

**Trạng thái:** `CHƯA LÀM BENCHMARK`

**Claim / outcome**

Copilot latency/failure chỉ đại diện cho report/explanation generation, không đại diện cho safety-event latency.

**Lệnh benchmark nếu token hợp lệ**

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE
node benchmark_bedrock.ts
```

**Expected output cần lưu**

```text
20_copilot_benchmark/copilot_benchmark.csv
20_copilot_benchmark/provider_failure.log
```

**Caveat**

Không claim p50/p95 nếu chưa chạy fixed prompt set ít nhất 3 lần.

---

## E-35 - Evidence Index

**Trạng thái:** `ĐÃ LÀM`

**Claim / outcome**

Evidence files có index để reviewer truy vết.

**Evidence đã có**

```text
35_evidence_index/evidence_files.txt
```

**Lệnh reproduce**

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
find evidence -type f | sort > evidence/Nhan/35_evidence_index/evidence_files.txt
```

**Caveat**

Index chỉ chứng minh file tồn tại. Access permission/Drive sharing cần `access_test.csv` riêng nếu evidence nằm ngoài repo.
