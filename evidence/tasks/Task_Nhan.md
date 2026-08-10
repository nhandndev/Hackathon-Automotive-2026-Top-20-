# Task Ticket - Nhân (Technical Lead/Product/Backend/Business)

Primary scope: E-02, E-03, E-04, E-14, E-15, E-16, E-17, E-18, E-19, E-20, E-26, E-28 to E-36, E-40, E-41.

## Core architecture and integration

### E-02 - AS-IS architecture

**Status: PARTIAL / ARCHITECTURE ARTIFACTS CREATED, OWNER SIGN-OFF PENDING**. Supporting: Hùng.

- [x] Tạo `as_is_architecture.pdf` và `source_map.csv`.
- [x] Map từng arrow tới commit/file/function.
- [ ] Owner sign-off từng arrow.

**Comment:** Evidence đã có ở `E-02/derived/` và `E-02/reports/`; chưa có chữ ký/xác nhận owner độc lập nên không đánh DONE.

### E-03 - Canonical DecisionEvent contract

**Status: DONE / SOURCE, SCHEMA, API TRACE, TEST VERIFIED**. Supporting: Hùng.

- [x] Export versioned schema/OpenAPI.
- [x] Lưu golden valid/invalid payloads và API response trace.

### E-04 - Golden end-to-end event trace

**Status: PARTIAL / TEST TRACE CREATED, RUNTIME CAPTURE REQUIRED**. Supporting: Hùng, Thiện, Dân.

- [x] Chọn deterministic replay và đồng bộ clock.
- [x] Capture deterministic Backend/CarSky command trace cho cùng scenario critical.
- [ ] Capture cùng trip/frame/event/score đồng bộ đầy đủ tại AI, Decision Engine, API, WebSocket, Dashboard và HMI bằng video/screenshot. (video ngoài folder nếu có thì cần attach/link vào E-04)
- [x] Xuất `golden_event.jsonl` và `trace_index.md`.
- [ ] Bổ sung video 60-90s và screenshots đồng bộ Signal Watch -> Bridge log -> Android HMI. (video ngoài folder nếu có thì cần attach/link vào E-04)

**Comment:** Có golden trace + runtime command `ok=true`; chưa có MP4/screenshot đồng bộ trong folder E-04 nên vẫn PARTIAL.

## Backend, reliability and release

### E-14 - Backend reliability boundary

**Status: DONE / CONTRACT, DEDUP, WEBSOCKET, RESTART LIMIT VERIFIED**.

- [x] Capture contract/dedup/WebSocket behavior.
- [x] Restart backend và ghi rõ recent state bị mất nếu vẫn dùng in-memory store.
- [x] Xuất `backend_contract.log`, `restart_test.md`, `websocket_trace.jsonl`.

### E-15 - Automated test traceability

**Status: DONE / BE TESTS, FE LINT-BUILD, HMI ARTIFACT VERIFIED**. Supporting: Hùng.

- [x] Chạy BE tests, FE lint/build và HMI APK artifact/static verification đúng commit.
- [ ] Chạy fresh HMI Gradle build/test khi có Gradle wrapper hoặc Android build environment chuẩn.
- [x] Lưu full log, JUnit, command/environment.
- [ ] Lưu coverage report.

**Comment:** DONE theo scope automated trace hiện có: BE pytest 29 passed, FE lint/build pass, APK hash/static scan pass. Không claim coverage hoặc fresh HMI rebuild.

### E-16 - Failure handling

**Status: PARTIAL / API, CARSKY, FALLBACK SOURCES VERIFIED; UI SCREENSHOT CAPTURED**. Supporting: tất cả technical owners.

- [x] Test malformed API payload, idempotency mismatch, missing live snapshot, CarSky auth/fallback, Bedrock/source fallback.
- [ ] Bổ sung missing model/corrupt frame/out-of-order sequence nếu owner muốn claim full chaos coverage.
- [x] Capture safe state, error code, recovery và xác nhận không fabricate data trong fault matrix.
- [x] Capture UI fallback screenshots bằng headless Chrome.

