# FPTU DMS Vision - Corrected Evidence Tasks

Thư mục này được đối chiếu với `C:\FA Hackathon\evi\evidence` ngày 10/08/2026.

## Quy ước trạng thái

- `DONE`: Artifact cốt lõi đã có; không tiếp tục để như task mở.
- `PARTIAL`: Đã có một phần artifact nhưng còn thiếu đầu ra bắt buộc hoặc owner sign-off.
- `OPEN`: Chưa có evidence thực tế; `.gitkeep` không được tính là evidence.
- `IN PROGRESS`: Có status/hoạt động chạy thử nhưng chưa có measurement artifact.
- `DEFERRED`: Có thể thực hiện sau khi đạt điều kiện tiên quyết.
- `NOT EXECUTED`: Không thể thực hiện ở thời điểm hiện tại; không giao tiếp tục chạy, chỉ cập nhật disclosure trong report/video/register.

## Nguyên tắc sử dụng

1. Mỗi Evidence ID chỉ có một primary owner và chỉ xuất hiện trong một file task chính.
2. Supporting owner được ghi trong task của primary owner, không tạo task trùng.
3. Lưu artifact theo đường dẫn phẳng `evidence/E-XX/` để khớp thư mục thực tế.
4. Chỉ đổi sang `DONE` khi đầu ra bắt buộc tồn tại, mở được và nội dung chứng minh đúng claim.
5. `Status.md`, `.gitkeep`, source note hoặc file placeholder không được tính là evidence hoàn chỉnh.
6. E-10, E-25, E-39 và E-40 không thực hiện trong scope hiện tại; report không được claim các capability tương ứng.

## File phân công

- `Task_Hung_Tam.md`: Core AI, C1/C2/C3, Decision Engine, calibration và domain gap.
- `Task_Dan.md`: Jetson, CARLA và connected-car runtime.
- `Task_Nhan.md`: Architecture, backend, release, Copilot, business, governance và evidence index.
- `Task_Thien.md`: Dashboard, report export và warning UX.
- `TASK_STATUS_INDEX.md`: Trạng thái tổng hợp E-01 đến E-42.
