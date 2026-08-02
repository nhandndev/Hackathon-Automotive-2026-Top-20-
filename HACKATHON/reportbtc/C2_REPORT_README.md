# README báo cáo tiến độ C2 — FPTU DMS Vision

> Mục đích: file này dùng để chuẩn bị **Progress Report** nộp BTC tại mốc **C2 · Giữa kỳ**.  
> File này **không phải script thực hành demo end-to-end**. Phần thao tác demo đã tách riêng ở `C2_END_TO_END_DEMO_SCRIPT.md`.

---

## 01. Mục tiêu của báo cáo C2

Báo cáo C2 cần chứng minh 4 điểm:

1. Nhóm đang giải quyết đúng bài toán đã đăng ký trong proposal.
2. Giải pháp đã có tiến độ thực tế, không chỉ là slide/mockup.
3. Các module chính đã có kết quả ban đầu và có thể kết nối thành luồng **end-to-end**.
4. Nhóm hiểu rõ phần còn thiếu, rủi ro, KPI cần đo và kế hoạch đến **Code Freeze**.

Thông điệp chính nên giữ xuyên suốt:

> FPTU DMS Vision không chỉ phát hiện từng event riêng lẻ. Hệ thống hợp nhất **TTC**, **Driver State** và **Telemetry** thành **Unified Risk Score**, sau đó đưa kết quả đến **Fleet Dashboard**, **Fleet AI Copilot**, **CarSky/KUKSA** và **Android HMI**.

---

## 02. Hồ sơ cần nộp cho BTC

Theo yêu cầu BTC, nhóm cần chuẩn bị:

| Hạng mục | Trạng thái cần có | Ghi chú |
|---|---|---|
| Progress Report | PDF, HTML hoặc slide | Nội dung lấy từ `C2_PROGRESS_REPORT_FPTU_DMS_VISION.md` |
| Video Demo | Tối đa 10 phút | Quay lại luồng cốt lõi, không cần đưa toàn bộ thao tác vào report |
| Repository Link | Link GitHub | Đảm bảo `.gitignore` không đẩy `.venv`, `node_modules`, `.env`, `.DS_Store` |
| Build/Demo Environment | Nếu có | Ghi rõ Backend/Frontend/AI/CarSky chạy ở môi trường nào |
| KPI Table | Số liệu hiện tại so với proposal | Nếu KPI chưa đủ, ghi `Pending measurement` thay vì đoán |
| Remaining Plan | Kế hoạch từ C2 đến Code Freeze | Tách rõ việc chắc chắn làm và việc optional |

---

## 03. Cấu trúc báo cáo đề xuất

Báo cáo nên đi theo đúng 9 mục BTC đề xuất.

### 03.1 Tóm tắt giải pháp

Nội dung cần có:

- Tên giải pháp: **FPTU DMS Vision**.
- Track/bài toán: **DMS-10 · Driver Intelligence Platform**.
- Insight chính: tai nạn thường đến từ nhiều tín hiệu rủi ro nhỏ tích lũy.
- Tính năng cốt lõi: **Risk Intelligence** cho tài xế và fleet manager.

Keyword nên dùng:

```text
Driver Monitoring System
TTC Estimation
Driver State Recognition
Risk Fusion
Fleet Dashboard
Fleet AI Copilot
CarSky
KUKSA
Android HMI
```

### 03.2 Phạm vi cam kết trong proposal

Nội dung cần có:

- **Live Fleet Monitor**.
- **Driver Behavior Analytics**.
- **Unified Risk Score**.
- **Fleet Dashboard**.
- **Fleet AI Copilot**.
- **Coaching Report**.
- **Local Warning** trên HMI.
- Hướng **Data-level Decision**, không gửi raw video liên tục.

Lưu ý cách viết:

- Phần đã chạy được thì ghi là `Completed / Verified`.
- Phần đang làm thì ghi là `In Progress`.
- Phần là định hướng sau C2 thì ghi là `Planned before Code Freeze` hoặc `Roadmap`.

Không nên viết Pi/Hailo/MQTT/offline queue là hoàn thành nếu chưa có bằng chứng demo thật.

### 03.3 Kiến trúc & luồng end-to-end

Mô tả bằng flow:

```text
Road Camera / Stereo / Depth
  → Challenge 1: TTC Estimation

Driver Camera
  → Challenge 2: Driver State Recognition

Telemetry
  → Vehicle Context

TTC + Driver State + Telemetry
  → Challenge 3: Risk Fusion
  → Backend API / WebSocket Replay
  → Fleet Dashboard / Fleet AI Copilot
  → CarSky KUKSA Signals
  → Android HMI / Simulated ECU Reaction
```

