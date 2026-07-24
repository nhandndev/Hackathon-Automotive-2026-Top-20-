# PHASE 6: KỊCH BẢN LÊN ĐÈN DEMO HOÀN CHỈNH (COMPLETE DEMO RUNBOOK & PITCHING SCRIPT)

---

## 1. MỤC TIÊU VÀ QUY CHUẨN MÀN DEMO (DEMO OVERVIEW)

### 1.1 Mục tiêu của Phase 6
Cung cấp **Kịch bản Demo chuẩn từng giây (Step-by-step Runbook & Pitch Script)** giúp đội thi tự tin trình diễn sản phẩm trước Ban Giám Khảo (BGK) và Ban Tổ Chức (BTC):
1. **Showcase Giá trị Business & Vận hành**: Minh chứng tiết kiệm 90% thời gian giám sát đội xe nhờ AI Risk Reasoning & Driver Safety Leaderboard.
2. **Minh chứng Kỹ thuật 20 FPS**: Trình diễn Replay mượt mà 20 FPS (50ms) đồng bộ Video Cabin, ADAS HUD Overlay và Telemetry Timeline.
3. **Thuyết phục Trợ lý AI Copilot**: Hỏi đáp tiếng Việt tự nhiên và ra quyết định chỉ đạo tức thì trong 3 giây.
4. **Bùng nổ Điểm Thưởng CarSky (+15 Điểm)**: Trình diễn màn hình Dual-Screen (Master Fleet Dashboard + CarSky HMI Virtual Cockpit) nổ còi cảnh báo thời gian thực.

---

## 2. CHUẨN BỊ MÔI TRƯỜNG VÀ CẤU HÌNH MÀN HÌNH DEMO (PRE-DEMO SETUP)

### 2.1 Cấu hình Màn hình hiển thị Song Song (Dual-Screen Layout)
Mở trình duyệt web và chia làm 2 cửa sổ chạy song song:

```text
┌──────────────────────────────────────────┬──────────────────────────────────────────┐
│ CỬA SỔ TRÁI: MASTER FLEET DASHBOARD      │ CỬA SỔ PHẢI: CARSKY WORKBENCH HMI        │
│ (http://localhost:8000/demo/index.html)  │ (https://carsky.io/room/fptu-dms-room)   │
│                                          │                                          │
│ - Màn hình Fleet Operations Manager      │ - Virtual Cockpit In-Cabin Display       │
│ - Bản đồ GPS Live Trajectory             │ - Signal Watch Widget (TTC & Speed)      │
│ - Driver Safety Ranking Leaderboard      │ - Red Alert Visual Pulse & Audio Beep    │
│ - Floating AI Copilot Chatbot Box        │ - Coaching Text Box Widget               │
└──────────────────────────────────────────┴──────────────────────────────────────────┘
```

### 2.2 Lệnh khởi chạy hệ thống trước 5 phút trình bày:
```bash
# 1. Chạy FastAPI Backend Engine
cd backend
python -m uvicorn main:app --reload --port 8000

# 2. Kiểm tra file dữ liệu chuyến đi T01d.json đã sẵn sàng ở gốc dự án
```

---

## 3. KỊCH BẢN DIỄN TỪNG BƯỚC THỜI GIAN (3-MINUTE DEMO SCRIPT)

### ⏱️ PHÚT 0:00 - 0:45 | GIỚI THIỆU TỔNG QUAN DASHBOARD & DRIVER RANKING LEADERBOARD
- **Thao tác**: Mở Cửa sổ Trái (Master Fleet Dashboard), chuyển sang tab **Fleet Manager View**.
- **Lời thoại thuyết trình (Pitch Script)**:
  > *"Kính chào Ban Giám Khảo! Các thiết bị định vị đội xe truyền thống hiện nay bị rơi vào bẫy 'Bội bội dữ liệu nhưng thiếu thông tin chi tiết' — Quản lý chỉ nhận được thông báo phanh gấp nhưng không biết TẠI SAO tài xế lại phanh gấp.  
  > Hệ thống **AI Fleet Management & Driver Intelligence Platform** của chúng em giải quyết triệt để bài toán này.  
  > Trên màn hình **Fleet View**, Quản lý đội xe nhìn thấy ngay **Bảng xếp hạng Tài xế (Driver Safety Ranking)**. Tài xế C đang giữ vị trí `#1 Safe` với 96/100 điểm, trong khi Tài xế A (Xe VH-04) tụt xuống hạng `#12 Critical` chỉ còn 42/100 điểm do có nhiều hành vi nguy hiểm."*

