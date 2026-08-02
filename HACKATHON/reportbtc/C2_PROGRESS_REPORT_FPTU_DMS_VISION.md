# FPTU DMS Vision — Báo cáo tiến độ C2

> Tài liệu chuẩn bị cho mốc giữa kỳ C2 — hạn nộp 03/08/2026.  
> Nguồn tổng hợp: `reportbtc/README.md`, `reportbtc/readmeproposal.md`, README dự án, hiện trạng code AI/SE/CarSky/HMI trong repository.

---

## 01. Tóm tắt giải pháp

**FPTU DMS Vision** xây dựng nền tảng **Driver Intelligence Platform** cho bài toán DMS-10, tập trung vào việc hợp nhất tín hiệu từ tài xế, đường và telemetry để tạo ra một đánh giá rủi ro có thể hành động.

Thông điệp cốt lõi từ proposal:

> Tai nạn không bắt đầu bằng một cảnh báo đơn lẻ, mà bằng nhiều tín hiệu nguy hiểm bị nhìn riêng lẻ.

Vì vậy hệ thống không chỉ phát hiện từng event riêng biệt. Mục tiêu là chuyển từ:

```text
Event Monitoring
→ Risk Intelligence
→ Proactive Safety Action
```

Ba lớp chính của giải pháp:

```text
AI Road/TTC + AI Driver State + Telemetry
→ Risk Fusion
→ Fleet Dashboard + Driver HMI + CarSky/KUKSA signal
```

Đầu ra kỹ thuật chính:

- `predicted_ttc` cho Challenge 1.
- `predicted_driver_state` cho Challenge 2.
- `predicted_risk_score` cho Challenge 3.
- Fleet Dashboard để quản lý đội xe.
- HMI/CarSky để trình diễn cảnh báo realtime trên môi trường xe.
- Coaching/behavior report phục vụ quản lý hành vi lái xe.

Checklist BTC yêu cầu cho C2:

| Yêu cầu BTC | Cách nhóm chuẩn bị/demo |
|---|---|
| Demo tối đa 10 phút | Có script riêng `C2_END_TO_END_DEMO_SCRIPT.md`, chia timeline 0–10 phút |
| Chạy trên môi trường triển khai thực tế | Demo chạy bằng code AI/Backend/Frontend và CarSky/HMI thật; không chỉ slide/mockup |
| Bài toán và tính năng cốt lõi | Driver Intelligence: hợp nhất TTC + driver state + telemetry thành cảnh báo/risk score |
| Kiến trúc hoặc luồng xử lý chính | Trình bày luồng AI Challenge 1/2/3 → Backend/Fleet Dashboard → CarSky/KUKSA → HMI |
| Thành phần đã hoàn thành/đang phát triển | Có bảng trạng thái từng module ở phần 04 |
| Khó khăn, rủi ro, điểm cần hỗ trợ | Có phần 07, đặc biệt CarSky/KUKSA, KPI AI, TTS/audio và demo stability |
| KPI ban đầu | Có phần 06; các KPI chưa có log chính thức được đánh dấu là cần bổ sung, không nói quá |

---

## 02. Phạm vi cam kết trong proposal

Proposal ban đầu đăng ký hướng **DMS-10 — Driver Intelligence Platform** với các mục tiêu:

| Nhóm mục tiêu | Nội dung |
|---|---|
| Live Fleet Monitor | Theo dõi rủi ro chuyến đi/đội xe theo thời gian |
| Driver Behavior Analytics | Phân tích trạng thái và hành vi tài xế |
| Unified Risk Score | Hợp nhất TTC, driver state và telemetry thành điểm rủi ro |
| Fleet Dashboard | Dashboard điều hành, alert log, live view |
| Fleet AI Copilot | Chatbot hỗ trợ fleet manager hỏi nhanh về xe rủi ro, nguyên nhân và hành động đề xuất |
| Coaching Report | Báo cáo/khuyến nghị sau chuyến đi |
| Local Warning | Cảnh báo trực tiếp cho tài xế trên HMI |
| Data-level Decision | Chỉ gửi kết luận/signal, không gửi ảnh thô liên tục |

