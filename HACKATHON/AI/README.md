# FPTU DMS Vision — AI Runtime

`AI/` là runtime inference chính thức của sản phẩm. Pipeline xử lý hai road
camera, cabin camera và telemetry để tạo output cho ba challenge, sau đó
Decision Engine phát cảnh báo cho Fleet Dashboard và CarSky qua Backend SE.

Repo sản phẩm chỉ chứa inference code, config, model đã train, manifest và tài
liệu chạy. Training, augmentation, prediction tạm và driver profile không được
commit.

## 1. Kiến trúc

```text
Road-left + road-right → Challenge 1: detection/depth/TTC ─┐
Cabin camera → Challenge 2: driver state ──────────────────┼→ CSV BTC
Telemetry + TTC → Challenge 3: safe/risk score ────────────┘
                              │
                              ▼
                       Decision Engine
                       │             │
                       ▼             ▼
                Fleet Dashboard    CarSky HMI
                       └────── FastAPI SE ──────┘
```

CSV chuẩn BTC:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Driver state: `alert | drowsy | yawning | distracted | microsleep`.
Decision Engine không thay đổi CSV; event được lưu JSONL và gửi riêng sang SE.

## 2. Global và personalized driver

### Global pipeline — dataset BTC

Dùng model chung `driver_state_rf_v3_onnx.joblib`. Đây là chế độ bắt buộc cho 6
practice trip và 10 scored trip vì BTC không có bước enrollment theo tài xế.

Trong `run_inference.py`, `--driver-id` chỉ gắn ID vào DecisionEvent, không load
profile và không thay đổi dự đoán CSV.

### Personalized pipeline — webcam

Tài xế nhập `driver_id` và thực hiện guided enrollment. Hệ thống chỉ lưu baseline
số như EAR mở/đóng, MAR trung tính/ngáp và neutral head pose; không lưu ảnh,
video, face embedding hoặc dữ liệu nhận diện.

```text
AI/artifacts/driver_profiles/<driver_id>.json
```

`webcam_driver_demo.py` và `end_to_end_demo.py` thực sự load profile này. Không
truyền `--driver-id` thì dùng global model.

## 3. Cấu trúc runtime

```text
AI/
├── core/
│   ├── challenge1_road/       # detection, stereo depth, tracking, TTC
│   ├── challenge2_driver/     # ONNX landmarks, RF, profile
│   ├── challenge3_fusion/     # công thức safe/risk BTC
│   └── decision_engine/       # alert policy và lifecycle
├── configs/                   # C1, C2, Decision Engine
├── models/                    # RF v3, YuNet, 468-landmark ONNX và YOLO C1
├── integrations/se_client.py
├── scripts/
│   ├── run_inference.py
│   ├── webcam_driver_demo.py
│   ├── trip_visual_demo.py
│   └── end_to_end_demo.py
├── artifacts/                 # runtime output, không commit
├── requirements.txt
└── README.md
```

## 4. Yêu cầu

- Python 3.13 cho AI.
- Webcam cho live/personalized demo.
- RAM từ 8 GB; 16 GB phù hợp hơn khi chạy C1 và C2 cùng lúc.
- GPU CUDA là tùy chọn. CPU vẫn chạy được nhưng có thể không realtime.
- Dataset BTC đặt ngoài repo, ví dụ `E:\automotive_cc\Practice_Dataset`.

Demo end-to-end dùng một `.venv` Python 3.13 tại root `HACKATHON`. Không dùng
Conda và không commit thư mục `.venv` lên Git.

## 5. Setup AI

Chạy từ root `HACKATHON` trên Windows PowerShell:

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt
```

Nếu `.venv` đã tồn tại, chỉ cần activate rồi đồng bộ requirements:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt
```

Kiểm tra môi trường và model:

