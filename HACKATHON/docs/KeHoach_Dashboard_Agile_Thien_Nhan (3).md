# **FPTU DMS VISION — SOFTWARE REQUIREMENTS SPECIFICATION (SRS) & ENGINEERING PLAN**

# **Tài Liệu Yêu Cầu Phần Mềm (SRS) & Lịch Thực Thi Chi Tiết FE & BE (Challenge 3)**

> **Dự án:** Connected Car — Driver & Fleet Risk Intelligence Platform  
> **Phiên bản Tài liệu:** SRS & Execution Plan v4.0 (Cập nhật Team AI xử lý Full Business Risk Data)  
> **Định hướng phân việc chính thức (100% Khớp Nối):**  
> 1. **Bên Team AI:** Xử lý FULL toàn bộ AI Vision + Business Risk Logic $\rightarrow$ Xuất file JSON/CSV hoàn chỉnh chứa đầy đủ thông tin (`predicted_ttc`, `predicted_driver_state`, `predicted_risk_score`, `safe_score`).  
> 2. **Bên Team SE (Thiện & Nhân):** Tập trung 100% vào **Master Fleet Dashboard, WebSocket Stream 20 FPS & AI Agent Chatbot Box**:  
>    - **Thiện** (Primary FE & Fleet Dashboard Specialist): Dựng Master Fleet Dashboard (3 Views), Replay Player Bar Controls, Giao diện **AI Agent Chatbot Box**, Audio Visual ADAS Alerts & Export PDF.  
>    - **Nhân** (Primary BE, Streaming & AI Agent Chatbot Specialist): Dựng FastAPI Backend Engine, Adapter nạp JSON/CSV đầy đủ từ AI, WebSocket Stream Replay Server (20 FPS), **AI Agent Chatbot (GenAI Coaching Agent)** & Script tự động xuất 10 CSV nộp BTC.  
> **Tiến độ Fast-Sprint:** **24/07/2026 – 28/07/2026** (Tối đa 4 - 5 ngày để hoàn thành 100% Dashboard & Pipeline)  

---

# **1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI VISION & TELEMETRY INPUTS                     │
│  [Challenge 1: Stereo Camera]   [Challenge 2: Cabin Camera]   [Telemetry]│
│       predicted_ttc          predicted_driver_state, alertness   Kinematics │
└────────────────────┬────────────────────┬───────────────────────────────┘
                     │                    │
                     ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKEND ENGINE (NHÂN - FASTAPI)                     │
│  ┌───────────────────────┐ ┌──────────────────────┐ ┌─────────────────┐ │
│  │  Unified Data Adapter │ │ Kinematics Detector  │ │ Risk Fusion Eng │ │
│  └───────────┬───────────┘ └──────────┬───────────┘ └────────┬────────┘ │
│              │                        │                      │          │
│              ▼                        ▼                      ▼          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │   20 FPS Stream Replay Server (WebSocket / Polling REST API)     │   │
│  └──────────────────────────────────┬───────────────────────────────┘   │
└─────────────────────────────────────┼───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND DASHBOARD (THIỆN - REACT/TAILWIND)          │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │ View 1: Driver HUD  │  │ View 2: Fleet Map   │  │ View 3: Report  │ │
│  │ (NHTSA 2s-glance)   │  │ (Leaderboard/Events)│  │ (SHAP / GenAI)  │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### **1.1. Cấu Trúc Thư Mục & Nguyên Tắc Mở Rộng Feature (Modular Feature-First & Plugin Architecture)**

Để ứng dụng dễ dàng phát triển thêm các tính năng mới (ví dụ: phát hiện *Hút thuốc / Nghe điện thoại*, áp suất lốp, quản lý nhiên liệu) mà **không bị gò bó hay vỡ hệ thống**, dự án áp dụng **Cấu trúc Mô-đun theo Tính năng (Feature-First)** kết hợp **Plugin / Strategy Pattern**.

