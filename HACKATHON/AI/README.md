# FPTU DMS Vision — Production AI Runtime

Thư mục `AI/` là runtime chính thức của sản phẩm. Repo chỉ chứa code inference,
runtime config, model đã train và một trip nhỏ phục vụ demo; không chứa
training, augmentation hay cross-validation.

## Chức năng

- **Challenge 1 — Road/TTC:** xử lý hai road camera, phát hiện và tracking
  phương tiện, ước lượng depth và Time-to-Collision.
- **Challenge 2 — Driver State:** xử lý face camera, dự đoán
  `alert | drowsy | yawning | distracted | microsleep`.
- **Challenge 3 — Risk Fusion:** kết hợp TTC và driver state thành risk score
  từ 0 đến 100.

## Cấu trúc

```text
AI/
├── core/
│   ├── btc_trip.py
│   ├── challenge1_road/
│   ├── challenge2_driver/
│   │   ├── dms_core.py
│   │   ├── ml_features.py
│   │   ├── predict_state.py
│   │   ├── driver_enrollment.py
│   │   └── driver_profile.py
│   └── challenge3_fusion/
├── configs/
│   ├── challenge1.yaml
│   └── challenge2.yaml
├── models/
│   ├── driver_state_rf_v2.joblib
│   └── driver_state_rf_v2.manifest.yaml
├── scripts/
│   ├── run_inference.py
│   ├── trip_visual_demo.py
│   └── webcam_driver_demo.py
├── demo_trips/
│   └── T_test_01/
├── artifacts/
├── requirements.txt
└── README.md
```

`demo_trips/T_test_01` là một augmented test trip 720 frame có đủ cấu trúc BTC
và đủ năm driver-state. Nó chỉ dùng để trình diễn, không được dùng để báo cáo
generalization hoặc train lại model.

## Cài đặt

Khuyến nghị Python 3.10 hoặc 3.11:

```powershell
cd HACKATHON\AI
python -m pip install -r requirements.txt
```

## Challenge 2 v2

Pipeline production:

```text
Face camera
→ MediaPipe Face Mesh
→ EAR, MAR, head pose, continuous eye closure
→ causal rolling windows 3/10/30 giây
→ 59 features
→ Random Forest v2
→ safety fusion
→ driver state + confidence
```

Model mặc định:

```text
models/driver_state_rf_v2.joblib
```

Runtime so sánh chính xác danh sách 59 feature trong model artifact. Model 49
feature cũ không thể bị load nhầm. Safety fusion chỉ override thành
`microsleep` khi face/eyes hợp lệ và mắt nhắm liên tục vượt ngưỡng trong
`configs/challenge2.yaml`.

## Personalized driver

Personalization không nhận diện khuôn mặt. Tài xế nhập một `driver_id`; hệ
thống chỉ lưu các baseline số như EAR mở/đóng, MAR trung tính/ngáp và neutral
head pose. Không lưu frame, ảnh, video hoặc face embedding.

Lần đầu hoặc khi muốn đo lại profile:

```powershell
python scripts\webcam_driver_demo.py `
  --driver-id driver_001 `
  --enroll
```

UI lần lượt yêu cầu nhìn thẳng, chớp mắt, quay trái/phải, nhìn xuống, thả lỏng
miệng, ngáp và nhắm mắt ngắn. Mỗi bước chỉ được chấp nhận khi:

1. đủ thời gian và số landmark sample hợp lệ;
2. action tương ứng đã được phát hiện;
3. người dùng nhấn `Space`.

Nếu action chưa hợp lệ, `Space` xóa sample của bước hiện tại và cho làm lại.
Profile hợp lệ được lưu tại:

```text
artifacts/driver_profiles/driver_001.json
```

Những lần sau:

```powershell
python scripts\webcam_driver_demo.py --driver-id driver_001
```

Camera khác:

```powershell
python scripts\webcam_driver_demo.py `
  --camera 1 `
  --driver-id driver_001
```

Trong hành trình:

- `R`: reset temporal history nhưng giữ personal profile.
- `Q` hoặc `Esc`: thoát.

Log được ghi vào `artifacts/webcam_driver_state.jsonl`.

## Demo trip ba camera

Chạy trip augmented được đóng gói cùng repo:

```powershell
python scripts\trip_visual_demo.py `
  --trip-dir demo_trips\T_test_01
```

Cửa sổ 1280×720 hiển thị:

- road-left: bounding box, track ID, depth và TTC;
- road-right: stereo reference;
- face camera: box mặt/mắt/miệng, driver state và continuous eye closure;
- fusion dashboard: tốc độ, TTC, alertness và risk score.

Điều khiển:

- `Space`: pause/resume;
- `N`: chạy một frame khi pause;
- `+` / `-`: thay đổi tốc độ phát;
- `Q` hoặc `Esc`: thoát.

Lưu video và CSV chuẩn BTC:

```powershell
python scripts\trip_visual_demo.py `
  --trip-dir demo_trips\T_test_01 `
  --output-video artifacts\T_test_01-demo.mp4 `
  --output-csv artifacts\T_test_01.csv
```

Nếu Ultralytics/YOLO weights chưa khả dụng, Challenge 1 vẫn tính TTC bằng
stereo ROI fallback. Box lấy từ `kitti/label_2`, nếu được hiển thị, luôn có
nhãn `KITTI LABELS (visual only)` và không tham gia tính TTC hoặc CSV.

## Inference BTC

Một trip:

```powershell
python scripts\run_inference.py `
  --trip-dir <BTC_DATA_DIR>\T01-Sample `
  --out artifacts\predictions
```

Nhiều trip:

```powershell
python scripts\run_inference.py `
  --data-dir <BTC_DATA_DIR> `
  --out artifacts\predictions
```

Mỗi trip tạo một file theo contract:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

## Quy tắc production

- Không đưa training/augmentation/CV vào `AI/`.
- Không commit log, prediction hoặc driver profile.
- Model mới phải có manifest, feature schema và SHA-256 tương ứng.
- Reset temporal state giữa các trip.
- Xử lý frame theo đúng thứ tự timestamp; không shuffle khi inference.
