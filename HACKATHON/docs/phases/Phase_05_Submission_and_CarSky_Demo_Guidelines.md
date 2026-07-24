# PHASE 5: QUY TRÌNH ĐÓNG GÓI & NỘP BÀI THI CHO BAN TỔ CHỨC (SUBMISSION & CARSKY DEMO GUIDELINES)

---

## 1. MỤC TIÊU VÀ QUY CHUẨN NỘP BÀI THI (SUBMISSION OVERVIEW)

### 1.1 Mục tiêu của Phase 5
Hướng dẫn chi tiết toàn bộ quy trình xuất dữ liệu và đóng gói sản phẩm để **nộp bài cho Ban Tổ Chức (BTC)** đạt điểm tuyệt đối:
1. **Phần Bắt Buộc**: Xuất đủ 10 file CSV kết quả (`T01d.csv` $\rightarrow$ `T10d.csv`) đúng quy chuẩn 1,800 dòng $\times$ 5 cột, sai số $MAE < 1.5$.
2. **Phần Điểm Thưởng CarSky (+15 Điểm)**: Đóng gói video demo running song song (Dual-Screen) và xuất file Blueprint JSON của CarSky.

---

## 2. QUY CHUẨN 10 FILE CSV NỘP BÀI BẮT BUỘC (1800 DÒNG x 5 CỘT)

### 2.1 Định dạng chuẩn 5 Cột
Tất cả 10 file CSV phải nằm trong thư mục `submissions/` với tên file đúng dạng `T01d.csv`, `T02d.csv`, ..., `T10d.csv`.
Mỗi file CSV chứa đúng **1,800 dòng data + 1 dòng Header** (20 FPS cho 90 giây chuyến đi):

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
0,0.0,inf,alert,0.0
1,0.05,inf,alert,0.0
...
450,22.5,1.2,drowsy,84.0
...
1799,89.95,inf,alert,0.0
```

### 2.2 Quy tắc điền dữ liệu cột:
- `frame_id`: Số nguyên từ `0` đến `1799`.
- `timestamp`: Số thực từ `0.0` đến `89.95` (bước nhảy `0.05`s).
- `predicted_ttc`: Chuỗi `"inf"` (nếu không có nguy cơ va chạm) hoặc số thực ví dụ `1.2`.
- `predicted_driver_state`: Chuỗi trạng thái tài xế (`alert`, `distracted`, `drowsy`, `yawning`, `microsleep`).
- `predicted_risk_score`: Số thực điểm rủi ro từ `0.0` đến `100.0`.

---

## 3. LỆNH TỰ ĐỘNG XUẤT VÀ KIỂM TRA CSV (AUTOMATED SCRIPTS)

SE Backend đã có sẵn 2 script hỗ trợ tự động trong thư mục `backend/scripts/`:

### 3.1 Lệnh 1: Xuất 10 file CSV nộp bài
```bash
cd backend
python scripts/export_submission_csv.py
```
*Kết quả*: Sinh ra 10 file `submissions/T01d.csv` đến `submissions/T10d.csv`.

### 3.2 Lệnh 2: Tự động kiểm tra tính hợp lệ (Validation)
```bash
cd backend
python scripts/validate_submission.py
```
*Kết quả kiểm tra*:
- [x] Đủ 10 file CSV (`T01d.csv` - `T10d.csv`).
- [x] Mỗi file đúng 1,800 dòng $\times$ 5 cột header chuẩn.
- [x] Không chứa giá trị `NaN`, `Null` hoặc dòng rỗng.

---

## 4. HƯỚNG DẪN QUAY VIDEO DEMO VÀ ĐÓNG GÓI CARSKY (+15 ĐIỂM THƯỞNG)

Để nhận trọn 15 điểm thưởng CarSky từ BTC, team cần chuẩn bị bộ hồ sơ demo gồm 2 thành phần:

### 4.1 Video Demo Chạy Song Song (Dual-Screen Video Demo - 1 đến 2 phút)
- **Cấu hình màn hình quay**:
  - **Nửa màn hình Trái**: Trình duyệt chạy **SE Master Fleet Dashboard** (`demo/index.html` hoặc React App) xem toàn đội xe.
  - **Nửa màn hình Phải**: Trình duyệt chạy **CarSky Workbench HMI** (Màn hình Cockpit cabin xe).
- **Kịch bản diễn minh chứng**:
  1. Bấm nút Play Replay chuyến đi `T01d`.
  2. Khi video chạy tới frame 450 (khoảnh khắc tài xế vi ngủ + xe phanh gấp):
  3. Màn hình bên trái Dashboard hiển thị Risk Score 84/100, tô màu đỏ nguy hiểm và hiển thị khối chữ **AI Risk Reasoning Card**.
  4. Đồng thời ngay lập tức, màn hình bên phải **CarSky HMI** nổ còi beep báo động, viền đỏ nhấp nháy và hiển thị tin nhắn Coaching của GenAI:  
     *`"Tài xế A (Xe VH-04) sụt giảm tỉnh táo xuống 15% do vi ngủ. Vui lòng tắp xe vào lề nghỉ ngơi!"`*

### 4.2 Export File CarSky Blueprint JSON
1. Trên giao diện CarSky Workbench Nydus, bấm **Export Blueprint**.
2. Lưu file với tên `FPTU_DMS_CarSky_Blueprint.json`.

---

## 6. HƯỚNG DẪN CHI TIẾT THAO TÁC LIÊN KẾT GIỮA HỆ THỐNG VÀ CARSKY WORKBENCH

### 6.1 Cơ chế liên kết REST API giữa 2 hệ thống
Hệ thống Fleet Management của chúng ta kết nối với CarSky thông qua **CarSky REST API Gateway**. Không cần cài đặt phần mềm phức tạp, Backend SE sẽ gọi HTTP POST trực tiếp đến CarSky Endpoint:

```text
HTTP POST https://<carsky_domain_or_ip>/api/v1/vms/{roomId}/{nodeKey}/text (hoặc /shell)
Headers: 
  Authorization: Bearer <your_carsky_api_key>
  Content-Type: application/json
