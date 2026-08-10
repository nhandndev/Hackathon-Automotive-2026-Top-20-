# Task Ticket - Thiện (Frontend/Dashboard/Report/UX)

Primary scope: E-21, E-22, E-23, E-39.

## E-21 - Report export accuracy/readability

**Status: OPEN**  
Primary: Thiện. Supporting: Nhân.

- [ ] Generate ít nhất ba report từ canonical data.
- [ ] Đối chiếu từng KPI với source JSON.
- [ ] Review toàn bộ trang về clipping, pagination, font và table layout.
- [ ] Xuất `report_samples/` và `report_qa.csv`.

Lưu tại `evidence/E-21/`.

## E-22 - Dashboard workflow

**Status: OPEN**  
Primary: Thiện. Supporting: Nhân.

- [ ] Dùng canonical replay, không dùng hidden seeded mock.
- [ ] Quay list → trip → event → evidence → human action.
- [ ] Hiển thị ID/provenance trong video và screenshots.

Lưu tại `evidence/E-22/`.

## E-23 - Dashboard honest failure states

**Status: OPEN**  
Primary: Thiện. Supporting: Nhân.

- [ ] Capture empty data, API down, WebSocket reconnect, stale data và invalid trip.
- [ ] Ghi observed recovery; UI không được thay lỗi thật bằng mock result.
- [ ] Xuất `ui_failure_states.pdf` và video.

Lưu tại `evidence/E-23/`.

## E-39 - Driver-warning human-factors review

**Status: NOT EXECUTED**  
Primary: Thiện. Supporting: Dân.

Không tiếp tục giao user study trong scope hiện tại.

- [x] Ghi report/register: `NOT EXECUTED - no human-factors, alert-fatigue or driver-acceptance outcome claim`.
- [x] Không dùng technical HMI evidence E-24 để suy ra UX/safety outcome.
- [ ] Chỉ mở lại trước external field pilot khi có participant protocol và consent.
