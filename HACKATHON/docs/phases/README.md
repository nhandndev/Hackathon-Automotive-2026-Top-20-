# TÀI LIỆU HƯỚNG DẪN TỔNG QUAN & DỮ LIỆU ĐÒN BẨY CÁC PHASES (PHASES MASTER INDEX)

> **Dự án**: AI Fleet Management & Driver Intelligence Platform  
> **Tài liệu gốc**: `SYSTEM_ALIGNMENT_SE_AI.md` & `KeHoach_Dashboard_Agile_Thien_Nhan.md`  
> **Đối tượng sử dụng**: **User (Fleet Manager / Team Leader)** để review & **AI Assistant / Developer** để thực thi code.

---

## DẠN Ý THƯ MỤC CÁC PHASES (`phases/`)

Toàn bộ kế hoạch sản xuất và tích hợp dự án đã được chi tiết hóa thành **4 Phase hoàn chỉnh**:

```text
phases/
├── README.md                           # Master Index & Hướng dẫn Review/Code này
├── Phase_01_Core_SE_AI_Alignment.md    # Phase 1: Nền tảng cốt lõi AI & SE, Payload Schema & Driver Ranking
├── Phase_02_Dashboard_Replay_Engine.md # Phase 2: Master Fleet Dashboard 3 Views & 20 FPS Replay Server
├── Phase_03_AI_Copilot_Coaching_Agent.md# Phase 3: AI Agent Chatbot Box & GenAI Risk Reasoning Card
├── Phase_04_CarSky_HMI_Integration.md # Phase 4: Hướng dẫn chi tiết kết nối dữ liệu AI/SE sang CarSky HMI
├── Phase_05_Submission_and_CarSky_Demo_Guidelines.md # Phase 5: Quy trình đóng gói nộp bài 10 file CSV & Video Demo CarSky (+15đ BTC)
└── Phase_06_Complete_Demo_Runbook_and_Pitching_Script.md # Phase 6: Kịch bản lên đèn Demo hoàn chỉnh 3 phút & Lời thoại Pitching trước BGK
```

---

## TỔNG QUAN NỘI DUNG VÀ MỤC TIÊU CỦA TỪNG PHASE

| Phase | Bài Toán & Mục Tiêu Của Phase (Cho User & AI) | Kết Quả Đầu Ra Cho User Review | Mã Nguồn Sẵn Cho AI Code |
| :---: | :--- | :--- | :--- |
| **Phase 1** | **Core SE & AI System Alignment**<br>- Phân định ranh giới công việc AI vs SE.<br>- Thống nhất Data Contract JSON 20 FPS.<br>- Duyệt tiêu chí Driver Safety Leaderboard. | Ma trận phân việc + Công thức tính Safe Score & Bảng phân cấp màu thứ hạng. | File Pydantic Schema `telemetry.py` |
| **Phase 2** | **Dashboard & 20 FPS Replay Engine**<br>- Trực quan hóa 3 View Dashboard.<br>- Replay đồng bộ 20 FPS (50ms/frame).<br>- GPS Trajectory Live Tracking. | Đánh giá 3 Màn hình (Driver HUD, Fleet View, Business Report). | FastAPI WebSocket Server + React `ReplayContext` |
| **Phase 3** | **AI Copilot & GenAI Coaching Agent**<br>- Trợ lý giao tiếp Tiếng Việt (NL2Query).<br>- GenAI Risk Reasoning Card.<br>- Đào tạo tài xế dựa trên bằng chứng. | Trải nghiệm gõ câu hỏi tự nhiên nhận câu trả lời + Action Buttons. | FastAPI Router `/api/v1/copilot/chat` + Chatbox Widget UI |
| **Phase 4** | **CarSky HMI Integration (+15đ BTC)**<br>- Mở rộng từ Dashboard xuống HMI Cockpit.<br>- Thao tác kết nối Output AI/SE sang CarSky HMI.<br>- Đẩy tin nhắn Coaching sang màn hình xe. | Đảm bảo kết nối dữ liệu mượt mà từ `T01d.json` $\rightarrow$ CarSky HMI. | Integration Adapter `carsky_adapter.py` + Script Luau |
| **Phase 5** | **Submission & CarSky Demo Guidelines**<br>- Quy chuẩn 10 file CSV (1800x5, MAE < 1.5).<br>- Đóng gói Video Demo Dual-Screen & Blueprint.<br>- Script tự động export & validate CSV. | Đảm bảo nộp đủ 10 CSV + Video minh chứng nhận trọn +15 điểm thưởng BTC. | Script `export_submission_csv.py` & `validate_submission.py` |
| **Phase 6** | **Complete Demo Runbook & Pitching Script**<br>- Kịch bản lên đèn demo 3 phút từng giây.<br>- Lời thoại pitch giá trị Business trước BGK.<br>- Tương tác Dual-Screen giữa Dashboard & CarSky HMI. | Tự tin trình diễn demo mượt mà, ấn tượng, ăn trọn điểm thưởng của BGK/BTC. | Cấu hình Dual-Screen Layout & Pre-demo Checklist |

---

## HƯỚNG DẪN REVIEW VÀ THỰC THI (CHO USER & AI)

### 1. Dành cho User (Reviewer)
1. Đọc phần **Mục tiêu và Bài toán thực tế** ở đầu mỗi file Phase để hiểu Phase đó giải quyết vấn đề gì.
2. Đọc bảng **Quy tắc & Tiêu chí** để xem giao diện/tính năng có đúng yêu cầu kinh doanh và quản lý đội xe hay không.
3. Đối chiếu với mục **Tiêu chí Review & Nghiệm thu** ở cuối mỗi Phase để tích chọn nghiệm thu.

### 2. Dành cho AI Assistant / Developer (Implementer)
1. Đọc phần **Data Contract / JSON Payload** để nắm chuẩn giao tiếp.
2. Copy trực tiếp các đoạn mã nguồn trong mục **CODE IMPLEMENTATION SPEC** vào thư mục dự án tương ứng.
3. Khởi chạy và kiểm thử theo các bước lệnh trong tài liệu.