#### **1.1.1. Backend Architecture (FastAPI - Nhân)**
```text
backend/app/
├── core/                        # Config, CORS, Security Middleware
├── domain/                      # Schemas & Base Interfaces (Pydantic `extra='allow'`)
│   ├── schemas/                 # telemetry.py, risk.py
│   └── interfaces/              # base_detector.py, base_risk_model.py, base_data_source.py
├── modules/                     # DỌN SẠCH TÍNH NĂNG VÀO ĐÂY (Mỗi feature 1 folder độc lập)
│   ├── streaming/               # FR-06: 20 FPS Replay Engine (`/ws/replay/{trip_id}`)
│   ├── risk_fusion/             # Engine rủi ro (Algorithms: nhtsa_v1.py, custom_ml.py)
│   ├── event_detection/         # FR-03: Kinematics & Behavioral Detectors (Plugin-based)
│   │   ├── detectors/           # brake_detector.py, corner_detector.py, [NEW] smoke_detector.py
│   │   └── detector_registry.py # Tự động load danh sách detectors
│   ├── fleet/                   # FR-02: Map & Leaderboard APIs
│   ├── insurance/               # FR-04: SHAP Breakdown & Export
│   └── coaching/                # FR-05: GenAI Agent & Local Fallback
├── adapters/                    # csv_file_adapter.py, live_mqtt_adapter.py
└── main.py                      # App entry point
```
* **Plugin Event Detector:** Mỗi quy tắc vi phạm kế thừa từ `BaseDetector`. Thêm detector mới chỉ cần tạo 1 file trong `detectors/` mà không cần sửa router hay streaming engine.
* **Open Data Schema:** Khai báo Pydantic với `model_config = ConfigDict(extra='allow')` giúp Backend không ném lỗi khi AI Team thêm các trường telemetry mới.

#### **1.1.2. Frontend Architecture (React + Vite - Thiện)**
```text
frontend/src/
├── components/                  # Shared UI Kit (Button, Card, Badge, Modal) & Charts
├── core/                        # ReplayContext (Central Sync 20 FPS Replay Clock), API client, WS Manager
├── features/                    # MỖI FEATURE / MÀN HÌNH NẰM TRONG 1 FOLDER ĐỘC LẬP
│   ├── driver-hud/              # FR-01: RiskGaugeWidget, StatusPill, AlertBanner, DriverHudPage.jsx
│   ├── fleet-manager/           # FR-02 & FR-03: TrajectoryMap, LeaderboardTable, EventTimeline
│   ├── insurance-report/        # FR-04 & FR-05: ShapBreakdownChart, CoachingChatbotBox
│   └── [NEW] fuel-management/   # Dễ dàng gắn thêm màn hình / tính năng mới
├── routes/                      # React Router configuration
└── App.jsx
```
* **Replay Engine Context:** `ReplayContext` quản lý nhịp tim 20 FPS. Tất cả các màn hình/widget đăng ký đọc state từ Context này để đồng bộ thời gian thực mà không vỡ layout.
* **Widget System:** Màn hình được ghép từ các widget độc lập. Muốn mở rộng UI chỉ cần import widget mới vào Dashboard layout.

---

### **1.2. MA TRẬN CĂN CỨ KHOA HỌC & TIÊU CHUẨN QUỐC TẾ CHO UI/UX & DATA FIELDS**

