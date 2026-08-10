# Task Ticket - Nhân (Technical Lead/Product/Backend/Business)

Primary scope: E-02, E-03, E-04, E-14, E-15, E-16, E-17, E-18, E-19, E-20, E-26, E-28 to E-36, E-40, E-41.

## Core architecture and integration

### E-02 - AS-IS architecture

**Status: OPEN**. Supporting: Hùng.

- [ ] Tạo `as_is_architecture.pdf` và `source_map.csv`.
- [ ] Map từng arrow tới commit/file/function và owner sign-off.

### E-03 - Canonical DecisionEvent contract

**Status: OPEN**. Supporting: Hùng.

- [ ] Export versioned schema/OpenAPI.
- [ ] Lưu golden valid/invalid payloads và API response trace.

### E-04 - Golden end-to-end event trace

**Status: OPEN**. Supporting: Hùng, Thiện, Dân.

- [ ] Chọn deterministic replay và đồng bộ clock.
- [ ] Capture cùng trip/frame/event/score tại AI, Decision Engine, API, WebSocket, Dashboard và HMI.
- [ ] Xuất `golden_event.jsonl`, video, screenshots và `trace_index.md`.

## Backend, reliability and release

### E-14 - Backend reliability boundary

**Status: OPEN**.

- [ ] Capture contract/dedup/WebSocket behavior.
- [ ] Restart backend và ghi rõ recent state bị mất nếu vẫn dùng in-memory store.
- [ ] Xuất `backend_contract.log`, `restart_test.md`, `websocket_trace.jsonl`.

### E-15 - Automated test traceability

**Status: OPEN**. Supporting: Hùng.

- [ ] Chạy AI/BE/FE/HMI test suite đúng release commit.
- [ ] Lưu full log, JUnit, coverage và command/environment.

### E-16 - Failure handling

**Status: OPEN**. Supporting: tất cả technical owners.

- [ ] Test missing model, corrupt frame, out-of-order sequence, API/network/provider failure.
- [ ] Capture safe state, error code, recovery và xác nhận không fabricate data.

### E-17 - Human intervention is not actuation

**Status: OPEN**. Supporting: Thiện.

- [ ] Capture API/UI operator-request workflow.
- [ ] Ghi scope statement xác nhận không có actuator path.

### E-18 - Immutable release packet

**Status: OPEN**.

- [ ] Freeze commit/dependencies/artifacts.
- [ ] Tạo release manifest và SHA-256.
- [ ] Test reviewer access từ clean/incognito context.

### E-26 - Clean-room build/run

**Status: OPEN**. Supporting: tất cả technical owners.

- [ ] Build BE/FE/AI trên máy/container mới từ packet final.
- [ ] Lưu `clean_room_run.log`, environment lock và video.

### E-36 - Long-run load test

**Status: OPEN**.

- [ ] Replay controlled stream 4-8 giờ.
- [ ] Log memory, queue, drops, reconnect và restart behavior.

### E-41 - Multi-instance readiness

**Status: DEFERRED**.

Không chạy trước khi có durable external store/outbox và multi-instance design. Đây không phải E-10; chỉ mở task khi prerequisite đạt.

## Copilot

### E-19 - Grounded/factual Copilot audit

**Status: OPEN**. Supporting: Thiện.

- [ ] Chạy tối thiểu 30 golden/adversarial questions.
- [ ] Lưu canonical input, raw output, validator result và reviewer labels.

### E-20 - Copilot latency/cost/failure

**Status: OPEN**.

- [ ] Chạy fixed prompt set tối thiểu 3 lần mỗi loại.
- [ ] Đo p50/p95, token/cost, timeout/provider-down/cache behavior.

### E-40 - Copilot review-time improvement

**Status: NOT EXECUTED**. Supporting: Thiện.

- [x] Ghi report/register: `NOT EXECUTED - no review-time improvement claim`.
- [x] Không dùng E-22 Dashboard workflow để suy ra time saving.

## Business, pilot and governance

### E-28 - Market sources

**Status: OPEN**.

- [ ] Lưu authoritative source snapshots, date, definition và calculation sheet.

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
- [ ] Không đánh dấu DONE chỉ vì có `EVIDENCE_INDEX.md`.
