# BÁO CÁO KỸ THUẬT TOÀN DIỆN & HƯỚNG DẪN KIỂM THỬ (FULL 100% TECHNICAL & FEATURE SPECIFICATION)
## DỰ ÁN: FPTU DMS VISION — DRIVER INTELLIGENCE & FLEET SAFETY PLATFORM
> **Connected Car Hackathon 2026 — Track: DMS-10 Driver Intelligence Platform**  
> *Dành riêng cho Ban Tổ Chức (BTC) Kỹ thuật & Đội ngũ Đánh giá Feature C (AI, Backend, Frontend, CarSky HMI)*

---

## 1. TỔNG QUAN HỆ THỐNG VÀ BẢN NGUYÊN TẮC (SYSTEM ARCHITECTURE & INTEGRATION PRINCIPLES)

### 1.1 Mục tiêu Hệ thống & Ba Challenge cốt lõi
FPTU DMS Vision giải quyết triệt để bài toán an toàn giao thông thông minh bằng cách hợp nhất đa luồng dữ liệu thời gian thực từ:
1. **Camera đường (Road Camera):** Xác định vật thể, ước lượng khoảng cách và chỉ số va chạm TTC.
2. **Camera cabin (Driver Camera):** Nhận diện hành vi, mắt, miệng và trạng thái tỉnh táo của tài xế.
3. **Telemetry xe (Vehicle Telemetry/CAN Bus):** Đọc tốc độ, gia tốc, phanh, bám đuôi.

Hệ thống cung cấp kết quả qua file Submission CSV theo chuẩn BTC:
```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

### 1.2 Nguyên tắc Tích hợp & Xử lý Dữ liệu Thực (Data Integrity Principles)
- **AI Core là Nguồn Sự Thật duy nhất (Single Source of Truth):** Toàn bộ các chỉ số `predicted_ttc`, `predicted_driver_state` và `predicted_risk_score` được tính toán trực tiếp từ mô hình AI, Backend tuyệt đối không override hay tạo dữ liệu giả.
- **Backend & Middleware Zero-Loss:** Backend validate contract qua Pydantic Schema, streaming realtime qua WebSocket không làm rơi frame hay giảm độ chính xác của AI.
- **Tích hợp phần cứng xe CarSky VSS:** Chuyển đổi dữ liệu trực tiếp sang Vehicle Signal Specification (VSS) để hiển thị trên màn hình ô tô Android Automotive OS (AAOS HMI).

---

## 2. SƠ ĐỒ LƯỚI KIẾN TRÚC TOÀN DIỆN (FULL SYSTEM DATAFLOW & COMPONENT MAP)

```text
                           [DATA INPUTS]
 ┌──────────────────────────────┬──────────────────────────────┐
 │ Road Camera (Video Frame)    │ Driver Camera (Video Frame)  │
 └──────────────┬───────────────┴──────────────┬───────────────┘
                │                              │
                ▼                              ▼
 ┌──────────────────────────────┐ ┌──────────────────────────────┐
 │ Challenge 1: Road AI (TTC)   │ │ Challenge 2: Driver State AI │
 │ - YOLOv8 Bounding Box        │ │ - MediaPipe Landmarks / EAR  │
 │ - Relative Kinematic Estim. │ │ - Random Forest / ONNX RF V3 │
 └──────────────┬───────────────┘ └──────────────┬───────────────┘
                │                              │
                └──────────────┬───────────────┘
                               ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ Challenge 3: Risk Fusion Engine                              │
 │ - Formula: Risk = f(DriverState, TTC, Speed, Accel)         │
 │ - Dynamic Escalation (TTC < 1.5s & Drowsy -> Risk > 85)      │
 └──────────────────────────────┬───────────────────────────────┘
                                │ (DecisionEvent Object)
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ FASTAPI BACKEND (SE/BE)                                      │
 │ - Pydantic Contract Validator (app.domain.schemas.ai_contract)│
 │ - Trip Session Management & Event Outbox                     │
 │ - WebSocket Broadcast Server (/api/v1/ws/live)               │
 └──────────────┬──────────────────────────────┬────────────────┘
                │                              │
                ▼                              ▼
 ┌──────────────────────────────┐ ┌──────────────────────────────┐
 │ FLEET DASHBOARD & AI COPILOT │ │ CARSKY AUTOMOTIVE PLATFORM   │
 │ (SE/FE)                      │ │ (SE/HMI & SE/BE/scripts)     │
 │ - React + Vite Realtime UI   │ │ - KUKSA Databroker (VSS Tree)│
 │ - Driver Safety Ranking      │ │ - VHAL Mux Bridge            │
 │ - AWS Bedrock LLM Gateway    │ │ - Android Native HMI APK     │
 └──────────────────────────────┘ └──────────────────────────────┘