Cần nhấn mạnh:

- AI tạo prediction.
- Backend phân phối dữ liệu.
- Dashboard phục vụ fleet manager.
- HMI phục vụ driver.
- CarSky/KUKSA chứng minh hướng connected-car integration.

### 03.4 Kết quả đã hoàn thành

Nên tách theo module:

| Module | Trạng thái | Bằng chứng |
|---|---|---|
| AI Challenge 1 | In Progress / Partial Verified | Có `trip_visual_demo.py`, TTC pipeline, tuning TTC |
| AI Challenge 2 | In Progress / Partial Verified | Có driver state model, RF v2, safety fusion |
| AI Challenge 3 | In Progress / Partial Verified | Có `risk_engine.py`, rule/model fusion |
| Backend | Completed foundation | Có FastAPI, `/health`, `/docs`, WebSocket replay |
| Fleet Dashboard | In Progress | Có FE app, cần polish UI/data integration |
| Fleet AI Copilot | Planned before Code Freeze | Đã xác định input/output và use case |
| CarSky/KUKSA | Verified | Deployment từng đạt `Running 3/3`, Signal Watch nhận signal |
| Android HMI | Verified visual | HMI đổi SAFE/WARNING/CRITICAL theo signal |
| Voice/TTS | Risk / Limited | Android VM thiếu TTS engine mặc định |

### 03.5 Demo tính năng cốt lõi

Trong report chỉ cần mô tả ngắn, không cần ghi toàn bộ thao tác.

Nội dung nên viết:

- Demo trip chạy qua AI để sinh `predicted_ttc`, `predicted_driver_state`, `predicted_risk_score`.
- Backend/Fleet Dashboard dùng output đó để hiển thị risk.
- CarSky/KUKSA nhận signal.
- Android HMI đổi trạng thái cảnh báo.

Không đưa quá nhiều command vào report. Command chi tiết để trong `C2_END_TO_END_DEMO_SCRIPT.md`.

### 03.6 KPI & số liệu ban đầu

Bảng KPI bắt buộc nên có:

| KPI | Cách đo | Trạng thái C2 |
|---|---|---|
| Model Accuracy | Accuracy/F1 cho Challenge 2 | Pending AI validation log |
| Detection True/False Rate | TP/FP/FN cho TTC danger và driver state | Pending measurement |
| End-to-end Capability | AI output → Dashboard/HMI | Verified by integrated demo |
| Processing Time / Latency | AI inference + Backend replay + CarSky signal + HMI update | Pending latency measurement |
| Data Completeness | Đủ trip/frame/column/output schema | In Progress |
| Technical KPI | `/health`, WebSocket 20 FPS, CarSky `Running 3/3` | Partial Verified |
| Business KPI | Risk prioritization, alert reason, recommended action | In Progress |

Nguyên tắc viết KPI:

- Có số thì ghi số.
- Chưa có số thì ghi `Pending measurement`.
- Không tự bịa accuracy hoặc latency.
- Nếu dùng mock signal cho CarSky demo, ghi rõ là `mock signal sender for demo`, không ghi là AI realtime đã hoàn chỉnh.

### 03.7 Khó khăn, rủi ro & hỗ trợ

Các rủi ro nên báo cáo:

| Rủi ro | Tác động | Hướng xử lý |
|---|---|---|
| KPI AI chưa chốt | Khó so sánh với proposal | Chạy validation/evaluation log trước Code Freeze |
| CarSky/KUKSA VSS format | Broker crash nếu VSS sai schema | Giữ VSS dạng object/map `{}` |
| Custom VHAL limitation | Android CarProperty không thấy custom DMS props | Dùng KUKSA/CarSky signal path trực tiếp |
| Android VM thiếu TTS engine | Voice có thể không phát âm thanh | Demo visual alert là kênh chính; TTS là optional |
| Fleet Dashboard chưa polish | UI có thể chưa đủ thuyết phục | Chuẩn hóa dashboard state và screenshot backup |
| Fleet AI Copilot chưa hoàn tất | Chưa thể demo full chatbot nếu trễ | Bắt đầu rule-based/RAG nhẹ trước, LLM API sau |
| Demo live phụ thuộc cloud | CarSky có thể chậm hoặc lỗi runtime | Chuẩn bị video/screenshot backup |