| Mã Căn Cứ | Quyết Định Thiết Kế & Data Field | Tiêu Chuẩn Quốc Tế & Căn Cứ Khoa Học Uy Tín | Bằng Chứng / Tác Động Thực Nghiệm | Feature & User Story Khớp Nối |
| :---: | :--- | :--- | :--- | :---: |
| **A1** | Hiển thị `predicted_ttc` & cảnh báo va chạm | **IIHS (Cicchino 2017) & NHTSA (1997)** | Cảnh báo FCW dựa trên TTC giúp giảm **27% - 50%** vụ va chạm đuôi xe thực tế. | **US-01 / FR-01** |
| **A2** | Hiển thị `predicted_driver_state` (DMS) real-time | **PMC NCBI & Quy định EU Mandate 2024** | Cảnh báo mệt mỏi nhiều tầng giúp giảm lệch làn; EU bắt buộc DMS trên xe mới từ 2024. | **US-02 / FR-01** |
| **A3** | Cờ telemetry (`is_harsh_brake`, `corner`, `speeding`) | **FMCSA (Chính phủ Mỹ), ScienceDirect, MDPI (2026)** | Phanh gấp tương quan dương **~0.59** với tỷ lệ tai nạn; là chỉ báo hàng đầu (leading indicator). | **US-05 / FR-03** |
| **A4** | Driver Risk Leaderboard (`predicted_safe_score`) | **ScienceDirect (Soleymanian, Stevenson) & MDPI Sensors (2025)** | Phản hồi so sánh đồng nghiệp (*peer comparison*) giảm **52%** tần suất sự kiện lái ẩu. | **US-04 / FR-02** |
| **A5** | Insurance Report tổng hợp (% state, SHAP breakdown) | **arXiv (Nghiên cứu 100,000+ khách hàng UBI) & Industry standard** | Ngành bảo hiểm UBI định phí dựa trên **điểm tổng hợp cuối trip**, không dùng dữ liệu log thô 20 FPS. | **US-06 / FR-04** |
| **B1** | Driver HUD Ergonomics: Tối giản, đọc $\le 2\text{s}$ | **NHTSA Visual-Manual Guidelines (Federal Register)** | Thao tác liếc mắt rời đường $>2.0\text{s}$ làm tăng đáng kể nguy cơ va chạm $\rightarrow$ HUD bỏ menu/sidebar. | **US-01 / FR-01** |
| **B2** | Quy chuẩn màu sắc (Đỏ = Nguy hiểm, Vàng = Cảnh báo, Xanh = An toàn) | **ISO 2575:2021 (Tổ chức Tiêu chuẩn hóa Quốc tế)** | Tiêu chuẩn toàn cầu ISO quy định màu sắc cho đèn cảnh báo và màn hình trong cabin ô tô. | **Tất cả Views** |
| **B3** | Giới hạn 4–8 KPI chính trên Fleet Dashboard | **Nielsen Norman Group (NN/g) & PMC Review 75 studies** | Người dùng bị quá tải nhận thức khi Dashboard có $\ge 9$ modules; giao diện tuân theo mắt quét hình chữ F. | **US-03, US-04 / FR-02** |
| **B4** | 3 Persona = 3 Giao diện thiết kế riêng biệt | **Nielsen Norman Group & NHTSA Guidelines** | Tách biệt nhu cầu real-time của Tài xế với nhu cầu retrospective của Quản lý đoàn xe & Bảo hiểm. | **FR-01, FR-02, FR-04** |

---

# **2. DANH SÁCH USER STORIES & SUY RA FEATURES CẦN LÀM (USER STORIES MAPPING)**
> **Nguyên tắc:** Mỗi Feature kỹ thuật đều được suy ra trực tiếp từ **User Story** của người dùng thực tế và có **Căn cứ Khoa học / Tiêu chuẩn Quốc tế** bảo chứng.

### **2.1. User Stories Dành Cho Tài Xế (Driver Persona)**

* **US-01 (Cabin Real-time Risk Warning):**
  - **User Story:** *"Là một tài xế đang điều khiển xe trên đường, tôi muốn nhìn thấy chỉ số rủi ro trực quan và nhận âm thanh/hình ảnh cảnh báo tức thì khi khoảng cách va chạm quá ngắn ($TTC \le 1.5s$) hoặc khi tôi chợp mắt, Để tôi kịp thời phản ứng trong 2 giây nhằm tránh tai nạn thảm khốc."*
  - **Feature suy ra:** **FR-01 (Driver HUD View & ADAS Audio/Visual Alerts)**.
  - **Căn cứ Khoa học / Tiêu chuẩn:** **A1 (IIHS & NHTSA FCW 27-50%)**, **B1 (NHTSA Visual-Manual 2s-glance)**, **B2 (ISO 2575:2021 Color Scheme)**.
  - **Tiêu chuẩn chấp nhận (AC):** Kim quay SVG Gauge biến đổi từ Xanh $\rightarrow$ Vàng $\rightarrow$ Đỏ. Âm thanh bíp bíp phát ngay khi va chạm nguy hiểm, viền màn hình nháy đỏ.