Luồng proposal:

```text
Driver Camera
Road Camera
Telemetry
    ↓
Feature Extraction
    ↓
Driver State + TTC
    ↓
Context Fusion / Risk Engine
    ↓
Local Warning + Fleet Dashboard + Coaching Report
```

Một số claim trong proposal như Pi 5 + Hailo-8L, MQTT/gRPC gateway, offline queue và production edge deployment đang được xem là **target/roadmap**, chưa mô tả như hoàn thành tại C2 nếu chưa có demo chạy thật.

---

## 03. Kiến trúc & luồng end-to-end hiện tại

Kiến trúc hiện tại trong repository:

```text
Challenge 1 — Road/TTC
  road stereo camera + telemetry
  → predicted_ttc

Challenge 2 — Driver State
  driver camera
  → predicted_driver_state + alertness

Challenge 3 — Risk Fusion
  predicted_ttc + predicted_driver_state + telemetry
  → predicted_risk_score

Backend
  → validate/cache/distribute
  → REST/WebSocket replay 20 FPS
  → CarSky/KUKSA signal adapter

Frontend Fleet Dashboard
  → fleet/risk/alert visualization

CarSky/HMI
  → KUKSA signal watch
  → Android HMI visual warning
  → simulated ECU reaction
```

Luồng demo C2 đề xuất:

```text
AI demo trip
→ CSV/AI result: TTC + Driver State + Risk
→ Backend/Fleet Dashboard replay
→ CarSky signal push
→ Android HMI đổi SAFE/WARNING/CRITICAL
→ Signal Watch chứng minh dữ liệu KUKSA đã update
```

---

## 04. Kết quả đã hoàn thành

### 4.1 AI Challenge 1 — Road/TTC

Đã có:

- `AI/core/challenge1_road/`
- YOLO/centroid tracking hoặc fallback.
- Stereo/depth estimation.
- TTC temporal engine.
- Looming TTC.
- Hold gap khi mất detection.
- `no_detection_floor`.
- Danger confirmation filter.
- Script inference CSV.
- Script đánh giá/tuning như `eval_practice.py`, `loto_postprocess.py`, `tune_output_map.py`.

Output mục tiêu:

```csv
frame_id,timestamp,predicted_ttc
```

Tình trạng:

- Foundation Challenge 1 đã tốt hơn bản đầu.
- Thành viên AI báo điểm đánh giá tăng.
- Cần log `AVERAGE COMPOSITE` để chốt KPI cụ thể.

### 4.2 AI Challenge 2 — Driver State

Đã có:

- `AI/core/challenge2_driver/`
- MediaPipe/DMS core.
- Feature extraction.
- Random Forest model artifact:

```text
AI/models/driver_state_rf_v2.joblib
AI/models/driver_state_rf_v2.manifest.yaml
```

State hợp lệ:

```text
alert | drowsy | yawning | distracted | microsleep
```

Đã có safety fusion:

- ML prediction.
- Override microsleep khi continuous eye closure đủ tin cậy.
- Alertness score.
- Eye/mouth/head pose primitive.

### 4.3 AI Challenge 3 — Risk Fusion

Đã có:

```text
AI/core/challenge3_fusion/risk_engine.py
```

Logic hiện tại:

- TTC hữu hạn → risk theo hàm exponential.
- Driver state có risk prior:
  - alert: 0
  - yawning: 30
  - drowsy: 50
  - distracted: 60
  - microsleep: 90
- Final risk = max(TTC risk, driver state risk).

Đây là bản deterministic, dễ giải thích, phù hợp MVP C2.

### 4.4 AI demo trip ba camera

Đã có:

```text
AI/demo_trips/T_test_01/
AI/scripts/trip_visual_demo.py
```

