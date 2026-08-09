# BÁO CÁO KỸ THUẬT TOÀN DIỆN & HƯỚNG DẪN VẬN HÀNH (FULL 100% TECHNICAL & BUSINESS SPECIFICATION)
## DỰ ÁN: FPTU DMS VISION — DRIVER INTELLIGENCE & FLEET SAFETY PLATFORM
> **Connected Car Hackathon 2026 — Track: DMS-10 Driver Intelligence Platform**  
> *Biến dữ liệu camera và cảm biến rời rạc thành hành động cứu mạng — từ phát hiện vi ngủ đến can thiệp khẩn cấp trong vài giây.*

---

## 1. TỔNG QUAN HỆ THỐNG (SYSTEM OVERVIEW)

**FPTU DMS Vision** là nền tảng giám sát an toàn tài xế và quản lý đội xe thông minh, hợp nhất dữ liệu thời gian thực từ ba nguồn cảm biến khác nhau trên xe:
- **Road Camera:** Camera phía trước xe, phát hiện vật cản và ước lượng chỉ số va chạm Time-to-Collision (TTC).
- **Driver Camera (Cabin Cam):** Camera cabin hướng vào tài xế, phát hiện buồn ngủ (`drowsy`), mất tập trung (`distracted`), vi ngủ (`microsleep`), ngáp (`yawning`), hoặc dùng điện thoại (`using_phone`).
- **Telemetry / CAN bus:** Dữ liệu tốc độ, gia tốc, vị trí GPS, và hành vi lái.

Hệ thống được xây dựng để giải quyết ba bài toán (challenge) cốt lõi:

| Challenge | Mục tiêu | Output Chấp nhận (Submission Format) |
|---|---|---|
| **Challenge 1 — Collision Risk / TTC** | Ưóc lượng Time-to-Collision từ road camera + telemetry | `predicted_ttc` |
| **Challenge 2 — Driver Intelligence** | Phân loại trạng thái tài xế (`alert`, `drowsy`, `distracted`, `microsleep`, `yawning`, `using_phone`) | `predicted_driver_state` |
| **Challenge 3 — Risk Fusion** | Hợp nhất TTC + driver state + behavior thành điểm rủi ro tổng hợp | `predicted_risk_score` |