* **US-02 (Driver Fatigue & State Monitoring):**
  - **User Story:** *"Là một tài xế, tôi muốn xem mức độ tỉnh táo và trạng thái hiện tại của mình (Alert, Drowsy, Yawning, Distracted, Microsleep), Để tôi chủ động tấp xe vào lề đường nghỉ ngơi khi cơ thể quá mệt mỏi."*
  - **Feature suy ra:** **FR-01 (Driver Status Pill & Alertness Bar)**.
  - **Căn cứ Khoa học / Tiêu chuẩn:** **A2 (PMC NCBI & Quy định EU Mandate 2024)**, **B2 (ISO 2575:2021)**.
  - **Tiêu chuẩn chấp nhận (AC):** Status Pill đổi 5 nhãn màu rõ ràng, thanh Tỉnh táo cập nhật liên tục theo nhịp 20 FPS.

---

### **2.2. User Stories Dành Cho Quản Lý Đoàn Xe (Fleet Manager Persona)**

* **US-03 (Live Fleet Trajectory Tracking):**
  - **User Story:** *"Là một Quản lý đoàn xe, tôi muốn theo dõi vị trí di chuyển thời gian thực của toàn bộ xe trên bản đồ GPS trực tuyến, Để tôi giám sát tuyến đường, tốc độ và tọa độ hoạt động của các xe trong đoàn."*
  - **Feature suy ra:** **FR-02 (Live Fleet Trajectory Map)**.
  - **Căn cứ Khoa học / Tiêu chuẩn:** **B3 (Nielsen Norman Group F-shaped pattern & PMC 75 studies - 4-8 KPIs limit)**, **B4 (3 Persona interfaces)**.
  - **Tiêu chuẩn chấp nhận (AC):** Bản đồ Leaflet/Mapbox vẽ Polyline màu xanh đậm, Marker biểu tượng ô tô xoay góc theo hướng chuyển động.

* **US-04 (Driver Risk Ranking & Safety Leaderboard):**
  - **User Story:** *"Là một Quản lý đoàn xe, tôi muốn xem bảng xếp hạng thứ tự tài xế dựa trên điểm an toàn (`predicted_safe_score`), Để tôi khen thưởng các tài xế lái xe an toàn và nhắc nhở các tài xế có nguy cơ rủi ro cao."*
  - **Feature suy ra:** **FR-02 (Driver Risk Leaderboard & Trip Switcher)**.
  - **Căn cứ Khoa học / Tiêu chuẩn:** **A4 (ScienceDirect RCT Soleymanian/Stevenson - Peer comparison giảm 52% vi phạm & MDPI 2025)**.
  - **Tiêu chuẩn chấp nhận (AC):** Bảng xếp hạng giảm dần theo Safe Score (0-100 điểm), hiển thị Badge Huy chương Top 1, Top 2, Top 3.

* **US-05 (Risk Event History & Jump-to-Replay):**
  - **User Story:** *"Là một Quản lý đoàn xe, tôi muốn xem danh sách dòng thời gian các sự kiện vi phạm (Phanh gấp, Cua gắt, Quá tốc độ, Vi ngủ) và có thể bấm vào sự kiện để video tua ngay đến khoảnh khắc đó, Để tôi kiểm tra nhanh sự cố mà không cần xem hết video dài 90 giây."*
  - **Feature suy ra:** **FR-03 (Risk Event Timeline & Interactive Filter)**.
  - **Căn cứ Khoa học / Tiêu chuẩn:** **A3 (FMCSA Leading indicator, ScienceDirect & MDPI 2026 peer-reviewed correlation ~0.59)**.
  - **Tiêu chuẩn chấp nhận (AC):** Event Timeline liệt kê sự kiện kèm Timestamp. Click vào dòng vi phạm $\rightarrow$ Replay tua đến đúng `timestamp` đó.

---

### **2.3. User Stories Dành Cho Bảo Hiểm & Doanh Nghiệp (Insurance Analyst Persona)**

