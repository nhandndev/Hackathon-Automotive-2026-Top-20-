# Hướng dẫn dùng bộ tài liệu báo cáo C2

## Vai trò 5 file

| File | Vai trò |
|---|---|
| `README.md` | Yêu cầu gốc của BTC |
| `readmeproposal.md` | Cam kết gốc của nhóm ở Proposal |
| `C2_PROGRESS_REPORT_FPTU_DMS_VISION.md` | Báo cáo tiến độ chính để chuyển thành PDF/slide |
| `C2_END_TO_END_DEMO_SCRIPT.md` | Runbook thao tác demo |
| `C2_REPORT_README.md` | File định tuyến và checklist này |

Chỉ lấy nội dung báo cáo từ `C2_PROGRESS_REPORT_FPTU_DMS_VISION.md`. Không đưa
toàn bộ command của runbook vào slide.

## Thông điệp cần giữ

> Hệ thống xử lý TTC, Driver State và telemetry tại AI runtime; Challenge 3 giữ
> đúng công thức BTC, còn Decision Engine phía sau dùng ngữ cảnh và thời gian để
> phát cảnh báo có chọn lọc đến Fleet Dashboard và CarSky HMI.

## Những cập nhật phải xuất hiện trong report

- Hai nhánh độc lập: CSV submission và product demo.
- Hai mode product demo: `hybrid-live` và `dataset-fleet`.
- Dashboard dùng ảnh, snapshot và event thật theo từng `trip_id`; không còn card
  fleet hard-code khi Backend đã có session.
- Dataset fleet đăng ký toàn bộ trip, inference tuần tự và giữ lịch sử trip đã
  hoàn thành trong phiên Backend.
- Decision Engine chỉ phát `open`, thay đổi có ý nghĩa và `resolved`; Frontend
  upsert theo `event_id` để tránh alert spam.
- Demo dùng multi-rate scheduling; CSV chấm điểm vẫn inference từng frame.
- CUDA đã được cấu hình cho PyTorch và ONNX Runtime, nhưng FPS end-to-end chính
  thức vẫn phải đo bằng rehearsal dài.
- Demo hiện gửi JPEG cabin/road đã annotate ở tần suất thấp đến Dashboard. Đây
  là ngoại lệ trình diễn; kiến trúc production event-only vẫn là mục tiêu.

## Những điều không được tuyên bố quá mức

- Không dùng C3 `100/100` để kết luận hoàn hảo vì safe score practice bão hòa 0.
- Không gọi multi-rate demo là pipeline CSV chính thức.
- Không gọi CarSky/HMI realtime là verified nếu deployment/device chưa được
  rehearsal trong buổi chạy hiện tại.
- Không gọi history là persistent qua Backend restart; artifact CSV/JSONL được
  lưu, còn Dashboard session history hiện ở RAM.
- Không tuyên bố Pi 5/Hailo, authentication, persistent outbox hoặc hidden-test
  performance đã hoàn thành.

## Evidence cần chụp trước khi nộp

- Evaluation JSON của 6 practice trips.
- Một `event_id` giống nhau tại AI JSONL, Backend, Dashboard và CarSky/HMI.
- Dashboard có nhiều trip với trạng thái `pending/running/completed`.
- Log CUDA provider và benchmark latency/FPS trên cùng máy demo.
- `pytest` Backend, Frontend production build và video backup dưới 10 phút.

## Checklist cuối

- [ ] Báo cáo có đủ 9 mục BTC yêu cầu.
- [ ] KPI ghi rõ phạm vi đo; số chưa đo để `Pending measurement`.
- [ ] Phân biệt realtime, replay và mock transport scenario.
- [ ] Không lộ `.env`, token, driver profile hoặc dữ liệu nhạy cảm.
- [ ] Có kế hoạch P0/P1 đến Code Freeze và phân công đủ 5 thành viên.