```

---

## 3. BÁO CÁO KỸ THUẬT CHI TIẾT TỪNG PHÂN HỆ (FEATURE C TECHNICAL SPECIFICATIONS)

### 3.1 Phân hệ AI Core Engine & Challenges

#### Challenge 1 — Collision Risk & Time-To-Collision (TTC)
- **Đường dẫn Source Code:** [AI/core/challenge1_road](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI/core/challenge1_road)
- **Thuật toán & Quy trình:**
  1. Sử dụng YOLOv8 phát hiện phương tiện/vật cản phía trước.
  2. Tính toán diện tích Bounding Box và ước lượng khoảng cách tương đối (Distance).
  3. Kết hợp tốc độ xe (Ego Speed) từ Telemetry để tính $TTC = \frac{Distance}{Closing\_Speed}$.
- **Định dạng Output:** `predicted_ttc` (kiểu `float`, đơn vị: giây, clipped [0.0, 10.0]).

#### Challenge 2 — Driver Intelligence (Phân loại Trạng thái Tài xế)
- **Đường dẫn Source Code:** [AI/core/challenge2_driver](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI/core/challenge2_driver)
- **Thuật toán & Quy trình:**
  1. Nhận dạng khuôn mặt và trích xuất 468 điểm mốc (MediaPipe Face Mesh).
  2. Tính toán chỉ số tỉ lệ mở mắt (Eye Aspect Ratio - EAR) và tỉ lệ mở miệng (Mouth Aspect Ratio - MAR).
  3. Đưa đặc trưng vào mô hình Random Forest Classifier v3 (`driver_state_rf_v3.onnx`).
- **Các Trạng thái Đã Phân loại:**
  - `normal`: Nhìn thẳng, mắt mở bình thường.
  - `drowsy`: Nhắm mắt prolonged (> 0.5s) hoặc ngáp liên tục.
  - `distracted`: Quay đầu sang trái/phải, nhìn xuống quá thời gian cho phép.
  - `using_phone`: Cầm điện thoại sát tai hoặc trước mặt.
- **Định dạng Output:** `predicted_driver_state` (kiểu `string`).

#### Challenge 3 — Risk Fusion Engine (Hợp nhất Rủi ro Đa luồng)
- **Đường dẫn Source Code:** [AI/core/challenge3_fusion](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI/core/challenge3_fusion)
- **Thuật toán Hợp nhất (Multi-modal Heuristic/ML Fusion):**
  $$Risk = BaseRisk(TTC) + Weight_{Driver} \times Penalty(DriverState) + TelemetryPenalty$$
  - Khi $TTC < 1.5s$ và $DriverState \in \{drowsy, distracted\}$, $Risk$ nhảy vọt lên ngưỡng nguy cấp ($> 85.0$).
- **Định dạng Output:** `predicted_risk_score` (kiểu `float`, từ `0.0` đến `100.0`).

---

### 3.2 Phân hệ Backend Service (FastAPI Architecture)

- **Đường dẫn Source Code:** [SE/BE/app/](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app)
- **Contract Schema (Lớp bảo vệ dữ liệu):**
  File [SE/BE/app/domain/schemas/ai_contract.py](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app/domain/schemas/ai_contract.py) quy định cấu trúc `DecisionEvent`:
  ```python
  class DecisionEvent(BaseModel):
      frame_id: int
      timestamp: float
      predicted_ttc: float
      predicted_driver_state: str
      predicted_risk_score: float
      speed: Optional[float] = 0.0
  ```
- **Hệ thống RESTful API Endpoints:**
  - `GET /health` & `GET /ready`: Trả về trạng thái hoạt động và cấu hình stream.
  - `GET /api/v1/trips`: Liệt kê danh sách tất cả chuyến đi trong hệ thống.
  - `GET /api/v1/trips/{trip_id}/events`: Lấy danh sách sự kiện rủi ro của từng chuyến đi.
  - `POST /api/v1/events/ingest`: Tiếp nhận event từ AI Engine.
- **WebSocket Streaming Engine:**
  - Endpoint: `WS /api/v1/ws/live`
  - Đảm bảo phát trực tiếp các sự kiện nguy hiểm tới Dashboard với độ trễ $< 50ms$.

---

### 3.3 Phân hệ Fleet Dashboard & AI Copilot System

- **Đường dẫn Source Code Frontend:** [SE/FE/src/](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src)
- **Web App Architecture (React + Vite + TypeScript):**
  - **Fleet Overview Screen:** Quản lý toàn bộ thông số xe, tổng quan mức độ an toàn.
  - **Driver Ranking Screen:** [SE/FE/src/components/DriverRankingView.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/DriverRankingView.tsx) tự động xếp hạng tài xế từ an toàn nhất đến nguy hiểm nhất dựa trên điểm số lũy kế.
  - **Trip Detail & Interactive Replay:** Tua lại hành trình video cùng biểu đồ biến thiên của TTC và điểm rủi ro.
#### C. Chi tiết Tất cả Màn hình UI, Components & Features của Fleet Dashboard
1. **Màn hình Bản đồ Đội xe (Fleet Map View - `MAP`):**
   - *Ô Bản đồ GPS Realtime (Interactive Map Canvas):* Hiển thị vị trí trực tiếp của các xe, đường đi chuyến đi thời gian thực.
   - *Ô Thẻ Thông tin Xe (Vehicle Quick Info Card):* Tên tài xế, Biển số xe, `trip_id`, Safety Score (0-100), Tốc độ (km/h) và TTC.
   - *Ô Danh sách Đội xe (Vehicle Selection Drawer):* Lọc và xem trạng thái vận hành của từng xe trong hệ thống.
   - *Các Nút Thao tác Quick Actions:* `View Live Feed` (Xem camera live), `Trip Detail` (Xem chi tiết chuyến đi), `Intervene` (Can thiệp khẩn cấp).

2. **Màn hình Xem Trực tiếp trên Xe (Vehicle Live View - `VEHICLE_LIVE`):**
   - *Ô Dual Video Streams:* Road Camera (Vẽ Bounding Box vật cản, khoảng cách) & Driver Camera (MediaPipe Face Mesh 468 mốc).
   - *Ô Realtime Telemetry & AI Overlay:* Chỉ số TTC thời gian thực, Driver State (`Normal`, `Drowsy`, `Distracted`, `Using Phone`) và Điểm Rủi ro Hợp nhất (`Final Risk Score`).
   - *Ô Console Cảnh báo Trực tiếp (Live Alert Log Drawer):* Nhận và hiển thị thông báo nguy hiểm thời gian thực qua WebSocket (`WS /api/v1/alerts/live`).

3. **Màn hình Chi tiết Chuyến đi & Tua lại (Trip Detail View - `TRIP_DETAIL`):**
   - *Ô Video Replay & Timeline Slider:* Tua lại từng giây video hành trình và đồng bộ trạng thái AI.
   - *Ô Biểu đồ Biến thiên Rủi ro (Risk & TTC Timeline Graph):* Biểu đồ đường biến thiên Risk Score và TTC theo thời gian thực.
   - *Ô Danh sách Sự kiện Vi phạm (Trip Risk Events Log):* Đánh dấu chính xác các thời điểm xảy ra sự kiện suýt va chạm hoặc tài xế mất tập trung.

4. **Màn hình Xếp hạng An toàn Tài xế (Driver Ranking View - `DRIVER_RANKING`):**
   - *Ô Bảng Xếp hạng Đội xe (Fleet Leaderboard Table):* Xếp hạng tài xế, Safety Score, Tổng số vi phạm buồn ngủ/mất tập trung/nguy hiểm.
   - *Ô Thống kê Phân bổ Điểm (Score Distribution Card):* Phân nhóm tài xế thành 3 mức: *Safe*, *Moderate*, *High Risk*.

5. **Trợ lý Fleet AI Copilot (AWS Bedrock LLM Integration):**
   - *AI Copilot Drawer:* Khung chat slide-out bên phải bằng Tiếng Việt tự nhiên, gợi ý câu hỏi mẫu (*Phân tích rủi ro chuyến đi*, *Tóm tắt vi phạm*).
   - *Copilot Fleet Report Page (`?view=copilot-report`):* Tự động tạo Báo cáo Quản trị An toàn (Executive Safety Report) với bố cục chuẩn in ấn/xuất PDF A4.

6. **Cửa sổ Can thiệp Khẩn cấp (Intervention Modal):**
   - Bấm `Intervene` khi có rủi ro `CRITICAL` để gửi tin nhắn cảnh báo giọng nói/âm báo khẩn cấp xuống màn hình **CarSky Android HMI** trên ô tô.


---

### 3.4 Phân hệ Tích hợp Màn hình Ô tô CarSky Ecosystem & Android HMI

- **Đường dẫn Source Code:** [SE/HMI/](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/HMI) và [SE/BE/scripts/carsky_phase05.py](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/scripts/carsky_phase05.py)
- **Kiến trúc 3 Nodes CarSky:**
  1. `DMS Signal Broker`: KUKSA Databroker lưu trữ cấu trúc tín hiệu VSS.
  2. `DMS HMI Bridge`: VHAL Multiplexer chuyển tín hiệu từ gRPC/KUKSA sang Android Property.
  3. `DMS Android HMI`: Native Android App trên Android Automotive OS.
- **Tín hiệu VSS Register trên CarSky Broker:**
  - `Vehicle.Speed`
  - `Vehicle.ADAS.FinalRiskScore`
  - `Vehicle.Driver.State`
  - `Vehicle.ADAS.DisplaySeverity` (`SAFE`, `WARNING`, `CRITICAL`)
  - `Vehicle.ADAS.AIStatus`

---

## 4. BẢNG TỔNG HỢP CHỈ SỐ VÀ KPI ĐÁNH GIÁ (EXPERIMENTAL KPI METRICS)

| Hạng mục Kiểm thử | Phương pháp / Môi trường Đánh giá | Kết quả Đạt được (Benchmark Result) | Trạng thái Đánh giá |
|---|---|---:|---|
| **Challenge 1 — TTC** | Test trên tập dữ liệu BTC Practice | **Composite: 65.5 / 100** (Danger F1: 69.9%) | PASSED |
| **Challenge 2 — Driver State** | Practice Evaluation Dataset | **Composite: 87.2 / 100** | PASSED |
| **Driver State Holdout Test** | Independent Holdout Test | **Accuracy: 78.47%** (Macro-F1: 80.28%) | PASSED |
| **Challenge 3 — Risk Fusion** | Evaluator Practice Suite | **100.0 / 100** | PASSED |
| **Backend Integration Tests** | Automated Pytest Suite (13 tests) | **13 / 13 Passed (100%)** | PASSED |
| **Frontend Production Build** | Vite Build Validation | **0 Errors / Clean Build** | PASSED |
| **CarSky Deployment Status** | 3 Blueprint Nodes Check | **3 / 3 Nodes RUNNING** | PASSED |
| **AWS Bedrock LLM Integration** | Bedrock Converse API Test | **Latency < 1.8s / 100% Success** | PASSED |

---

## 5. HƯỚNG DẪN CHI TIẾT CÁCH KIỂM THỬ HỆ THỐNG (BTC RUNBOOK FOR TESTING)

### Step 1: Chuẩn bị Môi trường Python Virtual Environment
```bash
# Mở Terminal tại thư mục root HACKATHON
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt toàn bộ dependencies của AI và SE Backend
pip install -r AI/requirements.txt
pip install -r SE/BE/requirements.txt
```

### Step 2: Chạy & Kiểm thử Backend FastAPI
```bash
cd SE/BE
source ../../.venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Mở Terminal mới kiểm tra:
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
pytest  # Chạy 13 bài test tự động của Backend
```

### Step 3: Khởi chạy Fleet Dashboard & Bedrock LLM Copilot
```bash
cd SE/FE
npm install
npm run build   # Kiểm tra build sản phẩm
npm run dev     # Khởi chạy giao diện web
```
Mở trình duyệt tại: `http://127.0.0.1:3000`