* **US-06 (UBI Insurance Risk Profiling & SHAP Breakdown):**
  - **User Story:** *"Là một Chuyên viên định phí bảo hiểm UBI, tôi muốn xem biểu đồ % phân bố trạng thái tài xế và ma trận đóng góp rủi ro SHAP Breakdown (% cận va chạm, % mệt mỏi, % phanh gấp), Để tôi đưa ra mức phí bảo hiểm phù hợp dựa trên dữ liệu lái xe thực tế."*
  - **Feature suy ra:** **FR-04 (Business & Insurance Report with SHAP Breakdown)**.
  - **Căn cứ Khoa học / Tiêu chuẩn:** **A5 (arXiv 100,000+ UBI Customers Retrospective aggregated data)**, **B4 (3 Persona distinct interfaces)**.
  - **Tiêu chuẩn chấp nhận (AC):** Biểu đồ Recharts Donut Chart phân bố trạng thái tài xế, Stacked Bar Chart SHAP breakdown, Nút xuất PDF.

* **US-07 (GenAI Coaching Advisory & PDF Report):**
  - **User Story:** *"Là một Cố vấn An toàn giao thông, tôi muốn hệ thống tự động sinh nhận xét huấn luyện tài xế bằng GenAI (và có thể chạy offline khi mất mạng), Để tôi gửi báo cáo đào tạo chuyên nghiệp cho tài xế và xuất file PDF."*
  - **Feature suy ra:** **FR-05 (GenAI Coaching Advisory Agent & Local Fallback)**.
  - **Căn cứ Khoa học / Tiêu chuẩn:** **A5 (Retrospective Coaching)**, **US-07 (Local Rule Fallback Engine)**.
  - **Tiêu chuẩn chấp nhận (AC):** UI Chatbot Box hiển thị câu tư vấn với hiệu ứng gõ chữ Streaming. Backend tự động chuyển sang bộ Template offline khi ngắt kết nối LLM API.

---

### **2.4. User Stories Dành Cho Ban Giám Khảo & Kỹ Thuật (Judge & Tester Persona)**

* **US-08 (20 FPS Real-time Stream Replay Simulation):**
  - **User Story:** *"Là một Ban Giám Khảo cuộc thi, tôi muốn có bộ điều khiển Replay (Play, Pause, Tua Seek slider, Đổi tốc độ 1x/2x/4x) với nhịp truyền mượt mà 20 FPS, Để tôi đánh giá được khả năng vận hành thời gian thực của hệ thống."*
  - **Feature suy ra:** **FR-06 (20 FPS Stream Replay Control Engine)**.
  - **Tiêu chuẩn chấp nhận (AC):** Replay Server push WebSocket nhịp $\Delta t = 50\text{ms}$ (20 FPS), UI Player Bar đồng bộ chuẩn.

* **US-09 (Automated Competition CSV Exporter & Validation):**
  - **User Story:** *"Là một Đội thi Hackathon, tôi muốn có script tự động xuất 10 file CSV nộp bài đúng chuẩn 1,800 dòng x 5 cột và đối chiếu sai số $MAE < 1.5$ điểm, Để đội thi đạt điểm số tối đa theo quy định của BTC."*
  - **Feature suy ra:** **FR-07 (Auto CSV Exporter & Ground-Truth Validator)**.
  - **Tiêu chuẩn chấp nhận (AC):** Script Python sinh đúng 10 file CSV (`T01d.csv`–`T10d.csv`), không chứa `NaN`, $MAE < 1.5$.

---

# **3. HỢP ĐỒNG GIAO TIẾP DỮ LIỆU (DATA CONTRACT & API SPECIFICATIONS)**

### **3.1. Bảng Khớp Nối Output AI $\rightarrow$ Input Dashboard**