**Submission CSV chuẩn hóa:**
```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

**Fleet Dashboard** là lớp giao diện quản lý đội xe (React + Vite + TypeScript), nhận dữ liệu thật từ AI pipeline thông qua **FastAPI Backend (REST + WebSocket)** và hiển thị trực quan cho Fleet Manager theo thời gian thực.

---

## 2. TÍNH NĂNG CỐT LÕI & GIÁ TRỊ KINH DOANH (CORE FEATURES & BUSINESS VALUE)

> **Lưu ý:** Toàn bộ tính năng dưới đây đều có trong codebase thực tế của dự án (`SE/FE/src/components/`, `SE/BE/app/`), không phải mock-up hay concept giả định.

### 2.1. Fleet Map View — Tổng Quan Đội Xe Thời Gian Thực
- **Thành phần liên quan:** [FleetMapView.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/FleetMapView.tsx), [App.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/App.tsx)
- **Tính năng thực tế:**
  - Hiển thị danh sách toàn bộ xe/trip trên sidebar với trạng thái realtime: `LIVE`, `PENDING`, `SAFE`, `WARNING`, `CRITICAL`.
  - Mỗi xe hiển thị 3 chỉ số chính: Speed (km/h), TTC (s), Driver State.
  - Click vào xe $\rightarrow$ xem chi tiết snapshot: tốc độ cuối, TTC cuối, Safe Driving Score, Max Risk Score.
  - Hiển thị tọa độ GPS (lat/lon), thông tin bản đồ nguồn, điều kiện thời tiết (cloudiness).
  - Thống kê tổng quan: số frames, near misses, avg headway, driver state.
  - Nút hành động nhanh: Live Cameras, Trip Detail, Intervene (khi rủi ro cao), AI Copilot.
- **Giá trị kinh doanh:**
  - *Tổng quan 1 màn hình:* Fleet Manager nhìn toàn bộ đội xe và trạng thái rủi ro từ một dashboard duy nhất — không cần gọi điện hỏi từng tài xế.
  - *Phản ứng nhanh:* Xe `CRITICAL` được highlight đỏ ngay lập tức, Manager can thiệp trong vài giây thay vì cuối ngày mới biết.
  - *Ra quyết định dựa trên dữ liệu:* Mọi trạng thái đều từ AI contract thật (TTC, driver state, risk score) — không cảm tính.

---

### 2.2. Vehicle Live View — Giám Sát Camera & Rủi Ro Realtime
- **Thành phần liên quan:** [VehicleLiveView.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/VehicleLiveView.tsx), [LiveCameraFrame.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/LiveCameraFrame.tsx)
- **Tính năng thực tế:**
  - Hiển thị 2 luồng camera đồng thời: Road Cam (phía trước) và Cabin Cam (tài xế) — streaming frame thật từ AI pipeline.
  - **Risk Score Gauge:** Vòng tròn trực quan hiển thị điểm rủi ro realtime (0–100).
  - **TTC (Time-to-Collision):** Hiển thị lớn, nổi bật, cập nhật liên tục.
  - **Active Safety Alert Banner:** Hiển thị severity (`critical`/`warning`), loại cảnh báo (`microsleep`, `drowsy_driving`, `harsh_brake`...) và recommended action.
  - Tốc độ hiện tại (km/h) cập nhật realtime.
  - **Alertness Score:** Phần trăm tỉnh táo của tài xế từ AI.
  - **Decision Event Log:** Bảng sự kiện thời gian thực từ WebSocket (`WS /api/v1/ws/live`): thời gian, loại event, severity, trạng thái (`open`/`resolved`).
  - Trạng thái kết nối: `LIVE` hoặc `OFFLINE`.
  - Nút can thiệp khẩn cấp khi có alert active. Polling snapshot mỗi 200ms để cập nhật liên tục.
- **Giá trị kinh doanh:**
  - *Giám sát trực quan:* Manager xem được camera tài xế VÀ đường cùng lúc — biết chính xác tài xế có tỉnh táo không và đường phía trước có nguy hiểm không.
  - *Phát hiện microsleep tức thì:* AI phát hiện tài xế vi ngủ $\rightarrow$ cảnh báo `CRITICAL` hiển thị ngay $\rightarrow$ Manager can thiệp trong vài giây, cứu mạng thực sự.
  - *Bằng chứng trực quan:* Camera frames + event log = bằng chứng pháp lý khi xảy ra sự cố.

---

### 2.3. Trip Detail View — Phân Tích Chi Tiết Chuyến Đi
- **Thành phần liên quan:** [TripDetailView.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/TripDetailView.tsx)
- **Tính năng thực tế:**
  - **Synchronized AI Camera Frames:** Cabin Cam + Road Cam đồng bộ theo từng `frame_id`.
  - **Live Telemetry Chart:** Biểu đồ đường realtime hiển thị Speed (km/h) và C3 Risk Score theo thời gian, giữ 120 điểm gần nhất.
  - **Challenge 3 Scores Panel:** SAFE Score (= 100 − Risk Score), RISK Score, TTC.
  - **Realtime Evidence Panel:** Raw data từ AI: `frame_id`, `timestamp`, `speed`, `TTC`, `driver_state`, `driver_confidence`, `alertness_score`, `risk_score`.
  - **Decision Events Panel:** Đếm và liệt kê các loại event (`microsleep` ×3, `drowsy_driving` ×2, `harsh_brake` ×1...).
  - Trạng thái kết nối `LIVE`/`OFFLINE`.
- **Giá trị kinh doanh:**
  - *Hiểu nguyên nhân rủi ro:* Manager không chỉ biết "có nguy hiểm" mà biết tại sao — `drowsy`? `distracted`? TTC thấp? `speeding`? — từ đó đưa ra hành động đúng.
  - *Audit trail minh bạch:* Mỗi frame có `timestamp`, `driver_state`, `risk_score` — truy vết chính xác thời điểm xảy ra sự kiện.
  - *Dữ liệu cho coaching:* Biết chính xác tài xế gặp vấn đề gì ở thời điểm nào để đào tạo mục tiêu.

---

### 2.4. Driver Ranking & Safety Scoring — Xếp Hạng & Chấm Điểm Tài Xế
- **Thành phần liên quan:** [DriverRankingView.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/DriverRankingView.tsx), [DriverRankingAnalysisPage.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/DriverRankingAnalysisPage.tsx)
- **Tính năng thực tế:**
  - Bảng xếp hạng (Leaderboard) toàn bộ tài xế, sắp xếp theo Safety Score (0–100).
  - Mỗi tài xế hiển thị: Rank #, Score, Risk Level (`SAFE`/`WATCH`/`AT_RISK`/`CRITICAL`), Critical Events, Coaching Priority (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`).
  - **Safety Score Formula:** Tính toán thật từ dữ liệu AI contract:
    $$Score = 100 - (\text{avgRisk} \times 0.2 + \text{maxRisk} \times 0.15 + \text{criticalEvents} \times 5 + \dots)$$
  - **Driver Detail Panel:** Bar chart trực quan (Risk, Speeding, Tailgating, Distraction, Fatigue, Harsh Events) và metrics chi tiết.
  - **Fleet Summary KPIs:** Drivers ranked, Fleet avg score, Need coaching, Critical signals.
  - **Explain Ranking:** Mở `DriverRankingAnalysisPage` giải thích chi tiết tại sao tài xế bị trừ điểm, có audit trail từng nhóm rủi ro.
  - **Local Analysis tự động sinh:** Executive summary, score audit trail, top risk factors kèm evidence (`frame_id`, `timestamp`...), fleet comparison, recommended action plan, coaching plan.