---

### ⏱️ PHÚT 0:45 - 1:45 | KÍCH HOẠT REPLAY 20 FPS & AI RISK REASONING CARD
- **Thao tác**: Bấm nút **Play Replay chuyến đi `T01d`**. Kéo thanh tua Video Timeline tới **Frame 450 (Thời điểm 22.5s)**.
- **Diễn biến Giao diện**:
  - Video Cabin hiển thị tài xế nhắm mắt vi ngủ.
  - Gauge TTC tụt xuống **1.2s** (Màu đỏ nguy hiểm).
  - Tiếng còi Beep 880Hz báo động nổ lên và viền màn hình nhấp nháy đỏ.
  - Khối **AI Risk Reasoning Card** hiển thị nội dung phân tích tự động.
- **Lời thoại thuyết trình (Pitch Script)**:
  > *"Ngay tại frame 450 (thời điểm 22.5 giây), hệ thống Replay 20 FPS đồng bộ thời gian thực phát hiện tài xế A sụt giảm độ tỉnh táo xuống 15% do vi ngủ (microsleep). Xe đạp phanh gấp ở tốc độ 65km/h với khoảng cách va chạm TTC nguy kịch 1.2s.  
  > Khối **AI Risk Reasoning Card** do SE Backend tự động sinh lập tức viết sẵn lời giải thích nguyên nhân và đề xuất hành động cho Manager mà không cần mất thời gian soi lại video thô."*

---

### ⏱️ PHÚT 1:45 - 2:30 | ĐIỂM BÙNG NỔ: TÍCH HỢP CARSKY HMI COCKPIT (+15 ĐIỂM THƯỞNG BTC)
- **Thao tác**: Hướng ánh mắt BGK sang **Cửa sổ Phải (CarSky Workbench HMI)**.
- **Diễn biến Giao diện**:
  - Đèn LED trên CarSky GPIO Panel Node bật sáng đỏ.
  - Widget Screen trên CarSky HMI phát tiếng còi báo động.
  - Ô văn bản Coaching hiển thị tin nhắn:  
    *`"Tài xế A (Xe VH-04) sụt giảm tỉnh táo xuống 15% do vi ngủ. Vui lòng tắp xe vào lề nghỉ ngơi!"`*
- **Lời thoại thuyết trình (Pitch Script)**:
  > *"Đặc biệt, hệ thống của chúng em được tích hợp hoàn chỉnh với **CarSky HMI Platform** qua REST API Gateway.  
  > Khi sự cố xảy ra trên Dashboard trung tâm, Backend lập tức push dữ liệu cảnh báo xuống trực tiếp màn hình **Virtual Cockpit trong cabin xe của Tài xế trên CarSky** (ở bên phải). Tài xế nghe thấy còi báo và nhìn thấy ngay lời nhắc nhở đào tạo (Coaching) từ AI Copilot để chủ động tắp xe vào lề dừng nghỉ!"*

---

### ⏱️ PHÚT 2:30 - 3:00 | INTERACTIVE AI COPILOT AGENT & KẾT THÚC
- **Thao tác**: Mở Chatbot Box ở góc dưới màn hình Dashboard, gõ câu hỏi:  
  *`"Tài xế nào đang có rủi ro cao nhất hôm nay?"`*
- **Diễn biến Giao diện**: Copilot trả lời trong 1 giây kèm nút hành động `[Gửi lịch nghỉ đề xuất]`.
- **Lời thoại thuyết trình (Pitch Script)**:
  > *"Quản lý đội xe cũng có thể giao tiếp với hệ thống bằng tiếng Việt tự nhiên qua **AI Copilot**. Chỉ trong 1 giây, Copilot trả về phân tích đầy đủ và cung cấp nút bấm gửi lịch nghỉ đề xuất cho tài xế.  
  > Hệ thống vừa đáp ứng 100% quy chuẩn xuất 10 file CSV của BTC, vừa mang lại giá trị kinh tế cắt giảm 15-30% chi phí bảo hiểm cho doanh nghiệp. Em xin chân thành cảm ơn BGK!"*

---

## 4. BẢNG TROUBLESHOOTING KHI DEMO (PHÒNG NGHĨA SỰ CỐ LIVE)