```powershell
python -c "import cv2, onnxruntime, sklearn, ultralytics; print('AI environment OK')"

python -c "from pathlib import Path; p=Path('AI/models'); r=['driver_state_rf_v3_onnx.joblib','face_detection_yunet_2023mar.onnx','face_landmark_468.onnx','yolov8s_finetuned_carla_v2.pt']; assert all((p/x).is_file() for x in r); print('AI models OK')"
```

## 6. Challenge 2 v3

```text
Cabin frame
→ YuNet face detector
→ ONNX FaceMesh-compatible 468 landmarks
→ EAR, MAR, head pose, continuous eye closure
→ causal rolling features 3/10/30 giây
→ Random Forest v3 với 59 features
→ reliable-microsleep safety fusion
```

Artifact khóa đúng feature schema và backend
`onnx-yunet-facemesh468`; model MediaPipe/49-feature cũ bị từ chối. Report hiện
tại ghi accuracy `0.7847`, macro-F1 `0.8028` trên 3.600 augmented test frames;
đây không phải hidden BTC test score.

## 7. Enrollment và webcam Challenge 2

Tạo hoặc đo lại profile:

```powershell
python AI\scripts\webcam_driver_demo.py `
  --camera 0 `
  --driver-id driver_001 `
  --enroll
```

UI chỉ nhận bước khi action và landmark sample hợp lệ.

- `Space`: xác nhận; nếu chưa hợp lệ thì reset bước và làm lại.
- `R`: reset temporal state nhưng giữ profile.
- `Q` hoặc `Esc`: thoát.

Chạy personalized:

```powershell
python AI\scripts\webcam_driver_demo.py --camera 0 --driver-id driver_001
```

Chạy global model:

```powershell
python AI\scripts\webcam_driver_demo.py --camera 0
```

Camera khác dùng `--camera 1`. Log mặc định nằm tại
`AI/artifacts/webcam_driver_state.jsonl`.

## 8. Demo ba camera từ BTC

Cả road và cabin frame đều lấy từ dataset:

```powershell
python AI\scripts\trip_visual_demo.py `
  --trip-dir E:\automotive_cc\Practice_Dataset\T01-Sample
```

`Space`: pause/resume; `N`: chạy một frame khi pause; `+/-`: tốc độ; `Q/Esc`:
thoát.

## 9. End-to-end: BTC road + webcam driver + SE

Đây là demo sản phẩm chính:

- road-left, road-right và telemetry lấy từ BTC;
- cabin frame lấy từ webcam;
- `--driver-id` load personalized profile thật;
- C1, C2, C3 và Decision Engine cùng chạy;
- event mới được POST ngay sang Backend SE.

CSV giữ timestamp BTC. C2 và Decision Engine dùng monotonic wall-clock của
webcam để thời lượng nhắm mắt/ngáp vẫn là thời gian thật khi road inference chậm.

Chạy Backend trước, sau đó:

```powershell
python AI\scripts\end_to_end_demo.py `
  --trip-dir E:\automotive_cc\Practice_Dataset\T01-Sample `
  --camera 0 `
  --driver-id driver_001 `
  --se-endpoint http://127.0.0.1:8000/api/v1/alerts `
  --output-csv AI\artifacts\predictions\T01-Sample-live.csv `
  --events AI\artifacts\decision_events\T01-Sample-live.events.jsonl
```

Bỏ `--driver-id` để dùng global model. Bỏ `--se-endpoint` nếu chỉ test AI/UI.

### Hai loại product demo

Chạy từ thư mục `HACKATHON`:

```powershell
# Hybrid: một road trip BTC + webcam + personalized profile
.\scripts\run_product_demo.ps1 `
  -Mode hybrid-live `
  -TripDir E:\automotive_cc\Practice_Dataset\T01-Sample `
  -Camera 0 `
  -DriverId driver_001 `
  -OpenDashboard

# Dataset fleet: tự phát hiện mọi trip trực tiếp dưới folder
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir E:\automotive_cc\Practice_Dataset `
  -OpenDashboard
```