- **Giá trị kinh doanh:**
  - *Quản lý nhân sự dựa trên dữ liệu:* Biết chính xác ai lái tốt, ai lái nguy hiểm — không đánh giá cảm tính.
  - *Ưu tiên coaching hiệu quả:* Tập trung vào tài xế `CRITICAL`/`AT_RISK` với vấn đề cụ thể.
  - *Thi đua lái xe an toàn:* Leaderboard tạo động lực cải thiện cho tài xế.
  - *Audit minh bạch:* Explain Ranking cho thấy chính xác tại sao score bị trừ kèm evidence frame-by-frame.

---

### 2.5. Fleet AI Copilot — Trợ Lý AI Phân Tích Đội Xe Thời Gian Thực
- **Thành phần liên quan:** [AICopilotDrawer.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/AICopilotDrawer.tsx), [server.ts](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/server.ts) (Endpoint `/api/copilot`)
- **Tính năng thực tế:**
  - Chat interface dạng slide-over drawer — Fleet Manager hỏi bằng tiếng Việt hoặc tiếng Anh, AI trả lời realtime.
  - Gọi AI thật qua **AWS Bedrock Runtime** (model `deepseek.v3.2`, region `ap-southeast-2`) — không fake response.
  - **Context-aware:** Mỗi câu hỏi gửi kèm dữ liệu đội xe thật (`trip_id`, `metadata`, `driver_summary`, `trip_aggregate`) để AI phân tích chính xác.
  - **Rich Response Cards:**
    - `DRI_RISK Card`: Tài xế rủi ro cao nhất kèm lý do chi tiết.
    - `RECOMMENDATION Card`: Khuyến nghị hành động + nút gửi lịch nghỉ tức thì.
    - `COMPARISON Card`: So sánh xe/tài xế, mở Fleet Report tab mới.
  - **Quick Suggestion Chips:** *"So sánh 2 tài xế"*, *"Xe nào cần bảo trì?"*, *"Báo cáo an toàn tuần này"*.
  - Lưu lịch sử chat trong session.
- **Giá trị kinh doanh:**
  - *Natural language insights:* Manager không cần đọc biểu đồ phức tạp — hỏi "Tài xế nào nguy hiểm nhất?" $\rightarrow$ AI trả lời ngay số liệu cụ thể.
  - *Quyết định nhanh hơn:* Thay vì đọc 10 trip reports, hỏi AI 1 câu $\rightarrow$ có câu trả lời trong vài giây.
  - *Actionable recommendations:* AI gợi ý hành động cụ thể (gửi lịch nghỉ, coaching, can thiệp khẩn cấp).

---