| Nguồn Dữ Liệu | Field Name | Kiểu Dữ Liệu | Giá Trị Cho Phép | Xử Lý Tại BE (Nhân) | Xử Lý Tại FE (Thiện) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Challenge 1** | `predicted_ttc` | `float` / `str` | Float $(0.1..10.0)$ hoặc `"inf"` | Chuẩn hóa string `"inf"` thành `Infinity` | Gauge TTC & Audio Alert khi $TTC \le 1.5\text{s}$ |
| **Challenge 2** | `predicted_driver_state` | `str` (Enum) | `"alert"`, `"drowsy"`, `"yawning"`, `"distracted"`, `"microsleep"` | Validate Enum, truyền vào Risk Engine | Render Status Pill (Green/Yellow/Purple/Red) |
| **Challenge 2** | `alertness_score` | `float` | `0.0` – `1.0` | Lưu log & tính PERCLOS trend | Hiển thị thanh Tỉnh Táo / Progress Bar |
| **Telemetry JSON**| `speed_kmh` | `float` | $0.0..180.0$ km/h | Lọc vận tốc, gắn cờ quá tốc độ | Hiển thị Đồng hồ Tốc độ (Speedometer) |
| **Telemetry JSON**| `longitudinal_accel` | `float` | Gia tốc dọc ($m/s^2$) | Tính `is_harsh_brake` ($<-3.0$), `is_harsh_accel` ($>3.0$) | Đẩy event vào Risk Event Timeline |
| **Telemetry JSON**| `lateral_accel` | `float` | Gia tốc ngang ($m/s^2$) | Tính `is_harsh_corner` ($>3.5$) | Đẩy event vào Risk Event Timeline |
| **Engine Ch3** | `predicted_risk_score` | `float` | $0.0..100.0$ (tại từng frame) | Risk Fusion Engine tính theo công thức | Hiển thị Gauge Rủi ro Tức thời |
| **Engine Ch3** | `predicted_safe_score` | `float` | $0.0..100.0$ (tổng hợp trip) | Trừ điểm rủi ro theo công thức BTC | Safe Driving Score chính trên Leaderboard |

---

### **3.2. Payload JSON 20 FPS cho WebSocket / REST API**

Endpoint Streaming: `WS /ws/replay/{trip_id}` hoặc `GET /api/trip/{trip_id}/frame/{frame_id}`  
Nhịp truyền: **20 FPS** ($\Delta t = 0.05\text{s} = 50\text{ms}$/frame).

```json
{
  "frame_id": 450,
  "timestamp": 22.500,
  "telemetry": {
    "speed_kmh": 65.4,
    "longitudinal_accel": -3.45,
    "lateral_accel": 0.82,
    "is_harsh_brake": true,
    "is_harsh_accel": false,
    "is_harsh_corner": false,
    "is_speeding": false
  },
  "ai_vision": {
    "predicted_ttc": 1.42,
    "predicted_driver_state": "microsleep",
    "alertness_score": 0.15
  },
  "risk_fusion": {
    "predicted_risk_score": 78.5,
    "is_compound_critical": true,
    "active_events": ["HARSH_BRAKE", "MICROSLEEP", "CRITICAL_TTC"]
  }
}
```

---

### **3.3. Danh Sách REST APIs Chi Tiết**

1. **`GET /api/fleet/summary`**
   - **Mục đích:** Trả về danh sách tất cả các Trips (`T01d` đến `T10d`), điểm safe score và thống kê lỗi.
2. **`GET /api/trip/{trip_id}/trajectory`**
   - **Mục đích:** Trả về mảng tọa độ GPS để vẽ bản đồ đường đi trên Leaflet Map.
3. **`GET /api/trip/{trip_id}/report`**
   - **Mục đích:** Trả về dữ liệu báo cáo phân tích rủi ro & SHAP breakdown cho Màn hình 3.
4. **`POST /api/coaching/generate`**
   - **Mục đích:** Gọi LLM API (hoặc Fallback Local Rule Engine) sinh câu khuyến nghị huấn luyện tài xế.

---

# **4. CHI TIẾT YÊU CẦU THỰC THI FEATURE & THỜI GIAN THỰC HIỆN (SRS FEATURES TIMELINE)**

---

### **📋 REQUIREMENT FR-01: Driver HUD View (Cabin Real-Time ADAS)**
* **🔗 User Story tương ứng:** **US-01, US-02**
* **⏱️ Thời gian thực hiện (Timeline):** **26/07 – 27/07/2026 (Thời lượng: 2 Ngày / 48 giờ)**
* **Mô tả:** Giao diện cabin cảnh báo thời gian thực cho tài xế tuân thủ chuẩn Ergonomics NHTSA 2s-glance.
* **Quy chuẩn UI/UX (Thiện):** SVG Gauge kim quay từ $0 \rightarrow 100$, Status Pill 5 màu, ADAS Audio Alert sound bíp bíp, CSS keyframes nháy đỏ.
* **Quy chuẩn Backend (Nhân):** WebSocket Stream 20 FPS, normalize `"inf"` $\rightarrow$ `Infinity`, validate enum.