```

---

### 6.2 Các bước thao tác thực tế trên giao diện CarSky Workbench (4 Bước)

#### 🔑 Bước 1: Lấy CarSky API Key từ Workbench UI
1. Mở web CarSky Workbench (màn hình Rework UI).
2. Click vào **Ảnh đại diện User** ở góc trên màn hình $\rightarrow$ Chọn tab **Credentials**.
3. Bấm nút **Create Credential** $\rightarrow$ Sao chép chuỗi **API Key** (dạng `Bearer carsky_sec_...`).
4. Lưu API Key này vào file `.env` hoặc file `backend/app/adapters/carsky_adapter.py` của Backend SE.

#### 🗺️ Bước 2: Lấy `roomId` và `nodeKey` trên Canvas
1. Vào tab **Nydus** trên CarSky Workbench $\rightarrow$ Mở Blueprint / Deployment đang chạy.
2. **`roomId`**: Mở tab **Devices** hoặc **Deployments**, sao chép chuỗi ID nằm cạnh thiết bị đang chạy (ví dụ `room-vh04-dms`).
3. **`nodeKey`**: Click trực tiếp vào Node **Skycraft (Android VM)** hoặc **Script Node** trên Canvas $\rightarrow$ Nhìn panel Inspector bên phải để lấy `id` của Node (ví dụ `vm-1` hoặc `hmi-display`).

#### 🎨 Bước 3: Tạo Widget HMI trên CarSky Cockpit
1. Trên CarSky Workbench, mở thiết bị `roomId`.
2. Bấm **Add Widget** $\rightarrow$ Thêm 3 Widget chính:
   - **Screen Widget**: Màn hình Virtual Cockpit trong xe hiển thị cảnh báo nhấp nháy đỏ.
   - **Signal Watch Widget**: Theo dõi tín hiệu TTC (`safety_metrics.min_ttc`) & Vận tốc (`speed_kmh`).
   - **Text / GPIO Panel Widget**: Ô văn bản hiển thị thông điệp Coaching từ AI Copilot (`ai_generated_reasoning.summary`).

#### ⚡ Bước 4: Kích hoạt Push từ Backend SE
Trong vòng lặp Replay Stream 20 FPS của Backend (`backend/main.py`), gọi hàm `push_hmi_alert_to_carsky(frame)`. 
Khi xảy ra sự cố vi ngủ (`frame_id 450`), Backend tự động kích hoạt HTTP Request:

```python
# Minh họa lệnh REST API gọi từ Backend SE sang CarSky:
import requests

url = f"https://carsky.io/api/v1/vms/{room_id}/{node_key}/text"
headers = {"Authorization": f"Bearer {api_key}"}
payload = {"text": "CẢNH BÁO: Phát hiện vi ngủ! Giảm tốc độ và dừng nghỉ ngay lập tức."}

requests.post(url, headers=headers, json=payload)
```

---

## 7. QUY TRÌNH NỘP BÀI THI HOÀN CHỈNH CHO BAN TỔ CHỨC (SUBMISSION PACKAGE)

Khi hoàn thành bài thi, team sẽ đóng gói nộp cho BTC gồm **3 phần chính**:

```text
HỒ SƠ NỘP BÀI BTC (FPTU_DMS_Vision_Submission.zip)
├── submissions/                          # Phần 1: 10 File CSV chuẩn thi
│   ├── T01d.csv (1800 dòng x 5 cột)
│   ├── T02d.csv
│   └── ... T10d.csv
├── carsky_bonus/                         # Phần 2: Hồ sơ Điểm thưởng CarSky (+15đ)
│   ├── FPTU_DMS_CarSky_Blueprint.json   # File Blueprint JSON export từ Nydus
│   └── Demo_DualScreen_CarSky_HMI.mp4   # Video quay 2 màn hình (Dashboard + CarSky)
└── source_code/                          # Phần 3: Mã nguồn dự án
    ├── backend/                          # FastAPI Backend & Scripts
    └── demo/index.html                   # Master Fleet Dashboard UI
```

---
*Hoàn tất Phase 5 — Sẵn sàng chạy Demo và nộp bài thi cho Ban Tổ Chức!*
