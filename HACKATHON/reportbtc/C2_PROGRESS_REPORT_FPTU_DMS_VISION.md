# FPTU DMS Vision — Báo cáo tiến độ C2

> Mốc giữa kỳ: 03/08/2026
> Căn cứ: yêu cầu BTC, proposal gốc, source code và artifacts hiện có.

## 01. Tóm tắt giải pháp

FPTU DMS Vision là nền tảng Risk Intelligence theo hướng edge-first. AI xử lý
road camera, driver camera và telemetry; Decision Engine chỉ gửi cảnh báo đã qua
quality gate, persistence và cooldown đến Fleet Dashboard và CarSky HMI.

```text
Road stereo → C1 TTC ───────────┐
Driver camera → C2 Driver State ├→ Decision Engine → FastAPI SE
Telemetry → C3 BTC Risk Score ──┘                     ├→ Fleet Dashboard
                                                      └→ CarSky → Android HMI
```

Hệ thống có hai nhánh độc lập:

1. **Submission:** BTC dataset → inference từng frame → CSV → evaluator.
2. **Product demo:** AI realtime/replay → DecisionEvent + live snapshot →
   Dashboard/CarSky; không dùng evaluator làm trung gian.

## 02. So sánh với proposal

| Cam kết | Hiện trạng C2 | Trạng thái |
|---|---|---|
| Driver camera + road stereo + telemetry | Unified AI runtime và hai mode demo | Implemented |
| Driver State tự xây | ONNX 468 landmarks + 59 causal features + RF v3 + safety fusion | Verified artifact |
| TTC Starter Kit có cải tiến | YOLOv8s, stereo/depth, tracking và temporal confirmation | Evaluated 6 practice trips |
| Unified Risk | C3 giữ công thức BTC; Decision Engine hợp nhất C1/C2/C3 phía sau | Implemented |
| Fleet Dashboard | Live frames, metrics, events và registry nhiều trip từ Backend | Implemented MVP |
| Local warning | DecisionEvent được map sang CarSky VSS/Android HMI | Implemented; cloud rehearsal required |
| Data-level decision | Event là contract chính; demo có gửi JPEG annotate 5 FPS | Partial so với privacy target |
| Offline-first | Queue RAM, chưa có persistent outbox | Partial |
| Pi 5/Hailo-8L | Chưa có bằng chứng triển khai | Not implemented |
| Coaching/Copilot | UI prototype | Prototype |

Challenge 3 của BTC không dùng Driver State. Context fusion cho sản phẩm nằm ở
Decision Engine sau C3 để không làm sai contract chấm bài.

## 03. Kiến trúc và luồng end-to-end

AI sở hữu `alert_type`, `severity`, `audiences`, evidence và lifecycle. Backend
chỉ validate, chống trùng, lưu theo `trip_id`, broadcast và map sang CarSky.

Product demo có hai mode:

- `hybrid-live`: road/telemetry BTC + webcam + optional personalized profile.
- `dataset-fleet`: tự quét mọi trip trong một folder, đăng ký tất cả trip nhưng
  inference tuần tự để giới hạn GPU/RAM.

Backend giữ riêng snapshot timeline, ảnh cuối và event của từng trip. Dashboard
hiển thị `pending/running/completed` và cho xem lại trip trước trong cùng phiên.
CSV/JSONL được lưu ra artifact; session history chưa persistent qua BE restart.

## 04. Kết quả đã hoàn thành

- **C1:** TTC từ hai road camera; output `inf` khi không đủ bằng chứng hợp lệ.
- **C2:** năm state `alert/drowsy/yawning/distracted/microsleep`; profile schema
  v3 dùng cho webcam, batch BTC dùng global model.
- **C3:** penalty từ TTC và telemetry theo công thức BTC; không trộn Driver State.
- **Decision Engine:** persistence, hysteresis, cooldown, compound risk và
  lifecycle. Không còn heartbeat mỗi giây; chỉ `open`, semantic `update` và
  `resolved`.
- **Backend/Dashboard:** live event, snapshot, cabin/road frame thật và registry
  nhiều trip; Frontend upsert theo `event_id` để tránh false-alarm duplication.
- **Runtime:** PyTorch CUDA và ONNX Runtime CUDA được khóa trong requirements;
  YuNet chạy thưa và tái sử dụng ROI trong product demo.

## 05. Demo tính năng cốt lõi