### Step 4: Chạy Demo Sản phẩm Tự động (End-to-End Product Runner)
Tại thư mục root `HACKATHON`:
- **Trên Linux / macOS:**
  ```bash
  bash scripts/run_product_demo.sh --mode hybrid-live --trip-dir ./AI/demo_trips/T01-Sample --open-dashboard
  ```
- **Trên Windows (PowerShell):**
  ```powershell
  .\scripts\run_product_demo.ps1 -Mode hybrid-live -TripDir .\AI\demo_trips\T01-Sample -OpenDashboard
  ```

### Step 5: Kiểm thử Tích hợp CarSky Automotive HMI Signals
```bash
cd SE/BE
python scripts/carsky_phase05.py status
python scripts/carsky_phase05.py scenario critical
```

---

## 6. DANH MỤC TÀI LIỆU VÀ CÁC THỦ THUẬT XỬ LÝ SỰ CỐ (TROUBLESHOOTING & DOCS)

### 6.1 Bảng xử lý sự cố thường gặp (Troubleshooting Guide)
1. **Lỗi Port 3000 hoặc Port 8000 bị chiếm dụng:**
   - *Cách xử lý:* Tắt ứng dụng cũ đang chạy ẩn bằng lệnh `lsof -i :3000` hoặc `lsof -i :8000` rồi `kill -9 <PID>`.