`dataset-fleet` lấy cả road camera và driver camera từ từng trip. Các trip được
đăng ký cùng lúc nhưng inference tuần tự để giới hạn GPU/RAM. Backend lưu riêng
theo `trip_id`: trạng thái, snapshot timeline, DecisionEvents, cabin frame và
road frame cuối. Vì vậy khi chuyển sang trip kế tiếp, trip cũ vẫn chọn/xem lại
được trên Dashboard. Đổi dataset chỉ cần thay `-DataDir`; tên trip không bị
hard-code. Sau trip cuối, runner chờ Enter để người demo xem toàn bộ lịch sử
trước khi dừng Backend và Dashboard.

SE endpoints:

```text
GET http://127.0.0.1:8000/api/v1/alerts/recent
GET http://127.0.0.1:8000/api/v1/alerts/trips
WS  ws://127.0.0.1:8000/api/v1/alerts/live
```

Đây là nhánh product demo và không đi qua evaluator. Backend phải bật CarSky
external để chuyển các event có audience `driver_display` sang HMI; Frontend
nhận cùng event qua WebSocket. Hướng dẫn đủ bốn cửa sổ, preflight và backup:
[`../reportbtc/C2_END_TO_END_DEMO_SCRIPT.md`](../reportbtc/C2_END_TO_END_DEMO_SCRIPT.md).

## 10. Inference BTC

Đây là nhánh submission độc lập: dataset → CSV → evaluator. Không cần chạy
Backend, Frontend, webcam hoặc CarSky.

Một trip:

```powershell
python AI\scripts\run_inference.py `
  --trip-dir E:\automotive_cc\Practice_Dataset\T01-Sample `
  --output-csv AI\artifacts\predictions\T01-Sample.csv
```

Sáu practice trip:

```powershell
python AI\scripts\run_inference.py `
  --data-dir E:\automotive_cc\Practice_Dataset `
  --samples-only `
  --out AI\artifacts\predictions_6_samples
```

Mười scored trip:

```powershell
python AI\scripts\run_inference.py `
  --data-dir E:\automotive_cc\Competition_Dataset `
  --scored-only `
  --out AI\artifacts\predictions_scored
```

Thêm Decision Engine:

```powershell
python AI\scripts\run_inference.py `
  --data-dir E:\automotive_cc\Practice_Dataset `
  --samples-only `
  --out AI\artifacts\predictions_6_samples `
  --decision-events-dir AI\artifacts\decision_events `
  --driver-id btc_practice
```

Trong batch, `--driver-id` chỉ là event metadata, không personalization.

### Evaluate sau inference

`AI/team_kit` là bản evaluator đi kèm Starter Kit, được giữ trong repo sản phẩm
để inference và evaluation dùng cùng một workspace. Chạy từ Git repo root
`Hackathon-Automotive-2026`.

Evaluate sáu practice trip:

```powershell
python HACKATHON\AI\team_kit\evaluation.py `
  --predictions HACKATHON\AI\artifacts\predictions_6_samples `
  --data-dir E:\automotive_cc\Practice_Dataset `
  --output HACKATHON\AI\artifacts\evaluation_6_samples.json
```

Evaluate một trip:

```powershell
python HACKATHON\AI\team_kit\evaluation.py `
  --predictions HACKATHON\AI\artifacts\predictions\T01-Sample.csv `
  --trip-dir E:\automotive_cc\Practice_Dataset\T01-Sample `
  --output HACKATHON\AI\artifacts\evaluation_T01-Sample.json
```

Evaluator chỉ đọc prediction và ground truth; không chạy lại inference và không
ghi đè CSV. Tham số đúng để lưu report là `--output`, không phải
`--output-json`.

## 11. Challenge 3 và Decision Engine

Challenge 3 bám công thức BTC và không dùng driver state:

```text
penalty = harsh_brake × 3 + harsh_accel × 2 + harsh_corner × 2
        + near_miss × 5 + speeding_pct_time × 0.15