---

### **📋 REQUIREMENT FR-02: Live Fleet Manager View (GPS Map & Leaderboard)**
* **🔗 User Story tương ứng:** **US-03, US-04**
* **⏱️ Thời gian thực hiện (Timeline):** **26/07 – 27/07/2026 (Thời lượng: 2 Ngày / 48 giờ)**
* **Mô tả:** Bản đồ giám sát đoàn xe di chuyển thời gian thực và Bảng xếp hạng điểm an toàn tài xế.
* **Quy chuẩn UI/UX (Thiện):** Leaflet/Mapbox Trajectory Map, Marker ô tô xoay góc di chuyển, Driver Leaderboard xếp hạng Safe Score Top 1-2-3.
* **Quy chuẩn Backend (Nhân):** REST APIs `GET /api/fleet/summary` & `GET /api/trip/{id}/trajectory`.

---

### **📋 REQUIREMENT FR-03: Risk Event Timeline & Interactive Filter**
* **🔗 User Story tương ứng:** **US-05**
* **⏱️ Thời gian thực hiện (Timeline):** **26/07 – 27/07/2026 (Thời lượng: 1.5 Ngày / 36 giờ)**
* **Mô tả:** Dòng thời gian lịch sử các sự kiện nguy hiểm trong chuyến đi với bộ lọc tương tác.
* **Quy chuẩn UI/UX (Thiện):** Timeline liệt kê sự kiện kèm Timestamp, Filter Dropdown, Click event tua ngay đến timestamp đó.
* **Quy chuẩn Backend (Nhân):** Module `KinematicsEventDetector` ($accel < -3.0m/s^2$, $accel > 3.0m/s^2$, $lat\_accel > 3.5m/s^2$).

---

### **📋 REQUIREMENT FR-04: Business & Insurance Report (SHAP & % State)**
* **🔗 User Story tương ứng:** **US-06**
* **⏱️ Thời gian thực hiện (Timeline):** **27/07 – 28/07/2026 (Thời lượng: 1.5 Ngày / 36 giờ)**
* **Mô tả:** Báo cáo phân tích rủi ro phục vụ định phí bảo hiểm UBI và quản trị doanh nghiệp.
* **Quy chuẩn UI/UX (Thiện):** Recharts Donut Chart % phân bố 5 trạng thái tài xế, Stacked Bar Chart SHAP breakdown, Export PDF.
* **Quy chuẩn Backend (Nhân):** Tính toán ma trận % phân bố trạng thái tài xế và SHAP contribution matrix.

---

### **📋 REQUIREMENT FR-05: GenAI Coaching Advisory Agent & Local Fallback**
* **🔗 User Story tương ứng:** **US-07**
* **⏱️ Thời gian thực hiện (Timeline):** **27/07 – 28/07/2026 (Thời lượng: 1.5 Ngày / 36 giờ)**
* **Mô tả:** Tự động sinh nhận xét huấn luyện tài xế bằng GenAI (hoặc Rule-based offline fallback).
* **Quy chuẩn UI/UX (Thiện):** UI Hộp thoại Chatbot với hiệu ứng gõ chữ thời gian thực (Streaming Typing Effect).
* **Quy chuẩn Backend (Nhân):** OpenAI/Gemini API + Module `FallbackRuleEngine` (offline template).

---

### **📋 REQUIREMENT FR-06: 20 FPS Stream Replay Control Engine**
* **🔗 User Story tương ứng:** **US-08**
* **⏱️ Thời gian thực hiện (Timeline):** **24/07 – 25/07/2026 (Thời lượng: 2 Ngày / 48 giờ)**
* **Mô tả:** Thanh điều khiển Replay dữ liệu xe chạy thời gian thực 20 FPS cho buổi trình diễn Demo.
* **Quy chuẩn UI/UX (Thiện):** Player Controls bar (Play, Pause, Speed 1x-4x, Seek Slider).
* **Quy chuẩn Backend (Nhân):** Server timer push WebSocket nhịp $\Delta t = 50\text{ms}$ (20 FPS).