### 2.6. Copilot Fleet Report — Báo Cáo AI Tự Động Toàn Diện
- **Thành phần liên quan:** [CopilotFleetReportPage.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/CopilotFleetReportPage.tsx), (Endpoint `/api/copilot/report`)
- **Tính năng thực tế & Chi tiết Cấu trúc Báo cáo:**
  - **3 Loại báo cáo chuyên sâu:**
    1. `Vehicle Safety Comparison` (So sánh an toàn giữa các phương tiện).
    2. `Vehicle Maintenance Priority Report` (Đánh giá ưu tiên bảo trì xe dựa trên harsh events và rủi ro).
    3. `Fleet Safety Executive Report` (Báo cáo an toàn tổng quan gửi Ban Lãnh đạo).
  - **Vehicle Cards & Ranking Matrix:** Mỗi xe hiển thị Score, Rank, Max Risk, Events, Risk Level (`SAFE`/`WATCH`/`AT_RISK`/`CRITICAL`), Driver Profile.
  - **Business KPI Table:** So sánh tổng điểm an toàn, chỉ số TTC, tỉ lệ mất tập trung (`distracted %`), số sự kiện nguy hiểm giữa **Fleet Average** vs **Best Driver**.
  - **Top 5 Critical Event Log per Vehicle:** Bảng liệt kê 5 sự kiện nguy hiểm nhất từng xe gồm `timestamp`, `type` (`Drowsy`, `Harsh brake`, `Tailgating`), `severity`, chỉ số `risk_score`, `TTC` và `alertness`.
  - **Bedrock AI Copilot Executive Summary:** Gọi AWS Bedrock sinh nhận xét chuyên sâu bằng tiếng Việt, phân tích nguyên nhân gốc rễ và kế hoạch đào tạo tài xế.
  - **Nút Export Report:** Hỗ trợ mở tab mới và in/xuất file PDF A4 phục vụ lưu trữ pháp lý hoặc gửi báo cáo.
- **Giá trị kinh doanh:**
  - *Báo cáo chuyên nghiệp tự động:* Không cần nhân viên ngồi tổng hợp — AI tự sinh report từ dữ liệu thật.
  - *Executive-ready:* Ban lãnh đạo đọc ngay — có KPI, so sánh, event log, AI insight.
  - *Benchmark liên tục:* So sánh Fleet Average vs Best Driver $\rightarrow$ biết đội xe đang ở đâu và cần cải thiện gì.

---

### 2.7. Emergency Intervention — Can Thiệp Khẩn Cấp
- **Thành phần liên quan:** [InterventionModal.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/InterventionModal.tsx)
- **Tính năng thực tế:**
  - Modal can thiệp khẩn cấp — hiển thị khi Fleet Manager nhấn "Intervene" cho xe rủi ro cao.
  - Hiển thị trạng thái tài xế hiện tại, điểm tỉnh táo (`alertness %`), tốc độ hiện tại.
  - **AI Risk Reasoning:** $\text{Base Risk} \times \text{Driver Factor} = \text{Final Risk Score}$ — giải thích tại sao AI đánh giá nguy hiểm.
  - **3 Phương án can thiệp:**
    1. *Phát chuông báo động Cabin khẩn cấp* xuống xe.
    2. *Gửi lệnh bắt buộc dừng xe nghỉ 30 phút*.
    3. *Gọi điện trực tiếp cho tài xế (Voice Call)*.
  - Confirmation UI xác nhận đã gửi lệnh thành công.
- **Giá trị kinh doanh:**
  - *Cứu mạng thực sự:* Phát hiện microsleep ở tốc độ cao $\rightarrow$ can thiệp trong vài giây.
  - *Quy trình can thiệp chuẩn hóa:* 3 mức can thiệp rõ ràng — không hoảng loạn, đúng quy trình.
  - *Trách nhiệm rõ ràng:* Lưu vết log ai đã can thiệp, khi nào — làm bằng chứng tuân thủ.

---

### 2.8. Performance Insights — Tổng Hợp Hiệu Suất Chuyến Đi
- **Thành phần liên quan:** [PerformanceInsightsView.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/components/PerformanceInsightsView.tsx)
- **Tính năng thực tế:**
  - 6 KPI cards lớn cho mỗi trip: Safe driving score, Near misses, Maximum risk score, Average headway, Microsleep count, Average alertness.
  - Tất cả dữ liệu từ AI contract thật (`trip_aggregate` + `driver_summary`).
- **Giá trị kinh doanh:**
  - *Dashboard KPI nhanh:* Manager nhìn 6 con số $\rightarrow$ biết ngay chuyến đi an toàn hay nguy hiểm.
  - *So sánh hiệu suất:* So sánh giữa các trip/tài xế — ai có microsleep nhiều? ai headway thấp?

---