Demo chính dùng `hybrid-live`: BTC road cameras, webcam tài xế và personalized
profile. Chứng minh cùng một `event_id` tại AI JSONL, Backend recent API,
Dashboard và CarSky/HMI.

Demo phụ dùng `dataset-fleet`: thay một `-DataDir` để tự thêm dataset mới, quan
sát nhiều trip trên Dashboard và lịch sử còn lại khi chuyển trip.

Runbook: `reportbtc/C2_END_TO_END_DEMO_SCRIPT.md`.

## 06. KPI và số liệu ban đầu

### KPI AI submission

| KPI | Kết quả | Phạm vi |
|---|---:|---|
| C1 composite | 65.5/100 | 6 practice trips, 3.600 frames |
| C1 critical MAE | 0.876 s | 6 practice trips |
| C1 danger F1 | 0.539 | 6 practice trips |
| C2 composite | 87.2/100 | 6 practice trips |
| C2 augmented holdout accuracy | 0.7847 | 3.600 frames |
| C2 augmented holdout macro-F1 | 0.8028 | 5 classes |
| C3 evaluator | 100/100 | Không phân biệt tốt vì prediction và GT cùng clip safe score về 0 |

### KPI runtime/integration

| Kiểm tra | Kết quả C2 |
|---|---|
| YuNet interval 1 → 10 | 2.944 s → 1.932 s trên 30 frame; 30/30 face; landmark delta trung bình 0.001964 |
| Backend API regression | 13/13 tests pass |
| Frontend | Production build pass |
| Dataset discovery | Tự nhận đúng 6/6 Practice trips, không hard-code tên |
| Dataset-driver smoke test | End-to-end script xử lý thành công 3 frame |
| FPS end-to-end dài | Pending measurement trên rehearsal chính thức |

Số YuNet là benchmark phát triển ngắn, không đại diện latency toàn hệ thống.
Multi-rate chỉ áp dụng product demo: landmark/RF chạy mỗi frame webcam, YuNet
hiệu chỉnh mỗi 10 frame, C1 chạy nền theo interval và UI bỏ road frame quá cũ.
Nhánh CSV vẫn inference từng frame.

## 07. Khó khăn, rủi ro và hỗ trợ

- CarSky phụ thuộc room/node/token, Android ADB có thể đóng sau thời gian idle.
- Persistent outbox và Dashboard history qua Backend restart chưa có.
- Demo truyền JPEG cabin annotate để trực quan, chưa đạt hoàn toàn mục tiêu
  production “chỉ gửi kết luận”; cần policy consent/retention hoặc tắt media.
- C1 nặng; multi-rate giảm giật UI nhưng TTC có thể là giá trị cache trong lúc
  worker đang xử lý.
- C3 practice bị saturation nên cần diagnostic KPI ngoài composite.
- Cần BTC/mentor xác nhận hardware target và tiêu chí latency edge chính thức.

## 08. Kế hoạch đến Code Freeze

### P0

1. Rehearsal AI → SE → Dashboard → CarSky → HMI và quay video backup.
2. Benchmark FPS/latency dài trên đúng máy demo; ghi GPU provider và cấu hình.
3. Chạy 10 scored trips, validate schema CSV và khóa artifacts nộp bài.
4. Thêm persistent outbox hoặc mô tả rõ degraded behavior khi mất mạng.

### P1

1. Quyết định media policy: event-only production hoặc consent + retention.
2. Persist trip session/audit và delivery latency.
3. Cải thiện C1/C2 bằng validation không leakage; không tune theo hidden labels.

## 09. Phân công

| Thành viên | Trách nhiệm C2 |
|---|---|
| Đoàn Ngọc Nhân | Team Lead, FastAPI, CarSky và orchestration |
| Dương Thị Mỹ Tâm | Driver-state, KPI và Backend hỗ trợ |
| Phan Lê Thanh Hùng | AI runtime, Decision Engine, inference/evaluation |
| Trương Tô Dân | CarSky, HMI và embedded storyline |
| Nguyễn Trí Thiện | Dashboard, multi-trip UI và live presentation |

## Kết luận

Nhóm đã có ba challenge, Decision Engine và hai luồng demo chạy trên cùng
contract. Điểm còn phải chứng minh trước Code Freeze là latency dài hạn,
CarSky/HMI live rehearsal, persistent delivery và chính sách media phù hợp với
cam kết privacy của proposal.