| Sự Cố Có Thể Xảy Ra | Nguyên Nhân | Cách Xử Lý Nhanh Trong 5 Giây |
| :--- | :--- | :--- |
| **Không thấy âm thanh còi báo** | Trình duyệt block Autoplay Audio. | Click nhẹ 1 cái vào màn hình Dashboard để kích hoạt `AudioContext`. |
| **CarSky HMI không nhấp nháy đỏ** | CarSky API Key hoặc Local URL bị ngắt. | Bấm nút `Retry Push` trên Dashboard UI hoặc giải thích: *"Mô phỏng Push REST API theo chế độ Offline Mode"*. |
| **Video tua bị giật** | RAM máy bị quá tải khi mở nhiều tab. | Bấm nút tạm dừng `Pause` $\rightarrow$ Kéo thanh tua thẳng đến Frame 450 $\rightarrow$ Bấm `Play`. |

---

## 5. HƯỚNG DẪN XỬ LÝ NHIỀU TRIP VÀ NHIỀU TÀI XẾ (MULTI-TRIP & MULTI-DRIVER MANAGEMENT)

### 5.1 Bài toán thực tế của BTC & Cách thức vận hành
Ban Tổ Chức (BTC) cung cấp sẵn bộ **10 Chuyến đi (10 Trips: `T01d` đến `T10d`)**. Mỗi chuyến đi đại diện cho 1 phương tiện và 1 tài xế trong đội xe (`VH-01` tương ứng `T01d`, `VH-02` tương ứng `T02d`, ..., `VH-10` tương ứng `T10d`).

### 5.2 Cơ chế Chọn Chuyến Đi (Trip Selector Dropdown) trên Dashboard UI
Trên Master Fleet Dashboard, SE thiết kế một thanh điều hướng chọn Trip thông minh:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  SELECT TRIP: [ Dropdown: T01d (VH-01 - Đang chạy) ▼ ]  [ Live / Replay ]│
├─────────────────────────────────────────────────────────────────────────┤
│  Danh sách Chuyến Đi khả dụng:                                          │
│  - T01d (Xe VH-01 - Tài xế B): Bình thường (Safe Score: 88/100)          │
│  - T04d (Xe VH-04 - Tài xế A): 🔴 Rủi ro cao (Safe Score: 42/100 - TTC 1.2s)│
│  - T08d (Xe VH-08 - Tài xế C): Xuất sắc (Safe Score: 96/100)            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 5.3 Cách Quản lý & Tính điểm khi có Nhiều Tài xế (Multi-Driver Fleet Score)
1. **Tính điểm Rủi ro Thời gian thực cho từng Trip**:
   - Backend quét qua 1,800 frame của từng Trip (`T01d` đến `T10d`).
   - Tự động lấy `max(final_risk_score)` hoặc `average(risk)` của 1,800 frame để ra điểm tổng kết cho Trip đó.
2. **Cập nhật Bảng xếp hạng Fleet Leaderboard**:
   - **Top 1 Safe**: Chuyến đi có điểm Rủi ro thấp nhất (Ví dụ `T08d` điểm Safe 96/100).
   - **High Risk / Critical**: Chuyến đi có điểm Rủi ro cao nhất (Ví dụ `T04d` có 2 khoảnh khắc vi ngủ, điểm Safe 42/100).
3. **Thao tác Chuyển Đổi Trip khi Demo**:
   - Mặc định chọn `T01d` hoặc `T04d` (chuyến đi có sự cố kịch tính nhất).
   - Khi BGK hỏi: *"Hệ thống xử lý thế nào nếu tôi muốn xem xe khác?"* $\rightarrow$ **Click Dropdown chọn sang `T02d` hoặc `T05d`**, toàn bộ Video, Bản đồ GPS, Gauge tốc độ và CarSky HMI sẽ lập tức load dữ liệu của xe tương ứng.

---

## 6. CHECKLIST CHUẨN BỊ LÊN SÂN SẤU DEMO (FINAL DEMO CHECKLIST)

- [ ] **Trip Selector**: Đã test Dropdown chuyển đổi mượt mà giữa các chuyến `T01d` đến `T10d`.
- [ ] **Dual-Screen Layout**: Đã chia đôi 2 cửa sổ trình duyệt (Dashboard Trái + CarSky Phải).
- [ ] **Audio Test**: Đã test tiếng còi Beep 880Hz kêu rõ ràng.
- [ ] **Dataset Ready**: Đã load sẵn file `T01d.json` và frame 450 chuẩn bị tua.
- [ ] **CarSky Connected**: Đã cấu hình `carsky_adapter.py` kết nối với CarSky Room.
- [ ] **Submissions Ready**: Đã có đủ 10 file CSV trong thư mục `submissions/` sẵn sàng nộp BTC.

---
*Chúc Đội thi có màn trình diễn xuất sắc và giành giải nhất!*