### 2.9. WebSocket Realtime & Alert System — Hệ Thống Cảnh Báo Thời Gian Thực
- **Thành phần liên quan:** [App.tsx](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/src/App.tsx) (WebSocket client), Backend endpoint `/api/v1/alerts/live`
- **Tính năng thực tế:**
  - WebSocket persistent connection — nhận `DecisionEvent` realtime từ Backend khi AI pipeline phát hiện sự kiện.
  - **Alert Schema chuẩn:** `event_id`, `trip_id`, `frame_id`, `trip_timestamp_ms`, `status` (`open`/`resolved`), `alert_type`, `severity` (`info`/`warning`/`critical`), `confidence`, `recommended_action`, `evidence`.
  - HTTP fallback — load 1000 alert gần nhất khi mở dashboard.
  - Auto trip refresh — poll trips mỗi 1 giây, tự động follow trip đang `running`.
  - Merge & deduplicate — cùng `event_id` chỉ hiển thị 1 lần.
  - Trạng thái kết nối `LIVE`/`OFFLINE` hiển thị khắp dashboard.
- **Giá trị kinh doanh:**
  - *Zero-delay notification:* Sự kiện nguy hiểm xảy ra $\rightarrow$ Manager biết ngay lập tức.
  - *Continuous monitoring:* Dashboard cập nhật liên tục — không cần refresh thủ công.
  - *Không bỏ sót:* Merge + deduplicate đảm bảo mọi event đều xử lý đúng 1 lần.

---

### 2.10. CarSky / Android HMI — Cảnh Báo Trực Tiếp Cho Tài Xế
- **Thành phần liên quan:** `SE/HMI/`, `SE/BE/scripts/carsky_phase05.py`, CarSky Blueprint
- **Tính năng thực tế:**
  - CarSky Blueprint với 3 nodes: `DMS Signal Broker`, `DMS HMI Bridge`, `DMS Android HMI`.
  - KUKSA custom signals: `Vehicle.Speed`, `Vehicle.ADAS.FinalRiskScore`, `Vehicle.Driver.State`, `Vehicle.ADAS.DisplaySeverity`, `Vehicle.ADAS.AIStatus`.
  - Gửi scenario safe/warning/critical lên CarSky $\rightarrow$ Signal Watch hiển thị.
  - Android HMI APK có UI cảnh báo 3 mức: an toàn (xanh), cảnh báo (vàng), nguy hiểm (đỏ).
- **Giá trị kinh doanh:**
  - *Cảnh báo closed-loop:* Cả manager VÀ tài xế đều nhận cảnh báo trực tiếp trên màn hình HMI trên xe.
  - *Phản ứng tức thì:* Tài xế buồn ngủ $\rightarrow$ HMI đổi màu đỏ + báo động $\rightarrow$ dừng nghỉ ngay.
  - *Tiêu chuẩn automotive thực tế:* Sử dụng KUKSA VSS và CarSky — chuẩn ô tô quốc tế.

---

## 3. KIẾN TRÚC END-TO-END (END-TO-END DATAFLOW ARCHITECTURE)

Luồng dữ liệu xuyên suốt hệ thống, từ cảm biến đầu vào đến hành động can thiệp và cảnh báo tài xế:

```text
BTC Dataset / Road Camera / Driver Camera / Telemetry
                        │
                        ▼
            AI Core / Decision Engine
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
Challenge 1: TTC  Challenge 2: DMS  Challenge 3: Risk Fusion
       └────────────────┼────────────────┘
                        ▼
             DecisionEvent / AITrip
                        │
                        ▼
                 FastAPI Backend
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
  REST APIs      WebSocket realtime   CarSky Adapter
       │                │                │
       ▼                ▼                ▼
Fleet Dashboard  Live event stream   KUKSA / VHAL / HMI
       │
       ▼
Fleet AI Copilot (qua AWS Bedrock)
```

**Nguyên tắc vòng lặp an toàn khép kín (Closed-Loop Safety):**
Kiến trúc này đảm bảo dữ liệu AI thật (TTC, driver state, risk score) chảy liên tục từ cảm biến đến ba điểm chạm cuối cùng: **Fleet Manager** (qua Dashboard), **Tài xế** (qua HMI trong xe), và **Trợ lý AI** (qua Copilot).

---

## 4. BẢNG KPI THỰC TẾ TRONG DASHBOARD (REALTIME DASHBOARD KPIS)

