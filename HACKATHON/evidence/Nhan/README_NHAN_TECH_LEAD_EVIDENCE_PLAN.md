# Evidence Folder - Nhan Technical Lead / Product

Folder này gom các evidence ticket Nhân owner. Mục tiêu là **trung thực**, không claim quá tay. File này dùng để biết:

- Ticket nào cần làm.
- Evidence nào đã có thể tạo từ repo.
- Evidence nào bắt buộc phải quay/chụp runtime.
- Evidence nào chưa đủ điều kiện, phải ghi caveat.

Packet chi tiết cho các mục Nhân thật sự liên quan trực tiếp:

```text
README_NHAN_SELECTED_EVIDENCE_DETAILED.md
```

## Quy Ước Trạng Thái

| Status | Ý nghĩa |
|---|---|
| `READY_TO_CAPTURE` | Có thể quay/chụp ngay bằng lệnh hoặc UI hiện tại. |
| `SOURCE_VERIFIED` | Có source/test/artifact evidence, nhưng cần runtime/video nếu muốn claim mạnh. |
| `MANUAL_REQUIRED` | Cần họp, phỏng vấn, báo giá, pilot hoặc quyết định của team. |
| `NOT_READY_TO_CLAIM` | Chưa đủ điều kiện để claim trong demo/report. |

---

## Tổng Quan Ticket

| ID | Tên evidence | Thư mục | Status | Việc cần làm ngắn |
|---|---|---|---|---|
| E-04 | Golden event trace | `04_event_trace/` | `READY_TO_CAPTURE` | Chọn 1 run, quay 60-90s và lưu event/log/screenshot cùng timestamp. |
| E-17 | Intervention chỉ là human workflow | `17_intervention_scope/` | `READY_TO_CAPTURE` | Chứng minh không có actuator path tự động điều khiển xe. |
| E-28..E-33 | Business & Market | `12_business_and_market/` | `MANUAL_REQUIRED` | Cần nguồn thật, báo giá thật, interview/pilot thật. |
| E-34 | Safety/privacy gates | `34_safety_privacy/` | `MANUAL_REQUIRED` | Tabletop review, approver, camera-offline state. |
| E-02 | AS-IS architecture khớp code | `02_as_is_architecture/` | `SOURCE_VERIFIED` | Vẽ sơ đồ và map từng arrow tới source/runtime evidence. |
| E-03 | DecisionEvent schema thống nhất | `03_decision_event_schema/` | `SOURCE_VERIFIED` | Export schema/golden payload/API trace từ BE tests. |
| E-14 | Backend reliability giới hạn đúng thực tế | `14_backend_reliability/` | `MANUAL_REQUIRED` | Test restart, WebSocket reconnect, ghi caveat mất in-memory data. |
| E-15 | Automated test claims traceable | `15_automated_tests/` | `READY_TO_CAPTURE` | Chạy test suite và lưu log đúng commit. |
| E-16 | Failure handling demonstrated | `16_failure_handling/` | `READY_TO_CAPTURE` | Capture fallback/safe state khi provider/signal/camera lỗi. |
| E-18 | Release packet immutable | `18_release_packet/` | `READY_TO_CAPTURE` | Tạo manifest hash + evidence index. |
| E-19 | Copilot grounded, không bịa | `19_copilot_grounding/` | `MANUAL_REQUIRED` | Cần reviewer label từng output, không chỉ test kỹ thuật. |
| E-20 | Copilot latency/cost/failure | `20_copilot_benchmark/` | `READY_TO_CAPTURE` | Chạy fixed prompt set 3+ lần, log latency/status. |
| E-26 | Clean-room build | `26_clean_room_build/` | `MANUAL_REQUIRED` | Cần máy/container mới, quay log full build. |
| E-35 | Evidence index | `35_evidence_index/` | `READY_TO_CAPTURE` | Sinh index từ toàn bộ `evidence/`. |
| E-36 | Long-run load test | `36_long_run_load_test/` | `MANUAL_REQUIRED` | Replay 4-8h, log memory/drops/reconnect. |
| E-41 | Multi-instance readiness | `41_multi_instance_readiness/` | `NOT_READY_TO_CLAIM` | Chỉ làm sau khi có durable architecture. |

---

## E-04 - Golden Event Trace

**Mục tiêu:** chứng minh cùng một event đi qua các lớp chính.

Luồng nên quay:

