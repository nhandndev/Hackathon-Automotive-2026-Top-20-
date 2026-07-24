# 📋 BẢNG PHÂN CÔNG CÔNG VIỆC NHÓM SE (SOFTWARE ENGINEERING)

> **Dự án:** AI Fleet Management & Driver Intelligence Platform (FPTU DMS)  
> **Thành viên SE:**  
> - **NHÂN:** Backend Lead Engineer (FastAPI Core, DDD Modules, AI Integration & Gateway)  
> - **THIỆN:** Frontend Lead Engineer (Fleet Dashboard UI, 3 Views Framework, CarSky HMI Widgets)  

---

## 1. 🎯 TỔNG QUAN PHÂN CHIA VAI TRÒ SE

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                               SE TEAM RESPONSIBILITY MATRIX                              │
├────────────────────────────────────────────┬─────────────────────────────────────────────┤
│ ⚙️ NHÂN - BACKEND ENGINEER (FastAPI Core)   │ 🖥️ THIỆN - FRONTEND ENGINEER (Fleet UI App) │
├────────────────────────────────────────────┼─────────────────────────────────────────────┤
│ 1. Core Architecture & Domain Schemas      │ 1. Master Fleet Dashboard UI Layout (HTML5) │
│ 2. WebSocket 20 FPS Replay Engine          │ 2. View 1: Driver HUD (Speed, TTC Gauge)    │
│ 3. Pre-ingestion & Driver Ranking Service  │ 3. View 2: Fleet Leaderboard & GPS Map      │
│ 4. NHTSA Risk Fusion & Event Detectors     │ 4. View 3: Business Donut & Radar Charts    │
│ 5. AI Copilot LLM & Fallback Engine        │ 5. Sync Video Replay Player Component       │
│ 6. CarSky REST/WebSocket Adapter Gateway   │ 6. Floating AI Copilot Chatbox Widget UI    │
│ 7. Automated 10-CSV Exporter & Validator   │ 7. Dual-Screen CarSky HMI Integration UI    │
└────────────────────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 2. 📝 CHI TIẾT CÔNG VIỆC THEO MỤC TIÊU & USER STORIES (FEATURE MATRIX)

| STT | User Story & Feature | Công việc của NHÂN (Backend) | Công việc của THIỆN (Frontend) |
| :---: | :--- | :--- | :--- |
| **US-01** | **Live Critical Alert & Risk Reasoning** | - Xây dựng Module `risk_fusion` (NHTSA Risk Algorithm).<br>- Tự động sinh `final_risk_score` & văn bản GenAI Reasoning. | - Thiết kế UI Alert Banner nổi bật nhấp nháy đỏ.<br>- Dựng khối hiển thị **AI Risk Reasoning Card**. |
| **US-02** | **Trip Incident Replay 20 FPS** | - Xây dựng Module `streaming` (WebSocket `/ws/replay/{trip_id}`).<br>- Xử lý luồng data 50ms/frame & cơ chế Seek/Jump. | - Dựng Trình phát Video đồng bộ ADAS HUD overlay.<br>- Thiết kế thanh tua Replay Timeline 20 FPS mượt mà. |
| **US-03** | **TTC & Headway Assessment** | - Lập công thức đo khoảng cách va chạm TTC ($s$).<br>- Đánh dấu cờ vi phạm khi `min_ttc < 1.5s`. | - Thiết kế Đồng hồ kim/số **TTC Assessment Gauge**.<br>- Tô màu đỏ nguy hiểm khi sụt giảm chỉ số an toàn. |
| **US-04** | **Driver & Trip Comparison** | - Viết API `/api/v1/fleet/compare` trả về dữ liệu so sánh 5 chiều giữa 2 tài xế. | - Dựng **Radar Chart & Bar Chart** so sánh đa chiều.<br>- Thiết kế 2 thanh Dropdown chọn tài xế song song. |
| **US-05** | **Fleet Driver Safety Leaderboard** | - Xây dựng Module `fleet` & Tiến trình **Pre-ingestion Worker** tính Safe Score cho 10 xe (`T01d`..`T10d`). | - Dựng Bảng xếp hạng **Driver Safety Leaderboard**.<br>- Hiển thị Badge xếp hạng Rank #1 (Safe) -> #12 (Critical). |
| **US-06** | **AI Fleet Copilot Chatbot** | - Xây dựng Module `coaching` tích hợp LLM tiếng Việt & Fallback Rule Engine. | - Dựng khung chat **Floating AI Copilot Widget**.<br>- Thêm các nút gợi ý câu hỏi (Prompt suggestions). |
| **US-07** | **Operational Analytics & ROI** | - Xây dựng Module `insurance` tổng hợp cờ hành vi thô bạo (phanh gấp, quá tốc độ). | - Thiết kế Biểu đồ **Donut Chart** phân bổ rủi ro.<br>- Hiển thị báo cáo tiết kiệm 15-30% chi phí bảo hiểm. |