2. **Bedrock Copilot báo Authentication Failed:**
   - *Cách xử lý:* Kiểm tra Bearer Token trong `SE/FE/.env.local` đã bị xóa khoảng trắng và dòng mới chưa. Token AWS Bedrock có hạn sử dụng ngắn hạn.
3. **CarSky KUKSA Broker báo `invalid type: sequence, expected a map`:**
   - *Cách xử lý:* Đảm bảo file cấu hình VSS JSON (`dms-vss-signals.json`) được truyền dưới dạng Map/Object `{...}` chứ không phải Array `[...]`.

### 6.2 Danh mục Tài liệu Tham chiếu (Documentation Index)
- **Tài liệu Báo cáo Tổng quát BTC:** [reportbtc/README_TONG_QUAT_DU_AN_VA_HUONG_DAN_TEST.md](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/reportbtc/README_TONG_QUAT_DU_AN_VA_HUONG_DAN_TEST.md)
- **Kịch bản Demo End-to-End Chi tiết:** [reportbtc/C2_END_TO_END_DEMO_SCRIPT.md](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/reportbtc/C2_END_TO_END_DEMO_SCRIPT.md)
- **Backend Architecture & Phases:** [SE/BE/docs/README.md](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/docs/README.md)
- **Android HMI APK Handoff:** [SE/HMI/README_UI_UX_APK_DESIGN.md](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/HMI/README_UI_UX_APK_DESIGN.md)

---
*Báo cáo Kỹ thuật Kịch bản Feature C được lập trực tiếp từ mã nguồn thực tế của dự án FPTU DMS Vision.*