---

### **📋 REQUIREMENT FR-07: Auto CSV Exporter & Ground-Truth Validator**
* **🔗 User Story tương ứng:** **US-09**
* **⏱️ Thời gian thực hiện (Timeline):** **27/07 – 28/07/2026 (Thời lượng: 1 Ngày / 24 giờ)**
* **Mô tả:** Xuất 10 file CSV chuẩn thi nộp BTC và kiểm tra tự động lỗi.
* **Quy chuẩn Backend (Nhân):** Script `export_submission_csv.py` (1,800 dòng x 5 cột) + Script `validate_submission.py` ($MAE < 1.5$).

---

# **5. BẢNG MÁT-RẬN USER STORIES $\rightarrow$ FEATURES $\rightarrow$ CĂN CỨ KHOA HỌC $\rightarrow$ PHÂN CÔNG THỜI GIAN**

| User Story ID | Persona | Tóm Tắt Nhu Cầu | Feature Suy Ra | Căn Cứ Khoa Học & Tiêu Chuẩn | Thời Gian | Task BE (Nhân) | Task FE (Thiện) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **US-01** | Driver | Muốn xem gauge rủi ro & nghe cảnh báo | **FR-01 (Driver HUD)** | **A1 (IIHS/NHTSA), B1 (NHTSA 2s), B2 (ISO 2575)** | 26–27/07 | Push WebSocket 20 FPS | SVG Risk Gauge, Audio FX, Red Blink |
| **US-02** | Driver | Muốn xem trạng thái vi ngủ / mệt mỏi | **FR-01 (Status Pill)** | **A2 (PMC NCBI / EU Mandate), B2 (ISO 2575)** | 26–27/07 | Validate Driver State Enum | Status Pill 5 màu, Progress Bar |
| **US-03** | Fleet Mgr | Muốn xem bản đồ xe chạy thời gian thực | **FR-02 (GPS Fleet Map)** | **B3 (NN/g 4-8 KPIs), B4 (3 Roles)** | 26–27/07 | API Trajectory GPS array | Leaflet Map, Marker ô tô chạy real-time |
| **US-04** | Fleet Mgr | Muốn xem BXH điểm an toàn tài xế | **FR-02 (Leaderboard)** | **A4 (ScienceDirect RCT 52% & MDPI 2025)** | 26–27/07 | API Fleet Summary list | Leaderboard UI, Top 1-2-3 Badges |
| **US-05** | Fleet Mgr | Muốn xem timeline vi phạm & tua nhanh | **FR-03 (Event Timeline)** | **A3 (FMCSA leading & MDPI peer-reviewed ~0.59)** | 26–27/07 | `KinematicsEventDetector` | Timeline UI, Filter, Click Seek Replay |
| **US-06** | Insurance | Muốn xem SHAP breakdown & % state | **FR-04 (Insurance Report)**| **A5 (arXiv 100k+ UBI retrospective), B4 (3 Roles)**| 27–28/07 | Calc % State & SHAP matrix | Recharts Donut & Stacked Bar, Export PDF |
| **US-07** | Coach/Exec | Muốn nhận tư vấn GenAI & file PDF | **FR-05 (GenAI Agent)** | **A5 (Retrospective Coaching)** | 27–28/07 | GenAI API + Local Fallback | Chatbot Box, Streaming Typing FX |
| **US-08** | Judge/Tester| Muốn tua/pause replay 20 FPS mượt | **FR-06 (Replay Engine)** | **Quy định BTC (20 FPS Simulation)** | 24–25/07 | WS Timer Server $\Delta t=50ms$| Player Controls Bar, Seek Slider |
| **US-09** | Hackathon | Muốn tự động xuất 10 file CSV chuẩn | **FR-07 (CSV Exporter)** | **Quy định nộp bài BTC (1800x5, MAE<1.5)** | 27–28/07 | `AutoCSVExporter` + Validator | (Auto Script tại Backend) |