Demo visual hiển thị:

- Road-left Challenge 1.
- Road-right stereo reference.
- Face camera Challenge 2.
- Fusion dashboard Challenge 3.

Có thể xuất:

- Video demo.
- CSV output theo contract BTC.

### 4.5 Backend

Đã có FastAPI Backend:

- `GET /health`
- `GET /ready`
- REST prefix `/api/v1`
- WebSocket replay:

```text
WS /ws/replay/{trip_id}
```

Các module đã có:

- Fleet.
- Event detection.
- Risk fusion.
- Insurance.
- Coaching.
- Streaming replay.
- CarSky integration.

Backend giữ nguyên quyết định dự án:

- Không authentication/authorization trong demo.
- Credential CarSky/AI/LLM chỉ dùng outbound integration.

### 4.6 Fleet Dashboard / Frontend

Đã có frontend trong:

```text
SE/FE/
```

Mục tiêu hiển thị:

- Fleet overview.
- Risk/alert state.
- Replay/demo view.
- Dashboard cho quản lý đội xe.
- Fleet AI Copilot để fleet manager hỏi nhanh:
  - Xe nào đang nguy hiểm nhất?
  - Vì sao risk tăng?
  - Tài xế đang ở trạng thái gì?
  - Hành động đề xuất là gì?
  - Có nên ưu tiên can thiệp xe/chuyến nào trước?

Frontend hiện là phần cần tiếp tục polish và nối dữ liệu demo end-to-end. **Fleet AI Copilot là feature nhóm cam kết triển khai từ C2 đến Code Freeze**, ưu tiên trước mắt là chatbot dạng rule/RAG nhẹ dựa trên dữ liệu trip/risk/alert hiện có; nếu đủ thời gian sẽ nối LLM API để trả lời tự nhiên hơn.

### 4.7 CarSky/KUKSA/HMI

Đã đạt được:

- CarSky deployment từng đạt trạng thái `Running 3/3`.
- KUKSA Broker chạy được sau khi sửa VSS artifact từ array sang object/map.
- Signal Watch thấy DMS signals.
- Script gửi signal lên CarSky từng trả:

```json
{"ok": true, "sent": 14}
```

- Android HMI APK cài được qua CarSky ADB widget.
- HMI hiển thị các state:
  - SAFE
  - WARNING
  - CRITICAL
- HMI hiển thị:
  - AI status.
  - Driver state.
  - Speed.
  - Risk.
  - Alertness.
  - TTC.
  - Recommended action.
  - Simulated ECU action.

Ví dụ critical:

```text
Vehicle.ADAS.DisplaySeverity = CRITICAL
Vehicle.ADAS.RecommendedActionCode = BRAKE_SAFE
Vehicle.ADAS.CriticalAlert = true
Vehicle.Driver.State = microsleep
Vehicle.ADAS.FinalRiskScore = 88
```

---

## 05. Demo tính năng cốt lõi

Demo C2 nên trình bày theo storyline:

> Một tình huống nguy hiểm không được quyết định bởi một tín hiệu đơn lẻ. Hệ thống của nhóm hợp nhất TTC, driver state và telemetry để tạo risk score, sau đó hiển thị lên Fleet Dashboard và HMI trong xe.

Kịch bản demo chính:

1. Mở AI trip visual demo.
2. Cho thấy Challenge 1 đang tính TTC từ road camera.
3. Cho thấy Challenge 2 đang phân loại driver state từ face camera.
4. Cho thấy Challenge 3 fusion ra risk score.
5. Mở Fleet Dashboard để show góc nhìn Fleet Manager.
6. Mở CarSky Android HMI để show góc nhìn Driver.
7. Gửi mock/realtime signal critical lên CarSky.
8. HMI đổi sang cảnh báo.
9. Signal Watch chứng minh KUKSA signal đã update.
10. Kết luận: cùng một risk intelligence được dùng cho cả quản lý đội xe và cockpit/HMI.

