# FPTU DMS Vision — Báo cáo tiến độ C2

> Mốc giữa kỳ: 03/08/2026
> Căn cứ: yêu cầu trong `reportbtc/README.md`, cam kết proposal trong
> `reportbtc/readmeproposal.md`, executable code và artifacts hiện có.

## 01. Tóm tắt giải pháp

FPTU DMS Vision giải bài toán DMS-10 bằng kiến trúc edge-first: xử lý road
camera, driver camera và telemetry tại AI runtime; chỉ gửi prediction/event nhẹ
sang Backend, Fleet Dashboard và CarSky HMI. Mục tiêu là chuyển từ cảnh báo tín
hiệu đơn lẻ sang cảnh báo có ngữ cảnh, giải thích được và có hành động cụ thể.

```text
Road stereo → TTC ───────────────┐
Driver camera → Driver State ────┼→ Decision Engine → SE → Dashboard/CarSky
Telemetry → BTC Safe/Risk Score ─┘
```

Hệ thống có hai nhánh độc lập:

1. **Submission:** dataset BTC → inference C1/C2/C3 → CSV → evaluator.
2. **Product demo:** road/telemetry BTC + webcam tài xế → DecisionEvent →
   FastAPI SE → live Dashboard + CarSky VSS → Android HMI.

Không dùng output evaluate làm input demo và không dùng mock CarSky để tuyên bố
AI end-to-end đã chạy.

## 02. So sánh với cam kết proposal

| Cam kết proposal | Hiện trạng kiểm chứng | Trạng thái C2 |
|---|---|---|
| Driver camera + road stereo + telemetry | Có unified AI runtime và hybrid demo webcam/BTC | Implemented |
| Driver-state tự xây | ONNX 468 landmarks + 59 features + RF v3 + safety fusion | Verified bằng test artifact |
| TTC từ Starter Kit, có cải tiến | YOLOv8s + stereo/depth + TTC temporal policy | Verified trên 6 practice trip |
| Context fusion / unified risk | BTC C3 giữ đúng behavior penalty; Decision Engine mới hợp nhất C1/C2/C3 để cảnh báo | Implemented |
| Chỉ gửi kết luận, không gửi video cabin | AI gửi canonical DecisionEvent; không gửi webcam frame sang SE | Verified theo contract |
| Fleet Dashboard | UI nền dùng mock trip; panel Decision Engine nhận WebSocket live | Partial |
| Local warning / CarSky HMI | BE map DecisionEvent sang 14 VSS paths và enqueue CarSky | Implemented; cloud live cần rehearsal |
| Offline-first queue | Publisher có bounded queue trong RAM; chưa có persistent outbox khi mất mạng/restart | Partial |
| Pi 5 + Hailo-8L | Chưa có bằng chứng triển khai trong repo | Not implemented |
| Latency dưới 500 ms / 50 ms | CPU-only benchmark mới khoảng 507 ms/frame sau warm-up | Chưa đạt ổn định |
| Coaching report / Copilot | UI/Copilot prototype; chưa phải KPI production | Prototype |

Điểm khác so với proposal cần nói rõ: Challenge 3 của BTC **không dùng driver
state**. Context fusion C1+C2+C3 nằm ở Decision Engine phía sau CSV, tránh sửa
công thức chấm bài.

## 03. Kiến trúc end-to-end hiện tại

```text
ON-VEHICLE / AI
  BTC road-left/right + telemetry
  live webcam + optional driver profile
       │
       ├─ C1 predicted_ttc
       ├─ C2 predicted_driver_state
       ├─ C3 predicted_risk_score (BTC penalty)
       └─ DecisionEvent(open/update/resolved)
                         │ HTTP POST + Idempotency-Key
                         ▼
BACKEND SE / FastAPI
  validate → deduplicate → store recent → WebSocket broadcast
                                   └→ CarSkyMapper → async publisher
                          │                      │
                          ▼                      ▼
                    Fleet Dashboard       CarSky Signals API
                                               │
                                               ▼
                                         Android HMI
```

