# FPTU DMS Vision — AI Inference

Thư mục `AI/` chứa runtime inference cho ba challenge:

- **Challenge 1 — Collision Risk:** dự đoán Time-to-Collision (TTC).
- **Challenge 2 — Driver Intelligence:** nhận diện trạng thái tài xế.
- **Challenge 3 — Risk Fusion:** kết hợp TTC và trạng thái tài xế thành điểm
  rủi ro.

Repository production chỉ chứa code inference, runtime config và model đã
train. Dataset, augmentation, training và cross-validation không nằm ở đây.

## Cấu trúc

```text
AI/
├── core/
│   ├── challenge1_road/       # Detection, stereo depth, tracking và TTC
│   ├── challenge2_driver/     # MediaPipe, rolling features và ML inference
│   └── challenge3_fusion/     # Risk score
├── configs/
│   ├── challenge1.yaml
│   ├── challenge2.yaml
│   └── bytetrack_vru.yaml
├── models/
│   ├── driver_state_rf.joblib
│   └── driver_state_rf.manifest.yaml
├── scripts/
│   ├── run_inference.py
│   └── webcam_driver_demo.py
├── requirements.txt
└── README.md
```

## Cài đặt

Khuyến nghị sử dụng Python 3.10 hoặc 3.11:

```powershell
cd HACKATHON\AI
python -m pip install -r requirements.txt
```

`run_inference.py` cần `team_kit/dataset_loader.py` từ Package Starter Kit.
Đường dẫn đến Starter Kit được truyền bằng `--starterkit-root`.

## Challenge 1 — Road Camera và TTC

Challenge 1 xử lý từng cặp ảnh stereo theo thứ tự thời gian:

```text
Ảnh road trái/phải
→ YOLO phát hiện phương tiện/người đi bộ
→ tracking giữ ID đối tượng
→ stereo/depth tính khoảng cách
→ tốc độ tiếp cận
→ Time-to-Collision
```

Core chính:

```text
core/challenge1_road/predict_ttc.py
```

Interface dùng chung:

```python
ttc = road_predictor.predict_frame(
    frame_id,
    timestamp,
    left_image,
    right_image,
    ego_speed_kmh,
)
```

Nếu YOLO hoặc weights không khả dụng, hệ thống tự chuyển sang stereo ROI
baseline để pipeline vẫn sinh được TTC. Nếu trip có `kitti/depth/*.npy`, core
ưu tiên depth đó; các frame còn lại dùng StereoSGBM.

Runtime config:

```text
configs/challenge1.yaml
```

Challenge 1 hiện chạy trên trip BTC/starter-kit. Demo camera đường thực tế cần
hai camera stereo đã đồng bộ, stereo calibration và tốc độ xe; một webcam đơn
không đủ để tính TTC đáng tin cậy.

## Challenge 2 — Driver State

Challenge 2 xử lý cabin camera:

```text
Ảnh khuôn mặt tài xế
→ MediaPipe Face Mesh
→ EAR, MAR và head pose
→ rolling features
→ Random Forest
→ driver state + confidence
```

Core production:

```text
core/challenge2_driver/
├── dms_core.py
├── ml_features.py
└── predict_state.py
```

`DriverStatePredictor` là interface dùng chung cho batch inference và webcam.
Nó quản lý MediaPipe, rolling history 30 giây, model schema và reset giữa các
trip.

Model production:

```text
models/driver_state_rf.joblib
```

Đây là model `driver_state_rf_augmented.joblib` đã được đổi tên khi đưa vào
runtime. Model dự đoán năm nhãn:

```text
alert | drowsy | yawning | distracted | microsleep
```

Runtime config:

```text
configs/challenge2.yaml
```

## Unified inference

`scripts/run_inference.py` là entry point duy nhất cho cả ba challenge. Chạy
một trip:

```powershell
python scripts\run_inference.py `
  --trip-dir <BTC_DATA_DIR>\T01-Sample `
  --starterkit-root <PACKAGE_STARTERKIT_DIR> `
  --out artifacts\predictions
```

Chạy tất cả trip trực tiếp trong một data directory:

```powershell
python scripts\run_inference.py `
  --data-dir <BTC_DATA_DIR> `
  --starterkit-root <PACKAGE_STARTERKIT_DIR> `
  --out artifacts\predictions
```

Ví dụ local:

```powershell
python scripts\run_inference.py `
  --data-dir E:\automotive_cc\Package_starterkit\data `
  --starterkit-root E:\automotive_cc\Package_starterkit `
  --out artifacts\predictions
```

Mỗi trip tạo một CSV đúng contract BTC:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Quy ước:

- `predicted_ttc`: số giây hoặc `inf`.
- `predicted_driver_state`: một trong năm nhãn Challenge 2.
- `predicted_risk_score`: điểm từ 0 đến 100.

## Webcam demo Challenge 2

Chạy cabin-camera demo bằng model production:

```powershell
python scripts\webcam_driver_demo.py
```

Nếu camera mặc định không mở được:

```powershell
python scripts\webcam_driver_demo.py --camera 1
```

Cửa sổ hiển thị driver state, confidence, rule state, alertness, eye, mouth,
head pose và chất lượng nhận diện.

- `R`: reset calibration và rolling history.
- `Q` hoặc `Esc`: thoát.

Log webcam được ghi vào:

```text
artifacts/webcam_driver_state.jsonl
```

## Output và model

Không commit dataset hoặc output sinh ra:

```text
data/
artifacts/
predictions/
```

Model production phải đi cùng `driver_state_rf.manifest.yaml` để kiểm tra tên,
version, class list và SHA-256.