File thao tác chi tiết:

```text
reportbtc/C2_END_TO_END_DEMO_SCRIPT.md
```

---

## 06. KPI & số liệu ban đầu

| KPI BTC yêu cầu | Trạng thái hiện tại | Cách đo/ghi chú cho C2 |
|---|---|---|
| Độ chính xác mô hình | Challenge 1/2 đã có pipeline và model; cần log chính thức | Challenge 1 lấy `AVERAGE COMPOSITE`; Challenge 2 lấy accuracy/F1 từ validation |
| Tỷ lệ phát hiện đúng/sai | Có thể đo từ output TTC và driver state | Cần báo TP/FP/FN cho các trạng thái nguy hiểm: distracted, drowsy, microsleep, TTC critical |
| Khả năng xử lý end-to-end | Đã chứng minh được luồng AI → signal → HMI bằng demo CarSky | Demo trực tiếp: send signal thành công và HMI đổi SAFE/WARNING/CRITICAL |
| Thời gian xử lý / độ trễ | Chưa chốt số đo chính thức | Cần đo latency theo từng đoạn: AI inference, Backend replay, CarSky push, HMI update |
| Mức độ hoàn thiện dữ liệu | Có sample trip, output CSV/JSON, KUKSA VSS map | Cần chốt dataset/cache đủ case demo và file submission theo format BTC |
| KPI kỹ thuật đặc thù | Backend có health/readiness, WebSocket 20 FPS, CarSky Running 3/3 | Có thể show `/health`, `/docs`, Signal Watch và HMI live |
| KPI nghiệp vụ đặc thù | Risk score giải thích được theo TTC + driver state | Có thể giải thích vì sao hệ thống đề xuất `FOCUS_FORWARD`, `REDUCE_SPEED`, `BRAKE_SAFE` |

Chi tiết theo module:

| Hạng mục | Trạng thái hiện tại | KPI/ghi chú |
|---|---|---|
| Challenge 1 TTC | Đã có pipeline + tuning mới | Cần log `eval_practice.py` để chốt điểm cụ thể |
| Challenge 2 Driver State | Đã có RF v2 + safety fusion | Cần team AI cung cấp accuracy/F1 theo validation |
| Challenge 3 Risk Fusion | Có deterministic rule/model đơn giản | Explainable, phù hợp MVP |
| Backend health/readiness | Có endpoint | Health chạy được; readiness phụ thuộc dataset/cache |
| WebSocket replay | Có endpoint 20 FPS | Cần dữ liệu/case demo ổn định để show |
| CarSky/KUKSA | Đã chạy được Running 3/3 | Signal push mock đã verify |
| HMI visual warning | Đã cài APK và đổi state | Voice phụ thuộc TTS engine của Android VM |
| Fleet Dashboard | Có frontend | Cần polish và đảm bảo data demo |

KPI nên bổ sung trước khi nộp:

- Challenge 1 `AVERAGE COMPOSITE`.
- Challenge 2 accuracy/F1 per class.
- End-to-end latency ước lượng:
  - AI inference/demo frame.
  - Backend replay.
  - CarSky signal update.
  - HMI visual update.
- Tỷ lệ trạng thái CarSky demo thành công.

---

## 07. Khó khăn, rủi ro & hỗ trợ cần BTC/mentor

### 7.1 CarSky/KUKSA VSS artifact

Đã từng gặp lỗi:

```text
ParseError("invalid type: sequence, expected a map at line 1 column 1")
```

Nguyên nhân:

- KUKSA yêu cầu VSS artifact dạng object/map.
- Artifact dạng array không deploy được.

Đã xử lý:

- Sửa `dms-vss-signals.json` về dạng object/map.
- Deployment đạt Running 3/3.

### 7.2 Custom Android VHAL không expose DMS property

Đã kiểm tra Android Car Service chỉ expose property chuẩn như speed, custom DMS property chưa ổn định qua `CarPropertyManager`.

Hướng demo hiện tại:

