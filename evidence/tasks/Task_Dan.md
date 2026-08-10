# Task Ticket - Dân (Edge/Hardware/CARLA/Connected Car)

Primary scope: E-09, E-10, E-11, E-12, E-24, E-25, E-38.

## E-09 - Jetson performance benchmark

**Status: IN PROGRESS**  
Primary: Dân. Supporting: Hùng.

`Status.md` không được tính là benchmark evidence.

- [ ] Khóa Jetson model, power mode, clocks, input resolution, stream count và build versions.
- [ ] Chạy sustained performance benchmark theo protocol E-09.
- [ ] Xuất `benchmark.csv`, `tegrastats.log`, `environment.json` và video.
- [ ] Báo FPS, p50/p95/p99, drop rate và CPU/GPU/RAM.

Lưu tại `evidence/E-09/`.

## E-10 - Thermal/power/soak/stability

**Status: NOT EXECUTED**  
Primary: Dân. Supporting: Hùng.

Không tiếp tục giao chạy trong scope hiện tại.

- [x] Ghi report/register: `NOT EXECUTED - no thermal/power/long-run stability claim`.
- [x] Không dùng E-09 để suy ra thermal/power/soak stability.
- [ ] Chỉ mở lại E-10 ở post-hackathon deployment validation.

## E-11 - Full CARLA manifest

**Status: DONE**  
Primary: Dân. Supporting: Hùng.

Đã có đủ manifest, validation report, dataset summary và invalid-trip report; validation PASS, 50/50 valid trips. Không để task mở.

Owner closure:

- [ ] Dân xác nhận đã review `invalid_trip_report.csv` và ký trạng thái DONE trong index final.

## E-12 - Reproducible CARLA collection

**Status: OPEN**  
Primary: Dân.

- [ ] Ghi CARLA server/Python API/build, map, seed, GPU/OS và command.
- [ ] Thu một trip mẫu từ clean collector run.
- [ ] Rerun validator và lưu command log/video.
- [ ] Xuất `collector_environment.json`, `command.sh` và sample trip reference.

Lưu tại `evidence/E-12/`.



## E-24 - CarSky/KUKSA/VHAL/APK same-event trace

**Status: PARTIAL / RUNTIME COMMAND AND SOURCE-APK PATH VERIFIED; SAME-EVENT MEDIA CAPTURE PENDING**  
Primary: Dân. Supporting: Nhân.

- [x] Runtime command evidence có thật: `carsky_phase05.py scenario critical` -> `ok=true`, `mode=vehicle-speed-mux`, `sent=14`.
- [x] Source/APK path evidence có thật: Backend mapper -> Vehicle.Speed -> Lua bridge -> PERF_VEHICLE_SPEED -> Android CarPropertyManager.
- [x] Bundle đã tạo: `evidence/E-24/derived/carsky_trace_bundle.zip`.
- [ ] Cần bổ sung screenshot/video/logcat cùng event để đóng DONE.

Lưu tại `evidence/E-24/`.


## E-25 - Audio/TTS path

**Status: NOT EXECUTED**  
Primary: Dân.

Không tiếp tục giao chạy trong scope hiện tại.

- [x] Ghi report/register: `NOT EXECUTED - audio/TTS not claimed`.
- [x] Không dùng visual Android HMI evidence để suy ra audio hoạt động.

## E-38 - CARLA scenario-to-event matrix

**Status: PARTIAL**  
Primary: Dân. Supporting: Hùng.

Đã có `scenario_matrix.csv`, nhưng matrix hiện cho thấy chỉ 2 scenario được observed/retained và nhiều scenario chưa được ghi nhận.

- [ ] Thu fresh-run collector logs cho scenario được claim.
- [ ] Chỉ đánh dấu observed với scenario có retained metadata và event evidence.
- [ ] Không claim 22/22 scenario coverage từ code/validator unit test.

Lưu tại `evidence/E-38/`.
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