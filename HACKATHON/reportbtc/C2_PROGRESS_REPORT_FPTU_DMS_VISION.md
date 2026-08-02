# FPTU DMS Vision — KPI và kế hoạch hoàn thiện Preview

## 1. KPI hiện tại so với mục tiêu đã đăng ký

| Nhóm KPI | Mục tiêu đã đăng ký trong Proposal | Kết quả hiện tại | Đánh giá |
|---|---|---:|---|
| C1 — TTC | Dùng TTC baseline Starter Kit và cải tiến; Proposal không chốt score | Composite **65,5/100**; critical MAE **0,876 s**; danger F1 retest **69,9%** | Đã có kết quả Practice; F1 mới retest trên máy khác, artifact đang chờ đồng bộ |
| C2 — Driver State | Driver-state tự xây; Proposal không chốt score | Practice composite retest **87,2/100** | Đạt MVP; artifact retest đang chờ đồng bộ |
| C2 — Augmented holdout | Proposal không chốt score | Accuracy **78,47%**; macro-F1 **80,28%** trên 3.600 frame/5 class | Có model test report; không phải hidden BTC test |
| C3 — Safe Driving Risk | Hợp nhất TTC và telemetry theo công thức BTC | Evaluator **100/100** | Không dùng để kết luận hoàn hảo vì prediction và GT cùng bị clip Safe Score về 0 trên 6 Practice trips |
| Local warning latency | Cảnh báo cục bộ trong **500 ms** | Chưa có p95 end-to-end chính thức | Chưa đủ bằng chứng đạt target |
| Data-level latency | Xử lý/gửi dữ liệu tóm tắt khoảng **dưới 50 ms** | Chưa có p95 AI → Backend → consumer | Chưa đủ bằng chứng đạt target |
| Runtime throughput | Realtime; Proposal không chốt FPS | Benchmark CPU ngắn khoảng **1,97 FPS** (~508 ms/frame) | Chưa đại diện một trip đầy đủ hoặc máy GPU demo |
| YuNet optimization | Proposal không đặt target riêng | 30 frame: **2,944 s → 1,932 s** khi interval 1 → 10; face 30/30 | Benchmark thành phần, không phải latency toàn pipeline |
| Input và Context Fusion | Driver Camera + Road Camera + Telemetry → Unified Risk | C1/C2/C3 và Decision Engine đã nối trong product pipeline | Đạt MVP |
| Fleet Dashboard | Live Map, Alert Log và Behavior Analytics | Live frame/metric/event và multi-trip registry; analytics còn một phần | Đạt MVP một phần |
| Alert quality | Đo false alarm; chỉ gửi alert đủ thời gian/ngữ cảnh | Có persistence, hysteresis, cooldown và lifecycle `open/update/resolved`; chưa khóa false-alert/session | Một phần |
| Local warning/CarSky | Cảnh báo tại xe | REST → KUKSA → HMI Bridge đã xác minh; VHAL → Android APK còn bị chặn | Một phần |
| Offline-first | Queue và tự đồng bộ sau khi có mạng | Queue RAM; chưa có persistent outbox qua restart | Chưa đạt |
| Privacy/data-level decision | Chỉ gửi kết luận, không gửi video thô | Event là contract chính; demo vẫn gửi JPEG annotate tần suất thấp | Một phần |
| Hardware edge | Raspberry Pi 5 + Hailo-8L | Chưa có deployment/benchmark artifact | Chưa đạt |
| Coaching Report/Copilot | Báo cáo tự động sau chuyến | UI prototype | Chưa đạt production |
| Software regression | Proposal không chốt số test | Lần xác minh gần nhất: Backend 13/13 test pass; Frontend production build pass | Cần lưu log test/build cùng hồ sơ cuối |
| Dataset coverage | Practice và scored dataset | 6/6 Practice trips; scored-trip validation chưa khóa | Một phần |

> **Nguồn và giới hạn:** C1 F1 `69,9%` và C2 composite `87,2/100` là kết quả
> retest mới nhất trên máy khác. File evaluation mới phải được đồng bộ vào repo
> trước khi khóa hồ sơ. Artifact đang có trong repo vẫn là snapshot cũ. C2
> augmented holdout lấy từ
> `AI/models/driver_state_rf_v3_onnx_test_report.json` và không được trộn với
> Practice evaluation.

## 2. Kế hoạch hoàn thiện Preview

| Ưu tiên | Công việc | Điều kiện hoàn thành/bằng chứng |
|---|---|---|
| P0 | Đồng bộ evaluation artifact mới | JSON trong repo phải thể hiện C1 F1 **0,699** và C2 composite **87,2**; lưu command, model/config version và checksum |
| P0 | Chuẩn hóa chạy đa máy | Không hard-code ổ đĩa; dùng `$PSScriptRoot`/Git root, `.venv` trong repo và truyền `-TripDir`/`-DataDir` |
| P0 | Rehearsal AI → Decision Engine → Backend → Dashboard → CarSky | Cùng `event_id`, severity và action xuất hiện tại AI JSONL, Backend, Dashboard và CarSky Signal Watch |
| P0 | Hoàn thiện CarSky Android HMI | Custom DMS signal đi qua VHAL/CarProperty và APK đổi trạng thái realtime; nếu platform chặn phải có xác nhận kỹ thuật và phương án fallback trung thực |
| P0 | Đo latency/FPS chính thức | Chạy ít nhất một trip đầy đủ trên đúng máy demo; lưu FPS trung bình, p95 AI latency, p95 delivery latency, GPU/ORT provider và cấu hình máy |
| P0 | Đo false alarm/alert fatigue | Lưu alert/session, `open/update/resolved`, duplicate bị chặn, cooldown và số cảnh báo thực sự gửi Dashboard/HMI |
| P0 | Khóa submission | Chạy Practice và scored trips, validate CSV/schema, lưu evaluation JSON, model/config checksum và prediction artifacts |
| P0 | Chuẩn bị Preview dự phòng | Video 5–7 phút, screenshot Dashboard/CarSky, JSONL và evaluation JSON; không lộ `.env`, token hoặc driver profile |
| P1 | Persistent offline outbox | Tắt mạng, sinh event, bật lại và chứng minh event được gửi đúng một lần sau restart |
| P1 | Persist lịch sử Dashboard | Trip/session/audit vẫn còn sau Backend restart |
| P1 | Chốt media/privacy policy | Production dùng event-only; JPEG demo phải có consent, retention và tùy chọn tắt |
| P1 | Cải thiện C1/C2 | Báo cáo per-trip/confusion matrix, validation không leakage và không tune theo hidden labels |
| P2 | Coaching Report/Copilot | Sinh ít nhất một báo cáo sau chuyến từ event và telemetry thật, không dùng dữ liệu mock |
| P2 | Hardware target | Benchmark trên Pi 5 + Hailo-8L hoặc có xác nhận thay đổi hardware target từ BTC |