**Comment:** Partial vì chưa phủ full chaos matrix. Các fault đã chạy thật nằm trong `E-16/derived/fault_matrix.csv`; UI screenshots có trong `E-16/screenshots/`.

### E-17 - Human intervention is not actuation

**Status: DONE / HUMAN INTERVENTION WORKFLOW VERIFIED; NO BACKEND VEHICLE ACTUATOR API FOUND**. Supporting: Thiện.

- [x] Capture API/UI operator-request workflow.
- [x] Ghi scope statement xác nhận không có physical vehicle actuator path.

**Comment:** DONE. Scope statement phân biệt CarSky `/actuate` signal transport với physical vehicle actuation. Evidence ở `E-17/reports/` và `E-17/raw/intervention_trace.jsonl`.

### E-18 - Immutable release packet

**Status: PARTIAL / RELEASE MANIFEST CREATED; WORKTREE NOT CLEAN SO PACKET NOT IMMUTABLE**.

- [x] Tạo manifest hash cho commit/dependencies/artifacts.
- [ ] Freeze final packet từ clean worktree/tag/archive.
- [x] Tạo release manifest và SHA-256.
- [x] Tạo local access-check CSV.
- [ ] Test reviewer access từ clean/incognito context nếu có external sharing link.

**Comment:** Partial vì `git status --short` đang dirty. Không claim immutable release cho tới khi freeze từ clean commit/tag/archive.

### E-26 - Clean-room build/run

**Status: PARTIAL / CLEAN SOURCE ARCHIVE AND STATIC COMPILE CHECK CREATED; FULL CLEAN-ROOM BUILD NOT EXECUTED**. Supporting: tất cả technical owners.

- [x] Tạo clean source archive từ git commit và chạy static compile/file checks.
- [ ] Build BE/FE/AI trên máy/container mới từ packet final với dependency reinstall đầy đủ.
- [x] Lưu clean-room command logs và `environment.lock.json`.
- [ ] Bổ sung MP4 nếu cần reviewer proof thao tác.

**Comment:** Partial vì Docker daemon không chạy và chưa reinstall dependency trong container/máy mới. Có `git archive` + compile check để làm partial evidence.

### E-36 - Long-run load test

**Status: PARTIAL / SHORT LOAD SMOKE EXECUTED; 4-8H LONG-RUN PENDING**.

- [x] Chạy short backend load smoke bằng `/api/v1/alerts/snapshot` để kiểm tra ingest/latest snapshot path.
- [x] Log memory RSS, latency sample, frame count và latest snapshot result.
- [ ] Replay controlled stream 4-8 giờ.
- [ ] Log đầy đủ memory, queue, drops, reconnect và restart behavior trong long-run thật.

**Comment:** Evidence ở `E-36/`. Đây là smoke evidence thật, không thay thế 4-8h long-run nên chưa đánh DONE.

### E-41 - Multi-instance readiness

**Status: DONE / READINESS ASSESSMENT COMPLETED - NOT READY FOR MULTI-INSTANCE**.

- [x] Quét source state boundary cho Backend live alerts/trips/snapshots/interventions.
- [x] Quét FE Copilot cache/inflight state.
- [x] Lưu readiness matrix và required fixes.
- [ ] Chạy two-instance runtime test sau khi có durable store/outbox.

**Comment:** Evidence ở `E-41/`. Kết luận trung thực: hiện tại single-instance demo OK, multi-instance production chưa sẵn sàng vì state/cache còn process-local.

## Copilot

### E-19 - Grounded/factual Copilot audit

**Status: PARTIAL / GOLDEN SET AND SOURCE VALIDATOR VERIFIED; RAW BEDROCK REVIEW PENDING**. Supporting: Thiện.