AI sở hữu `alert_type`, `severity`, `audiences`, evidence và lifecycle. Backend
không tính lại quyết định; chỉ validate, deduplicate, translate sang VSS và phân
phối.

## 04. Kết quả đã hoàn thành

### 4.1 Challenge 1 — TTC

- Hai road camera, YOLOv8s, tracking, stereo/depth và TTC temporal processing.
- Output `predicted_ttc`, `inf` khi không đủ nguy cơ hợp lệ.
- Sáu CSV practice hiện có và đã evaluate bằng `AI/team_kit/evaluation.py`.

### 4.2 Challenge 2 — Driver State

- Python 3.13 ONNX pipeline: YuNet + 468 landmarks.
- 59 causal features, Random Forest v3 và continuous-eye-closure safety fusion.
- Năm state: `alert`, `drowsy`, `yawning`, `distracted`, `microsleep`.
- Personalized driver profile schema v3 cho webcam; batch BTC luôn dùng global
  model vì không có enrollment.

### 4.3 Challenge 3 — BTC Safe Driving Score

- Dùng TTC C1 và telemetry để tính harsh brake/accel/corner, near miss và
  speeding theo đúng công thức BTC.
- Không trộn driver state vào C3.
- `predicted_risk_score` là penalty tích lũy; safe score cuối trip bằng
  `100 - final penalty`.

### 4.4 Decision Engine

- Temporal quality gates và lifecycle `open/update/resolved`.
- Cảnh báo TTC, microsleep, distraction, drowsiness, speeding, repeated harsh
  behavior và sensor health.
- Canonical JSON event, idempotency key, audience riêng cho driver/fleet.

### 4.5 Backend, Dashboard và CarSky

- `POST /api/v1/alerts`: validate và chống duplicate.
- `GET /api/v1/alerts/recent`: xem event gần nhất.
- `WS /api/v1/alerts/live`: broadcast canonical event cho Dashboard.
- Event có `driver_display` được map sang VSS và enqueue CarSkyPublisher.
- Dashboard có panel live riêng; phần fleet/map/trip nền vẫn là prototype/mock.
- Android HMI đọc `DisplaySeverity`, `RecommendedActionCode` và signal liên quan
  từ CarSky.

## 05. Kịch bản demo cốt lõi

Demo thật phải dùng một event do AI tạo, không dùng `scenario critical` làm proof
chính:

1. Mở CarSky Signal Watch và Android HMI.
2. Chạy Backend với `CARSKY_ENABLED=true`.
3. Chạy Frontend; panel báo `LIVE`.
4. Chạy `AI/scripts/end_to_end_demo.py` với road BTC và webcam.
5. Tạo hành vi hợp lệ hoặc dùng một trip/đoạn đã biết sinh alert.
6. Chỉ vào cùng `event_id/alert_type` tại AI log, Backend recent API, Dashboard
   live panel và VSS/HMI.

Script thao tác chi tiết: `reportbtc/C2_END_TO_END_DEMO_SCRIPT.md`.

## 06. KPI ban đầu

### KPI AI

| KPI | Kết quả hiện có | Phạm vi/giới hạn |
|---|---:|---|
| C1 overall composite | 65.5/100 | 6 practice trips, 3.600 frames |
| C1 critical MAE | 0.876 s | 6 practice trips |
| C1 danger F1 | 0.539 | 6 practice trips |
| C2 practice composite | 87.2/100 | 6 practice trips; label distribution theo trip không cân bằng |
| C2 augmented holdout accuracy | 0.7847 | 3.600 augmented test frames |
| C2 augmented holdout macro-F1 | 0.8028 | 5 classes |
| C3 evaluator | 100/100 | **Không đủ sức phân biệt:** predicted và GT safe score đều bão hòa 0 ở cả 6 trip |

Không dùng C3 `100/100` để khẳng định mô hình hoàn hảo. Kết quả xuất hiện do
penalty của cả prediction lẫn ground truth vượt 100, khiến safe score cùng clip
về 0.