```text
Backend scenario critical
-> CarSky Signal Watch Vehicle.Speed
-> DMS_HMI_SPEED_MUX bridge log
-> Android HMI CRITICAL UI
-> reset normal
```

Expected outputs:

```text
04_event_trace/golden_event.jsonl
04_event_trace/trace_index.md
04_event_trace/screenshots/
04_event_trace/demo_60_90s.mp4
```

Lệnh hỗ trợ:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python scripts/carsky_phase05.py scenario critical
.venv/bin/python scripts/carsky_phase05.py scenario normal
```

Caveat cần ghi nếu thiếu video Android UI:

```text
Trace hiện chứng minh Backend -> CarSky -> Bridge. Android UI same-event capture cần bổ sung nếu chưa quay cùng timestamp.
```

---

## E-17 - Intervention Chỉ Là Human Workflow

**Mục tiêu:** khẳng định hệ thống không tự động can thiệp actuator/xe.

Claim đúng:

```text
Intervention trong bản demo là human workflow: hệ thống khuyến nghị safety review / brake safely / take break, không gửi actuator command để tự động phanh, ga, lái hoặc dừng xe.
```

Evidence nên có:

- Search log không có actuator path.
- Source/log chỉ có alert, report, CarSky signal/HMI state.
- Scope statement ký bởi owner.

Lệnh kiểm tra:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
grep -RInE "actuator|brake_command|steer|throttle|autonomous|control_vehicle|vehicle_control|stop_vehicle" AI SE scripts README* 2>/dev/null
```

Nếu grep có match, đọc kỹ để phân loại:

```text
Allowed: recommended_action, UI warning, text instruction.
Not allowed to claim autonomous: actual actuator/control API.
```

---

## E-28..E-33 - Business & Market

Phần này **không được bịa**. Chỉ dùng nguồn thật.

| ID | Evidence cần có | Trạng thái hiện tại |
|---|---|---|
| E-28 Market stats | PDF/page/table từ nguồn thị trường thật | Chưa đủ nếu chưa lưu source thật |
| E-29 Competitive gap | Vendor docs/demo/quote thật | Manual required |
| E-30 Pricing/BOM | Báo giá thật, low/base/high case | Manual required |
| E-31 Hypotheses tested | Interview 5-8 người, notes consent/anonymized | Manual required |
| E-32 Pilot value | Pre-register KPI/threshold trước pilot | Manual required |
| E-33 ROI not invented | Before/after pilot thật | Not ready nếu chưa pilot |

Safe wording:

```text
Business evidence hiện ở mức hypothesis/pre-pilot. ROI và market adoption không được claim là validated nếu chưa có interview/pilot/báo giá thật.
```

---

## E-34 - Safety / Privacy Gates

Checklist cần có:

- Camera offline state được test.
- Không gửi raw cabin frame mặc định nếu chưa có policy.
- Không nhận diện khuôn mặt cá nhân nếu chưa có consent.
- Human intervention only, không tự động actuator.
- Approver table: Product, AI, SE, Privacy.

Expected outputs:

```text
34_safety_privacy/safety_privacy_checklist.md
34_safety_privacy/tabletop_minutes.md
```

---

## E-02 - AS-IS Architecture Khớp Code

AS-IS nên vẽ đúng trạng thái hiện tại:

```text
AI/local pipeline
-> DecisionEvent / JSON telemetry
-> Backend API
-> Fleet Dashboard
-> AI Copilot Report
-> CarSky Signal API
-> KUKSA Vehicle.Speed
-> DMS HMI Bridge
-> VHAL PERF_VEHICLE_SPEED
-> Android HMI APK
```

Không vẽ:

```text
custom DMS CarProperty production-ready
automatic actuator control
multi-instance durable cluster
ROI/pilot validated
```

Expected outputs:

```text
02_as_is_architecture/as_is_architecture.md
02_as_is_architecture/source_map.csv
```

---

## E-03 - DecisionEvent Schema Thống Nhất