- HMI đọc CarSky/KUKSA REST values hoặc mock fallback.
- Không phụ thuộc custom Android VHAL cho C2.

### 7.3 TTS/voice trên Android VM

Android VM hiện có thể không có TTS engine:

```text
tts_default_synth = null
```

Do đó:

- Visual critical alert là bắt buộc.
- Voice là optional/nice-to-have.

### 7.4 Dependency/dataset

AI inference cần:

- OpenCV.
- Ultralytics/torch nếu dùng YOLO.
- MediaPipe/joblib/yaml.
- Dataset đúng cấu trúc BTC.

Nếu thiếu YOLO, Challenge 1 vẫn có fallback nhưng chất lượng có thể thấp hơn.

### 7.5 Rủi ro demo live

CarSky hoặc ADB có thể không ổn định. Cần chuẩn bị:

- Video demo AI trip.
- Screenshot HMI Safe/Warning/Critical.
- Signal Watch evidence.
- CSV output sample.

---

## 08. Kế hoạch từ C2 đến Code Freeze

Ưu tiên 1 — Chốt output nộp bài:

1. Chốt Challenge 1 score log.
2. Chốt Challenge 2 validation metrics.
3. Chốt Challenge 3 fusion rule/model.
4. Sinh full CSV:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

5. Validate đủ trip/frame/column.

Ưu tiên 2 — Demo end-to-end:

1. Chuẩn hóa demo trip.
2. Chuẩn hóa Fleet Dashboard view.
3. Bổ sung Fleet AI Copilot trong dashboard.
4. Chuẩn hóa CarSky/HMI state.
5. Viết script chạy một lệnh cho demo.
6. Chuẩn bị video backup.

Ưu tiên 3 — Polish:

1. Improve UI/UX HMI.
2. Improve Fleet Dashboard presentation.
3. Hoàn thiện prompt/response template cho Fleet AI Copilot.
4. Coaching report text.
5. Documentation/usage notes.

Ưu tiên 4 — Risk mitigation:

1. Không deploy lại CarSky/VSS nếu bản demo đang chạy ổn.
2. Không đổi contract AI/Backend sát giờ.
3. Không thêm framework APK lạ chưa test trên CarSky.

---

## 09. Phân công nhiệm vụ trong đội

| Thành viên | Vai trò proposal | Trọng tâm C2 |
|---|---|---|
| Đoàn Ngọc Nhân | Team Lead, Backend | Backend, CarSky adapter, HMI integration, demo orchestration |
| Dương Thị Mỹ Tâm | AI & Backend | Challenge 2/AI validation, hỗ trợ integration |
| Phan Lê Thanh Hùng | AI & Backend | Challenge 1 TTC, Challenge 3 fusion, CSV output |
| Trương Tô Dân | IoT & Embedded | CarSky/HMI/ECU storyline, cockpit integration evidence |
| Nguyễn Trí Thiện | Frontend & UI/UX | Fleet Dashboard, HMI visual design, demo presentation |

---

## 10. Kết luận C2

Tại mốc C2, nhóm đã chuyển proposal từ ý tưởng thành một pipeline có các thành phần chạy được:

- AI Challenge 1/2/3 có code runtime.
- Backend có REST/WebSocket/module foundation.
- Fleet Dashboard có frontend foundation.
- CarSky/KUKSA/HMI đã chứng minh được signal update và visual warning.

Điểm mạnh để trình bày với BTC:

- Không chỉ nộp model AI rời rạc.
- Có câu chuyện end-to-end từ AI inference đến Fleet Dashboard và cockpit HMI.
- Có risk fusion explainable.
- Có CarSky/KUKSA integration thật để chứng minh hướng connected car.

Điểm cần hoàn thiện:

- Chốt KPI định lượng chính thức.
- Chuẩn hóa demo script.
- Polish dashboard/HMI.
- Đảm bảo full CSV submission khi BTC/Challenge data đầy đủ.