### KPI latency

Benchmark CPU-only trên 8 frame T01-Sample:

| Thành phần | Trước tối ưu |
|---|---:|
| Image I/O | 5.7 ms/frame |
| C1 | 417.9 ms/frame |
| C2 | 474.5 ms/frame |
| Pipeline tuần tự | khoảng 1.11 FPS |
| C1/C2 parallel + thread tuning | khoảng 1.97 FPS, ~507 ms/frame |

Máy có RTX 4060 nhưng môi trường hiện từng cài `torch+cpu` và `onnxruntime` CPU;
GPU migration cần được verify trước khi dùng latency làm KPI chính thức.

### KPI integration

| Boundary | Hiện trạng |
|---|---|
| AI event → BE validation/idempotency | Contract test pass |
| BE → Dashboard WebSocket | Implemented; cần browser rehearsal |
| BE event → CarSky mapper/queue | Unit/contract path implemented |
| CarSky cloud → Android HMI | Có artifact/runbook; trạng thái live phụ thuộc deployment/credential |

## 07. Khó khăn, rủi ro và hỗ trợ

- GPU packages chưa được khóa đúng trong requirements; CPU không đạt realtime.
- CarSky là external runtime, phụ thuộc room/node/token và deployment `Running`.
- Persistent offline outbox chưa có; queue hiện mất khi Backend restart.
- Dashboard vẫn dùng mock trip cho fleet/map, chỉ live alert panel là dữ liệu thật.
- C3 score practice bị saturation, cần thêm diagnostic KPI thay vì chỉ composite.
- Webcam demo phụ thuộc enrollment hợp lệ và hành vi thực tế đủ temporal gate.

Hỗ trợ cần BTC/mentor: xác nhận hardware target, tiêu chí latency edge, cách đánh
giá C3 khi safe score bão hòa và quyền truy cập CarSky ổn định trước demo.

## 08. Kế hoạch đến Code Freeze

### P0

1. Khóa GPU environment và benchmark lại C1/C2/end-to-end latency.
2. Chạy rehearsal thật AI → BE → Dashboard → CarSky → HMI và lưu evidence.
3. Kiểm tra 10 scored trips, validate CSV và chuẩn bị backup video.
4. Thêm persistent outbox hoặc ghi rõ degraded behavior khi CarSky mất mạng.

### P1

1. Cho Dashboard dùng thêm Backend trip/replay thay vì chỉ mock background.
2. Thêm delivery status/latency vào audit log và Dashboard.
3. Cải thiện C1 T01/T02 và C2 distracted/drowsy theo validation không leakage.

### Không tuyên bố hoàn thành ở C2

- Pi 5/Hailo deployment.
- Production authentication/rate limiting.
- Offline persistence qua restart.
- Copilot production quality.
- Hidden test performance.

## 09. Phân công

| Thành viên | Vai trò theo proposal | Trách nhiệm C2 |
|---|---|---|
| Đoàn Ngọc Nhân | Team Lead, Backend | FastAPI, CarSky adapter, orchestration |
| Dương Thị Mỹ Tâm | AI & Backend | Driver-state/KPI/integration hỗ trợ |
| Phan Lê Thanh Hùng | AI & Backend | AI runtime, Decision Engine, CSV/evaluation |
| Trương Tô Dân | IoT & Embedded | CarSky/HMI/ECU storyline |
| Nguyễn Trí Thiện | Frontend & UI/UX | Dashboard, live alert presentation |

## Kết luận

Nhóm đã có AI runtime ba challenge, Decision Engine và executable integration
boundary. Điểm cần phân biệt trung thực là: submission pipeline đã có artifact
và evaluator; product demo đã có code nối thật nhưng CarSky cloud/browser cần
rehearsal live trước khi đánh dấu Verified. Mục tiêu trước Code Freeze là chứng
minh một canonical event đi xuyên suốt toàn chuỗi, đo latency thật và giữ backup
evidence cho external runtime.
