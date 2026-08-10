# E-09 — Jetson performance benchmark

## Trạng thái tại thời điểm bàn giao

**PARTIAL — PRE-FLIGHT VÀ IDLE BASELINE ONLY. BENCHMARK HIỆU NĂNG CHƯA ĐƯỢC THỰC HIỆN.**

Thư mục này ghi nhận cấu hình phần cứng, power mode, trạng thái clocks và tài nguyên của Jetson ở trạng thái gần như nhàn rỗi. Các tệp hiện có không chứng minh hiệu năng của workload FPTU DMS Vision dưới tải và không được dùng để công bố FPS, p50/p95/p99, drop rate, công suất dưới tải hoặc độ ổn định nhiệt khi chạy kéo dài.

Việc thiếu các artifact benchmark không phải do thất lạc dữ liệu. Các artifact đó chưa được tạo vì workload final chưa hoàn tất một phiên chạy hợp lệ trên Jetson tại thời điểm thu thập.

## Artifact hiện có

| Artifact | Nội dung xác nhận được | Giới hạn |
|---|---|---|
| `environment.json` | Jetson Orin Nano Engineering Reference Developer Kit Super; Linux for Tegra R36.4.4; Python 3.10.12; bộ nhớ và dung lượng lưu trữ tại thời điểm chụp | Không ghi được Git commit/status; truy vấn JetPack, CUDA, TensorRT và ONNX Runtime chưa thành công; snapshot được tạo trước các lần sửa dependency sau đó nên không đại diện cho môi trường runtime cuối |
| `nvpmodel.txt` | Power mode tại thời điểm chụp là **25W**, mode ID **1**; 6 CPU online; GPU max 918 MHz; EMC max 3199 MHz | Chỉ là snapshot cấu hình, không phải kết quả benchmark |
| `jetson_clocks.txt` | Trạng thái CPU/GPU/EMC và quạt tại thời điểm chụp | `clocks_locked` trong `environment.json` là `false`; tệp này không chứng minh clocks đã được khóa trong suốt một phiên benchmark |
| `tegrastats_idle.log` | 59 mẫu trong khoảng 2026-08-10 11:58:40–11:59:39 (UTC+7); RAM 2894–2909 MB; GPU trung bình 1.54%, tối đa 36%; GPU/Tj tối đa 46.031 °C; VDD_IN trung bình 3.684 W, khoảng 3.634–3.991 W | Chỉ là **idle baseline khoảng 59 giây**. Không được diễn giải thành công suất, nhiệt độ hoặc mức sử dụng khi chạy FPTU DMS Vision |
| `events-test/` | Thư mục placeholder cho lần chạy thử | Không có DecisionEvent; không phải evidence kết quả |

## Artifact chưa có và lý do

| Artifact yêu cầu | Trạng thái | Lý do chưa tạo |
|---|---|---|
| `benchmark.csv` | Chưa có | Chưa có phiên inference/demo hoàn tất trên workload final; chưa thu được chuỗi latency theo từng frame/stage để tính FPS, p50/p95/p99 và drop rate một cách hợp lệ |
| `tegrastats.log` dưới tải | Chưa có | Các lần chạy dừng trong giai đoạn khởi tạo hoặc xử lý compatibility, chưa đạt warm-up và sustained run theo protocol E-09. `tegrastats_idle.log` không thay thế artifact này |
| Video benchmark | Chưa có | Chưa có phiên demo/inference ổn định để quay đồng thời workload, đầu ra và trạng thái thiết bị |
| `prediction.csv`/kết quả trip hoàn chỉnh | Chưa có | Chưa hoàn tất xử lý toàn bộ trip bằng source và model final trên Jetson |

## Nguyên nhân kỹ thuật đã quan sát

1. Source trên Jetson là phiên bản cũ và chưa đồng bộ với source final dùng cho hồ sơ dự án.
2. Model C2 ban đầu không tương thích với ONNX landmark backend đang hoạt động; model production final chưa được xác nhận trong phiên chạy này.
3. PyTorch báo CUDA runtime/driver không tương thích; ONNX Runtime không phát hiện được GPU đúng cách. Vì vậy chưa thể xác nhận GPU acceleration.
4. Môi trường Python từng có xung đột ABI giữa NumPy, SciPy, Matplotlib, pandas và scikit-learn; các package đã được xử lý từng phần nhưng chưa có một environment final được khóa và tái kiểm chứng đầy đủ.
5. Do workload dừng trước khi hoàn tất trip, mọi phép tính throughput, latency percentile, frame drop, thermal/power under load hoặc stability đều sẽ thiếu cơ sở nếu được công bố.

## Kết luận sử dụng evidence

Các tệp hiện tại chỉ đủ để xác nhận:

- Thiết bị Jetson và power mode 25W đã được nhận diện.
- Công cụ `nvpmodel`, `jetson_clocks` và `tegrastats` có thể thu thập dữ liệu.
- Một idle baseline ngắn đã được ghi lại.

Các tệp hiện tại **không đủ** để đánh dấu E-09 là `COMPLETE` hoặc `PASS`. Trạng thái phù hợp là:

> **E-09 — PARTIAL / IN PROGRESS: Jetson environment pre-flight and idle baseline captured; sustained performance benchmark pending a runnable final GPU workload. No FPS, latency percentile, drop-rate, load-power or sustained-thermal claim is made.**

## Điều kiện để hoàn tất E-09

E-09 chỉ được cập nhật thành `COMPLETE` sau khi:

1. Đồng bộ source final, model production và model phụ trợ lên Jetson.
2. Khóa Git commit, dependency versions, JetPack/L4T, CUDA, cuDNN, TensorRT, ONNX Runtime/PyTorch, power mode, clocks, input resolution và stream count.
3. Xác nhận provider GPU thực sự hoạt động.
4. Hoàn tất warm-up và sustained run theo protocol E-09 trên một input/trip đã khóa.
5. Xuất `benchmark.csv`, `tegrastats.log` dưới tải và video; lưu kèm command line, thời gian chạy và mã thoát.

## SHA-256 của artifact gốc

| File | SHA-256 |
|---|---|
| `environment.json` | `5CC2837FE6565901092D2C9282F0CB94C671D5A223DCC8C102C675CEB4E18EEC` |
| `jetson_clocks.txt` | `69B72DBAC8E2C46563E08A165665AF553FF6FD072428CB17B6FB41332218AB2E` |
| `nvpmodel.txt` | `1F20E1C7CEB9D7D0C4376B4F25638F22F03E0C980BDBE9AB558BA0B6EBC5F064` |
| `tegrastats_idle.log` | `3B3D9C9061FBBC31B7E217DCBDB3ADA6F2B89C140F259F773C0AA6890238E2EE` |

