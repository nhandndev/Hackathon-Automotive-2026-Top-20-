# 📊 DATASET SPECIFICATION & SCHEMA REFERENCE (HACKATHON T01-T10)

> **Tài liệu Mô tả Quy chuẩn & Schema Dữ liệu 10 Chuyến đi (Trips `T01d` đến `T10d`) dành cho AI & SE.**

---

## 1. 🎯 TỔNG QUAN BỘ DỮ LIỆU (DATASET OVERVIEW)

* **Số lượng chuyến đi:** 10 Trips (`T01d`, `T02d`, `T03d`, `T04d`, `T05d`, `T06d`, `T07d`, `T08d`, `T09d`, `T10d`).
* **Thời lượng mỗi Trip:** 90 giây.
* **Tần số lấy mẫu (Sampling Rate):** 20 FPS (Tương đương 50ms cho mỗi frame telemetry & vision).
* **Tổng số frame per Trip:** 1,800 frames (`frame_id`: 0 -> 1799).
* **Định dạng lưu trữ:** File JSON chuẩn hóa (`.json`).

---

## 2. 📝 CẤU TRÚC mà AI SẼ TRẢ VỀ

```json
"trip_id": "T01d",
  "metadata": {
    "trip_id": "T01d",
    "description": "DEBUG 30s: highway evening, motorcycle cut-in + mild lead brake (compressed)",
    "duration_sec": 90,
    "fps": 20,
    "map": "Town01"
"driver_profile": "normal",
    "carla_version": "0.9.15",
    "random_seed": 1001,
    "speed_limit_kmh": 80

frame_id": 0,
"timestamp": 0.0,
      "ego": {
        "speed_kmh": 0.0,
        "longitudinal_accel": 0.0,
        "lateral_accel": 0.0
"geolocation": {
          "lat": -0.00123,
          "lon": -0.000485,
          "alt": 0.16
        }

"driver": {
        "state": "distracted",
        "alertness_score": 0.45,
        "eye_state": "open",
        "head_pose": "side",
        "mouth_state": "normal",
        "nthu_subject_id": "14"
      }
"min_ttc": Infinity,
      "headway_sec": Infinity,
      "behavior_flags": {
        "harsh_brake": false,
        "harsh_accel": false,
        "harsh_corner": false,
        "speeding": false,
        "tailgating": false

"risk": {
        "base_risk": 0.0,
        "driver_factor": 2.2,
        "final_risk_score": 0.0

```

### 2.1 Diễn giải Chi tiết Trường Dữ liệu (Field Dictionary)

| Khối Dữ Liệu | Trường (Field Name) | Kiểu Dữ Liệu | Mô Tả & Đơn Vị Đo |
| :--- | :--- | :--- | :--- |
| **Gốc (Root)** | `trip_id` | `string` | Mã định danh chuyến đi (`T01d` .. `T10d`). |
| | `total_frames` | `integer` | Tổng số frame trong file (`1800`). |
| **Frame** | `frame_id` | `integer` | Thứ tự frame từ `0` đến `1799`. |
| | `timestamp` | `float` | Mốc thời gian tính bằng giây (`0.00` đến `89.95s`, bước nhảy 0.05s). |
| **`telemetry`** | `speed_kmh` | `float` | Vận tốc tức thời của xe ($km/h$). |
| | `longitudinal_accel` | `float` | Gia tốc dọc / Gia tốc phanh ($m/s^2$). Giá trị âm mạnh đại diện cho phanh gấp (`harsh_brake`). |
| | `lateral_accel` | `float` | Gia tốc ngang / Đảo làn ($m/s^2$). |
| | `latitude` | `float` | Tọa độ Vĩ độ GPS. |
| | `longitude` | `float` | Tọa độ Kinh độ GPS. |
| | `heading_deg` | `float` | Góc hướng di chuyển của xe ($0^\circ - 360^\circ$). |
| **`ai_vision`** | `predicted_ttc` | `string / float` | Thời gian dự kiến va chạm (Time-To-Collision in seconds). Trả về `"inf"` nếu an toàn, hoặc chỉ số cụ thể (ví dụ `"1.2"` khi nguy kịch). |
| | `predicted_driver_state`| `string` | Trạng thái sinh lý tài xế: `alert` (Tỉnh táo), `drowsy` (Buồn ngủ), `yawning` (Ngáp), `microsleep` (Vi ngủ), `distracted` (Mất tập trung). |
| | `alertness_score` | `float` | Điểm độ tỉnh táo của tài xế (Mức giá trị từ `0.00` đến `1.00`). |

---

## 3. ⚙️ QUY CHUẨN XỬ LÝ DÀNH CHO SE BACKEND & AI MODEL

1. **Replay Engine 20 FPS:** SE Backend dùng trường `timestamp` (bước nhảy `0.05s`) để stream WebSocket đúng tần số 20 FPS cho Client UI.
2. **Cảnh báo Nguy hiểm (Critical Alert Criteria):**
   * Nếu `predicted_driver_state` thuộc nhóm `microsleep` hoặc `drowsy`.
   * HOẶC chỉ số va chạm `predicted_ttc` $< 1.5$ giây.
   * $\rightarrow$ Kích hoạt ngay còi báo động 880Hz, nhấp nháy đỏ trên UI & push REST API cảnh báo sang **CarSky HMI**.
3. **Batch Pre-ingestion (Cold-Start Ranking):** Backend khởi chạy sẽ quét nhanh qua 1,800 frames của cả 10 chuyến đi để tính sẵn điểm an toàn tổng kết:
   $$\text{Safety Score} = 100 - \max(\text{Risk Score of 1800 frames})$$