### 03.8 Kế hoạch công việc còn lại

Kế hoạch từ C2 đến Code Freeze:

| Ưu tiên | Việc cần làm | Owner đề xuất |
|---|---|---|
| P0 | Chốt full CSV submission cho Challenge 1/2/3 | AI team |
| P0 | Chạy KPI log: composite score, accuracy/F1, latency | AI + BE |
| P1 | Nối output AI vào Backend/Fleet Dashboard ổn định | BE + FE |
| P1 | Chuẩn hóa Fleet Dashboard UI | FE team |
| P1 | Làm Fleet AI Copilot MVP | FE + BE |
| P1 | Giữ CarSky deployment ổn định | BE/CarSky |
| P2 | Polish Android HMI visual | HMI/UIUX |
| P2 | Chuẩn bị video backup và screenshot evidence | All |
| P2 | Viết coaching/report summary | BE + FE |

### 03.9 Phân công nhiệm vụ trong đội

Mẫu phân công:

| Thành viên | Vai trò | Công việc |
|---|---|---|
| Nhân | Backend / CarSky / HMI integration | Backend API, CarSky signal, HMI, report/demo coordination |
| AI member | AI Challenge 1/2/3 | TTC, driver state, risk fusion, KPI log |
| FE member | Fleet Dashboard | Dashboard UI, alert/risk view, Copilot UI |
| UI/UX member | HMI/Fleet visual polish | Design HMI/dashboard, support APK visual |
| Presenter | Storytelling/demo | Script nói, video demo, trả lời BTC |

Nếu chưa chắc tên người, để role trước rồi điền sau.

---

## 04. Checklist trước khi xuất báo cáo

Trước khi nộp report, kiểm tra:

- [ ] Có đủ 9 mục BTC yêu cầu.
- [ ] Không lẫn nội dung thao tác demo quá dài.
- [ ] Có bảng KPI.
- [ ] KPI chưa đo được ghi rõ `Pending measurement`.
- [ ] Có phần khó khăn/rủi ro/hỗ trợ.
- [ ] Có kế hoạch từ C2 đến Code Freeze.
- [ ] Không show API key/secret.
- [ ] Không nói feature roadmap là đã hoàn thành.
- [ ] Có link repository.
- [ ] Có video demo tối đa 10 phút.

---

## 05. File nên dùng để soạn báo cáo cuối

| File | Mục đích |
|---|---|
| `C2_PROGRESS_REPORT_FPTU_DMS_VISION.md` | Nội dung báo cáo chính |
| `C2_REPORT_README.md` | Hướng dẫn cấu trúc và checklist báo cáo |
| `C2_END_TO_END_DEMO_SCRIPT.md` | Script thao tác demo, không đưa toàn bộ vào report |
| `readmeproposal.md` | Proposal gốc/ý tưởng nhóm |
| `README.md` | Yêu cầu BTC / context nộp bài |

---

## 06. Câu chữ nên dùng trong báo cáo

Nên dùng:

```text
At C2, the team has completed the foundation and verified the key integration path.
```

Viết tiếng Việt:

> Tại mốc C2, nhóm đã hoàn thiện foundation của AI pipeline, Backend, Fleet Dashboard và CarSky/HMI integration. Một số KPI định lượng đang được chốt bằng validation log trước Code Freeze.

Nên dùng cho Fleet AI Copilot:

> Fleet AI Copilot là feature nhóm cam kết triển khai từ C2 đến Code Freeze, nhằm giúp fleet manager hỏi nhanh về xe rủi ro, nguyên nhân cảnh báo và recommended action dựa trên trip/risk/alert summary.

Không nên dùng:

```text
Hoàn thành 100%
Production-ready
Realtime full system completed
TTS fully supported
ECU real control completed
```

Trừ khi có bằng chứng chạy thật.

---

## 07. Kết luận ngắn cho báo cáo

Có thể dùng đoạn này ở cuối report:

> FPTU DMS Vision đã đạt được foundation quan trọng tại mốc C2: AI pipeline cho TTC, driver state và risk fusion; Backend API/replay; Fleet Dashboard MVP; CarSky/KUKSA signal integration; Android HMI visual warning. Giai đoạn tiếp theo sẽ tập trung vào KPI định lượng, hoàn thiện full submission, polish Fleet Dashboard/HMI và triển khai Fleet AI Copilot để tăng giá trị vận hành cho fleet manager.

