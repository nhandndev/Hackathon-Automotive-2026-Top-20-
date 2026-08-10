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

**Status: OPEN**  
Primary: Dân. Supporting: Nhân.

- [ ] Đồng bộ clock.
- [ ] Gửi một known event có event ID cố định.
- [ ] Capture Backend payload, Signal Watch value, Bridge log, Android logcat và APK UI cùng event.
- [ ] Xuất `carsky_trace_bundle.zip`, MP4 và `mapping.md`.

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
