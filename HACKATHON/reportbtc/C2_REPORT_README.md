# FPTU DMS Vision — KPI và kế hoạch hoàn thiện Preview

## 1. KPI hiện tại so với mục tiêu đã đăng ký

| Nhóm KPI | Mục tiêu Proposal | Hiện tại | Trạng thái |
|---|---|---:|---|
| C1 TTC | Baseline Starter Kit + cải tiến; không chốt score | Composite **65,5/100**; MAE-critical **0,876 s**; F1 retest **69,9%** | Artifact F1 mới chờ đồng bộ |
| C2 Driver State | Tự xây; không chốt score | Practice composite retest **87,2/100** | Artifact mới chờ đồng bộ |
| C2 augmented holdout | Không chốt score | Accuracy **78,47%**; macro-F1 **80,28%** | Đã có model test report; không phải hidden test |
| C3 Safe Driving Risk | TTC + telemetry theo công thức BTC | **100/100** | Không kết luận hoàn hảo vì Safe Score prediction/GT cùng clip về 0 |
| Local warning | Trong **500 ms** | Chưa có p95 end-to-end | Chưa xác nhận đạt |
| Data-level latency | Khoảng **<50 ms** | Chưa có p95 delivery | Chưa xác nhận đạt |
| Product throughput | Realtime, không chốt FPS | Benchmark CPU ngắn **1,97 FPS** (~508 ms/frame) | Cần benchmark một trip đầy đủ |
| Unified pipeline | Driver + road + telemetry + Decision Engine | Đã nối end-to-end | Đạt MVP |
| Dashboard | Live Map + Alert Log + Analytics | Live data/multi-trip đạt MVP; analytics một phần | Một phần |
| Alert filtering | Đo false alarm và gate theo thời gian | Persistence/hysteresis/cooldown/lifecycle đã có; KPI false alarm chưa khóa | Một phần |
| CarSky local warning | Cảnh báo trên xe | Đến KUKSA/HMI Bridge; VHAL → APK còn blocked | Một phần |
| Offline-first | Queue + resync | Queue RAM, chưa persistent | Chưa đạt |
| Privacy | Event-only, không gửi video thô | Event chính + JPEG demo tần suất thấp | Một phần |
| Pi 5 + Hailo-8L | Có deployment | Chưa có evidence | Chưa đạt |
| Coaching/Copilot | Post-trip report | Prototype | Chưa đạt production |

> Kết quả hiện hành là C1 F1 **0,699** và C2 composite **87,2/100** từ lần
> retest mới nhất trên máy khác. Phải copy evaluation artifact mới vào repo
> trước khi khóa hồ sơ để số liệu có thể tái lập.

## 2. Kế hoạch hoàn thiện Preview

| Ưu tiên | Việc cần hoàn thành | Bằng chứng pass |
|---|---|---|
| P0 | Đồng bộ artifact retest | Evaluation JSON có C1 F1 `0,699`, C2 `87,2`; kèm model/config/checksum |
| P0 | Portable setup/run | Máy clone mới chạy không cần sửa ổ đĩa tuyệt đối |
| P0 | Rehearsal toàn luồng | Cùng `event_id` tại AI, Backend, Dashboard và CarSky |
| P0 | Đóng boundary Android HMI | APK nhận custom signal realtime hoặc có xác nhận platform/fallback rõ ràng |
| P0 | Benchmark chính thức | FPS trung bình, p95 AI/API delivery, CUDA/ORT provider trên một trip đầy đủ |
| P0 | Đo alert fatigue | Alert/session, lifecycle, cooldown và duplicate rejection |
| P0 | Khóa submission | CSV/schema/evaluation/checksum cho Practice và scored trips |
| P0 | Chuẩn bị backup | Video 5–7 phút, screenshot, JSONL, evaluation JSON; không lộ secret |
| P1 | Persistent outbox/history | Event retry đúng một lần và trip còn sau Backend restart |
| P1 | Chốt privacy | Event-only production; consent/retention cho JPEG demo |
| P1 | Cải thiện C1/C2 | Per-trip/confusion matrix, validation không leakage |
| P2 | Coaching và hardware | Report từ dữ liệu thật; benchmark Pi 5/Hailo-8L hoặc xác nhận đổi target |