safe_driving_score = clip(100 - penalty, 0, 100)
```

Decision Engine dùng C1/C2/C3, quality gate và temporal persistence để phát
event `open/update/resolved`. Ngưỡng ở `AI/configs/decision_engine.yaml`; tài
liệu chi tiết ở `AI/core/decision_engine/README.md`.

## 12. Hiệu năng và hướng tối ưu

Nút thắt hiện tại là:

1. Challenge 1: YOLOv8s và stereo SGBM trên road frames.
2. Challenge 2: YuNet và ONNX 468-landmark trên mỗi webcam frame.

Random Forest khoảng 15 MB nhưng không phải nút thắt chính; feature extraction
tốn thời gian hơn bước `predict` của RF.

Tối ưu CPU đã triển khai:

- C1 và C2 chạy song song trên hai worker vì không chia sẻ model/state.
- PyTorch/YOLO dùng 4 CPU threads thay vì chiếm toàn bộ logical cores.
- ONNX landmark dùng 1 intra-op thread để tránh tranh CPU với YOLO/OpenCV.

Benchmark 8 frame T01-Sample trên máy phát triển CPU-only: pipeline tuần tự cũ
khoảng `1.11 FPS`; scheduling mới khoảng `1.97 FPS` sau warm-up. Đây là benchmark
hiệu năng, không phải cam kết FPS cho mọi máy.

Kiểm tra CUDA:

```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU mode')"
```

Nếu có CUDA, đặt `device: 0` trong `AI/configs/challenge1.yaml`. Nếu chỉ smoke
test luồng, giới hạn số frame:

```powershell
python AI\scripts\end_to_end_demo.py `
  --trip-dir E:\automotive_cc\Practice_Dataset\T01-Sample `
  --camera 0 `
  --max-frames 100
```

Không tự đổi YOLOv8s thành model nhỏ hơn hoặc skip frame vì sẽ thay đổi C1. Bước
tối ưu sâu tiếp theo là benchmark ONNX execution provider, detector scheduling,
cache và road model nhẹ hơn rồi đánh giá lại TTC trước khi chấp nhận.

### Product-demo scheduling (không áp dụng cho CSV chấm điểm)

`end_to_end_demo.py` dùng multi-rate scheduling để giao diện không bị khóa bởi C1:

- Challenge 2 landmark/RF vẫn cập nhật trên mỗi frame webcam;
- YuNet chỉ hiệu chỉnh ROI mỗi 10 frame và chạy ngay nếu mất landmark;
- Challenge 1 chạy nền mỗi 5 frame hiển thị, UI dùng TTC gần nhất trong lúc chờ;
- khi máy xử lý chậm, BTC road frame cũ bị bỏ để demo bám wall-clock;
- JPEG gửi Dashboard vẫn chạy trên worker riêng.

Hai tham số có thể điều chỉnh là `--face-detector-interval 10` và
`--road-inference-interval 5`. `run_inference.py` không dùng các tối ưu skip/cache
này: nhánh CSV BTC vẫn inference đầy đủ từng frame.

## 13. Troubleshooting

- Webcam không mở: thử `--camera 1`.
- Profile cũ bị từ chối: chạy lại với `--enroll` để tạo schema v3 ONNX.
- SE connection refused: chạy Backend trước hoặc bỏ `--se-endpoint`.
- SE trả 404: kiểm tra đang chạy đúng repo/port và có module `ai_alerts`.
- Thiếu model: kiểm tra đủ ba artifact được liệt kê trong mục Setup.
- Warning ONNX/protobuf không phải lỗi nếu không có traceback và vẫn có output.

## 14. Quy tắc production

- Không commit artifacts, prediction, profile, webcam data hoặc secret.
- Không hard-code dataset path, API key hoặc CarSky credential.
- Không để Backend tính lại risk/severity của AI.
- Không sửa Challenge 3 để phục vụ Dashboard.
- Reset temporal state giữa các trip; batch luôn giữ timestamp order.
- Model mới phải có manifest, feature schema và report.