| KPI | Nguồn dữ liệu | Hiển thị ở đâu trên UI |
|---|---|---|
| **Safe Driving Score (0–100)** | `trip_aggregate.safe_driving_score` + ranking formula | Fleet Map, Ranking, Insights |
| **Risk Score (0–100)** | `risk.final_risk_score` (Challenge 3) | Live View, Trip Detail, Ranking |
| **TTC — Time to Collision (s)** | `min_ttc` (Challenge 1) | Live View, Trip Detail, Fleet Map |
| **Driver State** | `driver.state` (Challenge 2) | Live View, Trip Detail, Fleet Map |
| **Alertness Score (%)** | `driver.alertness_score` | Live View, Trip Detail, Insights |
| **Microsleep Count** | `driver_summary.microsleep_count` | Insights, Ranking |
| **Near Miss Count** | `trip_aggregate.near_miss_count` | Fleet Map, Ranking, Insights |
| **Harsh Events (brake/accel/corner)**| `behavior_flags` + aggregate | Ranking |
| **Speeding %** | `trip_aggregate.speeding_pct_time` | Ranking |
| **Tailgating %** | `trip_aggregate.tailgating_pct_time` | Ranking |
| **Distracted %** | `driver_summary.state_distribution_pct.distracted` | Ranking |
| **Average Headway (s)** | `trip_aggregate.avg_headway_sec` | Fleet Map, Insights |
| **Coaching Priority** | Computed từ Risk Level (`LOW`/`MED`/`HIGH`/`CRITICAL`) | Ranking |

---

## 5. HƯỚNG DẪN KHỞI CHẠY & KIỂM THỬ THỰC TẾ (RUNBOOK FOR TESTING)

### Step 1: Kích hoạt môi trường Python từ `HACKATHON/`

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt
python AI\scripts\preflight_ai.py
```

### Step 2: Cài Fleet Dashboard dependencies một lần

```powershell
Push-Location SE\FE
npm install
npm run build
Pop-Location
```

### Step 3: Local end-to-end demo — AI + SE Backend + Fleet Dashboard

Runner tự mở FastAPI Backend ở `127.0.0.1:8000`, Fleet Dashboard ở
`127.0.0.1:3000`, rồi chạy AI pipeline.

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir ..\Practice_Dataset `
  -DriverModel AI\models\driver_state_current.joblib `
  -OpenDashboard `
  -SkipCarSkyPreflight
```

Nếu test model candidate:

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir ..\Practice_Dataset `
  -DriverModel AI\models\modelv5-final.joblib `
  -OpenDashboard `
  -SkipCarSkyPreflight
```

### Step 4: Full demo có CarSky

Chỉ bỏ `-SkipCarSkyPreflight` khi `SE\BE\.env` đã có credential external thật:

```env
CARSKY_ENABLED=true
CARSKY_MODE=external
CARSKY_BASE_URL=...
CARSKY_API_KEY=...
CARSKY_ROOM_ID=...
CARSKY_NODE_KEY=...
CARSKY_ANDROID_NODE_KEY=...
```

---

## 6. KẾT LUẬN & ĐIỂM KHÁC BIỆT DỰ ÁN (SUMMARY & VALUE PROPOSITION)

Fleet Dashboard trong dự án **FPTU DMS Vision** là một **Driver Intelligence Platform** — nền tảng giám sát an toàn tài xế thông minh vượt trội với 7 lợi thế cạnh tranh:
1. **AI-First:** Mọi dữ liệu đều đến từ AI pipeline thật (TTC, driver state, risk fusion) — không chỉ hiển thị vị trí GPS rời rạc.
2. **Dual-Camera Realtime:** Xem đồng thời camera cabin và camera đường phía trước — giám sát toàn diện cả tài xế lẫn môi trường lái.
3. **Driver Scoring có Audit Trail:** Điểm số có công thức minh bạch, Explain Ranking kèm bằng chứng `frame_id` và `timestamp`.
4. **AWS Bedrock AI Copilot Thật:** Gọi Bedrock LLM thật (`deepseek.v3.2`), trả lời bằng tiếng Việt, phân tích trên dữ liệu đội xe thật.
5. **Can Thiệp Khẩn Cấp Tức Thì:** Phát hiện vi ngủ (microsleep) $\rightarrow$ Manager bấm nút can thiệp $\rightarrow$ phát chuông báo động cabin trong vài giây.
6. **Cảnh Báo CarSky HMI Trong Xe:** Tài xế nhận cảnh báo trực tiếp qua Android Automotive OS HMI.
7. **Báo Cáo Tự Động AI:** Tự động tạo 3 loại báo cáo an toàn chuyên sâu ready-to-print.

> **Giá trị cốt lõi:** Biến dữ liệu camera và cảm biến rời rạc thành hành động cứu mạng — từ phát hiện vi ngủ đến can thiệp khẩn cấp trong vài giây.

---
*Báo cáo Kỹ thuật & Vận hành được tổng hợp trực tiếp từ mã nguồn sản phẩm thực tế của dự án FPTU DMS Vision.*