---

## 3. 🚀 PHÂN CHIA THEO PHASES PHÁT TRIỂN (AGILE SPRINT PLAN)

### ⚙️ NHÂN (Backend Lead Engineer)
* [x] **Phase 1:** Thiết lập Pydantic Schemas (`ai_vision.py`, `telemetry.py`, `risk.py`) & `csv_file_adapter.py` đọc 10 chuyến đi.
* [x] **Phase 2:** Phát triển WebSocket Replay Server 20 FPS (`replay_service.py`) & Pre-ingestion Worker cho Leaderboard.
* [x] **Phase 3:** Xây dựng LLM Coaching Service (`llm_service.py`) & Fallback Engine phục vụ Chatbot.
* [x] **Phase 4:** Phát triển `carsky_adapter.py` đẩy dữ liệu thời gian thực sang CarSky Platform (`https://carsky.io`).
* [x] **Phase 5 & 6:** Viết script `export_submission_csv.py` tự động xuất 10 file CSV chuẩn nộp BTC & kiểm thử hệ thống.

---

### 🖥️ THIỆN (Frontend Lead Engineer)
* [x] **Phase 1:** Thiết kế Bố cục Master Fleet Dashboard UI & Khung hiển thị Bảng xếp hạng Driver Leaderboard.
* [x] **Phase 2:** Xây dựng Trình phát Replay 20 FPS, Đồng hồ Tốc độ Speedometer, Gauge TTC & Bản đồ GPS Trajectory Tracker (Leaflet).
* [x] **Phase 3:** Xây dựng Widget Chatbox AI Copilot tiếng Việt & Khối văn bản AI Risk Reasoning Card.
* [x] **Phase 4:** Tích hợp Cửa sổ song song (Dual-Screen Layout) hiển thị màn hình CarSky Virtual Cockpit HMI.
* [x] **Phase 5 & 6:** Hoàn thiện trải nghiệm người dùng, chuẩn bị kịch bản lên đèn Demo 3 phút thuyết trình trước BGK.

---

## 4. 🔗 GIAO THỨC PHỐI HỢP GIỮA BACKEND (NHÂN) & FRONTEND (THIỆN)

1. **Giao thức Replay Stream:** Backend (Nhân) mở WebSocket `/ws/replay/{trip_id}` $\rightarrow$ Frontend (Thiện) kết nối lắng nghe 20 FPS để cập nhật UI.
2. **Giao thức REST API:**
   * GET `/api/v1/fleet/leaderboard`: Trả về Bảng xếp hạng 10 tài xế.
   * POST `/api/v1/coaching/chat`: Nhận tin nhắn chat tiếng Việt, trả về câu trả lời phân tích trong 1-3 giây.
   * GET `/api/v1/insurance/report`: Trả về dữ liệu biểu đồ Donut/Radar Chart.
3. **Giao thức CarSky HMI:** Backend (Nhân) gửi REST API `POST https://carsky.io/room/...` $\rightarrow$ Frontend (Thiện) hiển thị kết quả đồng bộ trên cửa sổ CarSky HMI bên phải.