Evidence đã có thể tạo:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python -m pytest tests/test_contract.py
```

Source chính:

```text
AI/core/decision_engine/schemas.py
SE/BE/app/modules/ai_alerts/router.py
SE/BE/docs/AI_CONTRACT_AND_CHANGELOG.md
SE/BE/tests/test_contract.py
```

Expected outputs:

```text
03_decision_event_schema/decision_event.schema.json
03_decision_event_schema/golden_payloads/
03_decision_event_schema/api_trace.log
```

---

## E-14 - Backend Reliability Giới Hạn Đúng Thực Tế

Claim trung thực:

```text
Backend hiện có in-memory live state cho demo. Khi restart, một số runtime session/WebSocket state có thể mất nếu chưa persist durable storage. Saved trips/demo JSON là replay context, không thay thế production persistence.
```

Expected outputs:

```text
14_backend_reliability/backend_contract.log
14_backend_reliability/restart_test.md
14_backend_reliability/websocket_trace.jsonl
```

---

## E-15 - Automated Test Claims Traceable

Lệnh BE đã pass:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python -m pytest tests/test_contract.py tests/test_ai_alerts.py tests/test_carsky.py
```

Observed:

```text
17 passed, 1 warning
```

Expected output:

```text
15_automated_tests/test_command.log
15_automated_tests/junit/
15_automated_tests/coverage/
```

Caveat:

```text
BE contract/CarSky tests pass. Full AI/FE/HMI clean-room suite cần log riêng nếu claim toàn bộ repo.
```

---

## E-16 - Failure Handling Demonstrated

Cases nên capture:

| Failure | Expected safe behavior |
|---|---|
| Bedrock token lỗi/timeout | UI giữ JSON/local baseline, không render insight giả |
| Custom CarSky VSS path missing | Fallback sang `Vehicle.Speed` speed-mux |
| Camera offline | HMI/Dashboard hiển thị offline/unknown, không tự điền safe |
| Backend restart | Nói rõ state nào mất, state nào còn từ saved trip |

Expected outputs:

```text
16_failure_handling/fault_matrix.csv
16_failure_handling/provider_failure.log
16_failure_handling/camera_offline.mp4
```

---

## E-18 - Release Packet Immutable

Nên tạo manifest hash:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
find README* SE AI scripts evidence -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/.venv/*" \
  -not -path "*/.git/*" \
  -print0 | sort -z | xargs -0 shasum -a 256 > evidence/Nhan/18_release_packet/release_manifest.sha256
```

Expected outputs:

```text
18_release_packet/release_manifest.json
18_release_packet/release_manifest.sha256
18_release_packet/evidence_index.md
```

---

## E-19 - Copilot Grounded, Không Bịa

Không nên claim factual accuracy nếu chưa review thủ công.

Required:

- Fixed prompt set.
- Raw Copilot output.
- Reviewer label từng claim:
  - numeric consistency
  - unsupported claim
  - wrong trip context
  - fallback behavior

Expected outputs:

```text
19_copilot_grounding/copilot_golden.jsonl
19_copilot_grounding/factuality_summary.csv
```

---

## E-20 - Copilot Latency / Cost / Failure

Lệnh benchmark tùy token/provider. Nếu token hợp lệ:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE
node benchmark_bedrock.ts
```

Expected outputs:

```text
20_copilot_benchmark/copilot_benchmark.csv
20_copilot_benchmark/provider_failure.log
```

Caveat:

```text
Latency/cost chỉ đại diện cho AI Copilot report generation, không đại diện cho safety-event latency.
```

---

## E-26 - Clean-Room Build

Chỉ claim khi đã chạy trên máy/container mới.

Expected outputs:

```text
26_clean_room_build/clean_room_run.log
26_clean_room_build/environment.lock
26_clean_room_build/clean_room_build.mp4
```

Safe wording nếu chưa làm:

```text
Clean-room build chưa hoàn tất; hiện có local build/test evidence.
```

---

## E-35 - Evidence Index

Sinh index nhanh:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
find evidence -type f | sort > evidence/Nhan/35_evidence_index/evidence_files.txt
```

Expected:

```text
35_evidence_index/evidence_index.md
35_evidence_index/access_test.csv
```

---

## E-36 - Long-Run Load Test

Chưa nên claim nếu chưa chạy 4-8h.

Required metrics:

- duration
- memory
- CPU
- dropped events
- reconnect count
- final status

Expected outputs:

```text
36_long_run_load_test/load_test.log
36_long_run_load_test/resource_usage.csv
```

---

## E-41 - Multi-Instance Readiness

Không làm trước khi có durable architecture.

Safe wording:

```text
Multi-instance readiness is intentionally out of final demo claim because durable persistence, distributed coordination and multi-node recovery have not been validated.
```