- [x] Tạo 30 golden/adversarial questions cho Copilot report.
- [x] Verify source-level grounding controls: `ai_status`, report-mode prompt contract, Bedrock validator, timeout/cache/inflight handling.
- [x] Lưu canonical input/golden set và validator/source summary.
- [ ] Chạy raw Bedrock outputs + human reviewer labels cho từng câu hỏi.

**Comment:** Evidence ở `E-19/`. Không claim formal factual accuracy vì chưa có raw Bedrock output và reviewer labels.

### E-20 - Copilot latency/cost/failure

**Status: PARTIAL / OFFLINE FAILURE AND COST-BUDGET EVIDENCE CREATED; REAL BEDROCK LATENCY PENDING**.

- [x] Tạo fixed prompt set cho 3 loại Copilot request.
- [x] Ước tính token/cost budget từ prompt size, không gọi provider ngoài.
- [x] Verify source timeout/provider-down/cache/inflight controls.
- [x] Chạy provider-down simulation nội bộ không external egress.
- [ ] Chạy real Bedrock benchmark 3+ lần mỗi prompt sau khi có approval gửi prompt/data ra Bedrock.
- [ ] Đo p50/p95 thật và token/cost thật từ payload `usage` của Bedrock.

**Comment:** Evidence ở `E-20/`. Không claim real Bedrock latency/cost vì chưa gọi provider thật trong evidence này.

### E-40 - Copilot review-time improvement

**Status: NOT EXECUTED / NO REVIEW-TIME IMPROVEMENT CLAIM**. Supporting: Thiện.

- [x] Ghi report/register: `NOT EXECUTED - no review-time improvement claim`.
- [x] Không dùng E-22 Dashboard workflow để suy ra time saving.
- [ ] Chạy before/after review-time study nếu muốn claim productivity/time saving.

**Comment:** Evidence ở `E-40/`. Đây là claim-control evidence, không phải performance improvement evidence.

## Business, pilot and governance

### E-28 - Market sources

**Status: OPEN / NOT EXECUTED**.

- [ ] Lưu authoritative source snapshots, date, definition và calculation sheet.

**Comment:** Chưa làm. E-28 cần nguồn thị trường thật, snapshot/PDF/source URL và calculation sheet; không tự bịa số liệu thị trường.

### E-29 - Competitive matrix

**Status: OPEN**.

- [ ] Hoàn thiện feature/pricing comparison với source URL/snapshot và access date.

### E-30 - Pricing/BOM/unit economics

**Status: OPEN**. Supporting: Dân.

- [ ] Thu BOM/quotes thật và tính low/base/high sensitivity.
- [ ] Tách approved quote, estimate và hypothetical pricing.

### E-31 - Customer/buyer hypotheses

**Status: OPEN**.

- [ ] Thực hiện 5-8 interviews có consent và cùng questionnaire.
- [ ] Tổng hợp cả confirming và disconfirming insight.

### E-32 - Pilot protocol

**Status: OPEN**. Supporting: Hùng.

- [ ] Pre-register KPI, label protocol, sample-size rationale và stop/scale gates.

### E-33 - ROI model

**Status: OPEN**.

- [ ] Tạo transparent ROI calculator và baseline log.
- [ ] Tách observed, assumed và pending values; không claim field ROI khi chưa có pilot.

### E-34 - Safety/privacy gates

**Status: OPEN**. Supporting: Dân.

- [ ] Tabletop review consent, retention, role access, escalation và camera-offline behavior.
- [ ] Ghi approver và unresolved items, không chỉ tick checklist.

### E-35 - Reviewer evidence index

**Status: PARTIAL**. Supporting: Thiện.

Hiện chỉ có danh sách E-01 đến E-42.

- [ ] Map claim → artifact path → hash → timestamp → owner.
- [ ] Tạo `access_test.csv` và kiểm tra từng link/file ở reviewer mode.
- [x] Không đánh dấu DONE chỉ vì có `EVIDENCE_INDEX.md`.

**Comment:** Đã giữ status PARTIAL đúng thực tế; còn thiếu claim-file-hash-owner mapping và reviewer access test.
