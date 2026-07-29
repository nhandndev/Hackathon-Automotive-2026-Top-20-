# Phase Challenge 1 AI — Road / TTC Estimation

File này ghi nhận trạng thái sau khi merge phần **Challenge 1 AI** vào repository. Đây chỉ là đánh giá tài liệu/kỹ thuật hiện tại, chưa chỉnh code.

## 1. Mục tiêu Challenge 1

Challenge 1 phụ trách ước lượng **Time-to-Collision (TTC)** từ dữ liệu road camera/stereo/telemetry.

Output cốt lõi của Challenge 1:

```csv
frame_id,timestamp,predicted_ttc
```

Trong submission tổng cuối cùng, `predicted_ttc` sẽ được ghép với Challenge 2 và Challenge 3 để tạo:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

## 2. Folder/code đã có

Phần Challenge 1 hiện nằm trong:

```text
AI/
├── configs/
│   ├── bytetrack_vru.yaml
│   └── challenge1.yaml
├── core/
│   └── challenge1_road/
│       ├── detection.py
│       ├── depth.py
│       ├── predict_ttc.py
│       └── ttc_engine.py
└── scripts/
    ├── run_inference.py
    ├── eval_practice.py
    ├── extract_features.py
    ├── loto_postprocess.py
    ├── train_ttc_model.py
    ├── train_ttc_model2.py
    └── tune_output_map.py
```

## 3. Những gì đã đạt được

### 3.1 Có core inference riêng cho TTC

File chính:

```text
AI/core/challenge1_road/predict_ttc.py
```

Core chính:

```python
RoadTTCPredictor
```

Vai trò:

- nhận calibration;
- nhận stereo frame trái/phải;
- nhận ego speed;
- trả về `min_ttc` theo frame.

Đây là hướng tốt vì có một core inference riêng, tránh copy thuật toán rải rác.

### 3.2 Có pipeline detection + tracking

File:

```text
AI/core/challenge1_road/detection.py
```

Đã có:

- YOLOv8 detector.
- ByteTrack tracking thông qua `ultralytics`.
- Mapping COCO class sang target class:
  - car/bus/truck → `vehicle`;
  - motorcycle/bicycle → `motorcycle`;
  - person → `pedestrian`.

Điểm tốt:

- Có `track_id`, phù hợp để tính closing speed theo thời gian.
- Có graceful fallback nếu YOLO/torch/weights không khả dụng.

### 3.3 Có stereo depth estimation

File:

```text
AI/core/challenge1_road/depth.py
```

Đã có:

- OpenCV StereoSGBM.
- Depth map từ disparity.
- Estimate depth theo bbox.
- Monocular fallback dựa trên bbox height.
- Upsample disparity để giảm quantization.

Điểm tốt:

- Có xử lý noise stereo bằng median/percentile trong bbox.
- Có giới hạn trust depth.
- Có fallback nếu stereo depth yếu.

### 3.4 Có TTC engine temporal

File:

```text
AI/core/challenge1_road/ttc_engine.py
```

Đã có:

- Track history theo object.
- Closing speed từ slope depth theo thời gian.
- Lateral offset / collision cone.
- TTC 1D và 2D.
- Looming TTC từ bbox expansion.
- Feature snapshot để train model sau.

Điểm tốt:

- Có logic tránh adjacent-lane false positive qua collision cone.
- Có hỗ trợ target cắt vào làn.
- Có `last_features` phục vụ learned model.

### 3.5 Có fallback TTC đơn giản cho SE contract

Trong `predict_ttc.py` có helper:

```python
predict_ttc(telemetry_data, road_vision_data=None)
```

Vai trò:

- Cho caller không có vision pipeline vẫn lấy được TTC guess.
- Trả `"inf"` nếu không có nguy cơ.
- Trả `"1.2"` hoặc `"1.8"` nếu braking mạnh + speed cao.

Điểm tốt:

- Hữu ích cho mock/demo hoặc fallback Backend.
- Không làm toàn hệ thống chết nếu vision chưa sẵn.

### 3.6 Có script inference xuất CSV

File:

```text
AI/scripts/run_inference.py
```

Hỗ trợ:

```bash
python AI/scripts/run_inference.py --trip-dir <trip> --out <out>
python AI/scripts/run_inference.py --data-dir <data_root> --out <out>
```

Output:

```text
<out>/<trip_id>.csv
```

Columns:

```csv
frame_id,timestamp,predicted_ttc
```

Điểm tốt:

- Có batch mode cho nhiều trip.
- Có logging progress.
- Nếu một frame fail thì ghi `inf`, không kill cả trip.

### 3.7 Có config tách khỏi code

File:

```text
AI/configs/challenge1.yaml
```

Config có:

- YOLO detector config.
- SGBM disparity config.
- TTC thresholds.
- ROI fallback.

Điểm tốt:

- Threshold có thể tune mà không sửa source.
- Phù hợp workflow experiment.

### 3.8 Có hướng learned model

Files:

```text
AI/scripts/extract_features.py
AI/scripts/train_ttc_model.py
```

Đã có:

- Extract feature per frame.
- Train XGBoost inverse-TTC model.
- Leave-one-trip-out CV.
- Save model `artifacts/ttc_model.json`.

Điểm tốt:

- Có anti-overfit check theo trip.
- Hướng train inverse-TTC hợp lý vì `inf` map về 0.

### 3.9 Cập nhật mới: TTC post-processing tốt hơn trước

Sau lần cập nhật mới, Challenge 1 TTC có thêm nhiều xử lý thực tế hơn để tăng điểm scoring:

File chính:

```text
AI/core/challenge1_road/predict_ttc.py
AI/core/challenge1_road/ttc_engine.py
AI/configs/challenge1.yaml
AI/scripts/loto_postprocess.py
AI/scripts/tune_output_map.py
```

Các điểm tốt mới:

- Có đọc depth keyframe `.npy` từ `kitti/depth/*.npy` nếu trip có dữ liệu này.
- Có normalize depth sentinel lớn thành `inf`, tránh lấy depth rác làm depth thật.
- Có optical/looming TTC từ bbox expansion để bắt các object cut-in/transient nhanh.
- Có hold TTC qua vài frame mất detection, tránh output `inf` ngắt quãng ở đoạn nguy hiểm.
- Có `no_detection_floor`, giảm rủi ro báo `inf` khi detector hụt object.
- Có danger confirmation filter, giảm false positive khi TTC nhảy xuống dưới 2 giây do nhiễu.
- Có script leave-one-trip-out validation cho post-processing knobs.
- Có script tune output mapping để kiểm tra scale/demote/floor.

Nhận xét:

- Đây là cập nhật có giá trị thật cho Challenge 1, vì nó xử lý đúng các lỗi hay làm mất điểm: missing detection, TTC jitter, depth nhiễu, false danger và `inf` sai thời điểm.
- Việc thành viên báo điểm tăng là hợp lý về mặt kỹ thuật.
- Tuy nhiên repo hiện chưa có file prediction/report score được commit, nên chưa thể xác nhận con số điểm tăng cụ thể nếu chưa chạy lại `eval_practice.py`.

Command cần yêu cầu AI team gửi log để xác nhận điểm:

```bash
python AI/scripts/eval_practice.py
```

Dòng cần xem:

```text
AVERAGE COMPOSITE: xx.x / 100
```

## 4. Readiness hiện tại

| Hạng mục | Mức sẵn sàng | Nhận xét |
|---|---:|---|
| Core TTC logic | 82% | Có pipeline rõ hơn, thêm depth `.npy`, looming TTC, hold gap, floor và danger confirmation |
| Inference CSV Challenge 1 | 70% | Có script xuất CSV, nhưng vẫn phụ thuộc dataset/starter kit/dependency |
| Evaluation practice | 62% | Có script eval và LOTO tuning, nhưng vẫn hardcode path dataset |
| Learned model workflow | 50% | Có thêm hướng train/tune, nhưng cần dependency + feature artifacts + kiểm chứng |
| Tích hợp Backend AITrip JSON | 35% | Chưa có adapter từ TTC CSV/core sang AI canonical JSON |
| Demo realtime với HMI | 30% | Chưa có stream realtime từ AI Challenge 1 vào Backend/HMI |

Đánh giá tổng Challenge 1 AI hiện tại:

```text
Khoảng 70–78% cho phần research/inference foundation.
Khoảng 35–45% cho phần integration với Backend/demo realtime.
```

Ghi chú merge:

- Chưa merge Challenge 1 vào pipeline full Backend/HMI cho đến khi có log `eval_practice.py`, dependency rõ ràng và output CSV sample.
- Khi Challenge 1 đủ ổn, merge theo hướng adapter/export, không sửa Backend contract để chạy theo nội bộ của Challenge 1.
- Challenge 1 chỉ chịu trách nhiệm `predicted_ttc`; driver state và risk score sẽ ghép sau từ Challenge 2/3.

## 5. Những rủi ro/chưa hoàn thiện

### 5.1 Chưa thấy dependency file riêng cho AI

Hiện chưa thấy:

```text
AI/requirements.txt
```

Các dependency có khả năng cần:

```text
opencv-python
numpy
pyyaml
ultralytics
torch
pandas
xgboost
pyarrow hoặc fastparquet
```

Nếu không có file dependency, thành viên mới hoặc AI Agent sau này khó chạy lại.

### 5.2 Phụ thuộc `team_kit`

`run_inference.py` cần:

```python
team_kit.dataset_loader.TripDataset
```

Script `_find_team_kit()` chỉ search dưới `AI_ROOT`.

Nếu starter kit không nằm dưới `AI/`, script có thể fail:

```text
Could not find team_kit/dataset_loader.py
```

Cần xác nhận vị trí official starter kit trong repo.

### 5.3 Một số script hardcode dataset path

Các file:

```text
AI/scripts/eval_practice.py
AI/scripts/extract_features.py
AI/scripts/train_ttc_model.py
```

có path kiểu:

```text
AI/Dataset/Dataset/...
```

Rủi ro:

- Máy thành viên khác có dataset ở path khác.
- CI/Backend không chạy được.

Nên chuyển sang CLI args hoặc env config sau.

### 5.4 Output Challenge 1 chưa phải output tổng

Hiện Challenge 1 chỉ xuất:

```csv
frame_id,timestamp,predicted_ttc
```

Đây là đúng cho Challenge 1, nhưng chưa đủ cho submission tổng:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Cần Challenge 2 + Challenge 3/fusion để ghép.

### 5.5 Chưa có adapter sang Backend AI contract

Backend đang dùng AITrip canonical có:

```text
frame.min_ttc
frame.driver.state
frame.risk.final_risk_score
```

Challenge 1 hiện mới tạo TTC CSV hoặc trả `min_ttc` qua core predictor.

Cần adapter:

```text
RoadTTCPredictor output → AITrip.frames[].min_ttc
```

Quy ước:

- Python nội bộ: `float("inf")`.
- CSV submission: `inf`.
- REST/WebSocket JSON: `"Infinity"`.

Không chuyển `inf` thành `0`.

### 5.6 Rủi ro auto-download YOLO weights

Config:

```yaml
detector:
  weights: yolov8n.pt
```

Ultralytics có thể auto-download weights lần đầu.

Nếu môi trường không có mạng:

- detector unavailable;
- pipeline fallback về ROI baseline;
- vẫn có CSV nhưng chất lượng có thể thấp.

Nên lưu ý khi chạy ở môi trường nộp bài/offline.

## 6. Lỗi/rủi ro kỹ thuật riêng của Challenge 1

Phần này chỉ nói lỗi hoặc rủi ro của **Challenge 1 AI Road/TTC**, không tính Backend, Frontend, HMI hoặc CarSky.

### 6.1 `depth_for_bbox()` có logic threshold chưa đúng

File:

```text
AI/core/challenge1_road/depth.py
```

Đoạn hiện tại:

```python
finite = patch[np.isfinite(patch)]
if finite.size:
    return float(np.percentile(finite, 25))
if finite.size < 20:
    return None
return float(np.median(finite))
```

Vấn đề:

- Nếu chỉ có 1 pixel depth hợp lệ thì `finite.size` vẫn true và return ngay.
- Nhánh `if finite.size < 20` gần như không có tác dụng khi có 1–19 pixel hợp lệ.
- Nhánh `return median` cuối gần như unreachable.

Ảnh hưởng:

- Depth trong bbox nhỏ/yếu texture có thể bị nhiễu.
- TTC có thể jitter hoặc sai ở frame critical.

Mức độ: `Medium`.

Gợi ý sửa sau này:

```python
finite = patch[np.isfinite(patch)]
if finite.size < 20:
    return None
return float(np.percentile(finite, 25))
```

### 6.2 Config `ttc` chưa thật sự điều khiển hết engine

File:

```text
AI/configs/challenge1.yaml
AI/core/challenge1_road/ttc_engine.py
```

Config có:

```yaml
ttc:
  ego_half_width_m: 1.2
  corridor_growth: 0.02
  min_closing_speed: 0.5
  smooth_window: 5
```

Nhưng engine đang dùng constant trong code:

```python
EGO_HALF_WIDTH_M = 2.6
CORRIDOR_GROWTH = 0.02
MIN_CLOSING_SPEED = 0.3
SMOOTH_WINDOW = 13
```

Vấn đề:

- Người tune `challenge1.yaml` có thể tưởng đã đổi threshold, nhưng engine vẫn dùng constant.
- `smooth_window` trong config dễ bị nhầm với `smooth_out` output smoothing.

Mức độ: `Medium`.

Gợi ý:

- Truyền `ttc_cfg` vào `TTCEngine`.
- Đổi tên config rõ hơn, ví dụ `engine_history_window` và `output_smooth_window`.

### 6.3 Chưa có dependency manifest cho AI

Hiện chưa thấy:

```text
AI/requirements.txt
```

Rủi ro:

- Người khác clone repo không biết cài gì.
- AI Agent sau này dễ mất thời gian vì lỗi import.

Dependency có khả năng cần:

```text
opencv-python
numpy
pyyaml
ultralytics
torch
pandas
xgboost
pyarrow hoặc fastparquet
```

Mức độ: `High`.

### 6.4 `team_kit` discovery có thể fail

File:

```text
AI/scripts/run_inference.py
```

Code search:

```python
for cand in AI_ROOT.rglob("team_kit/dataset_loader.py"):
    return cand.parent.parent
```

Vấn đề:

- Chỉ tìm dưới `AI/`.
- Trong repo hiện tại chưa thấy `AI/**/team_kit/dataset_loader.py`.
- Nếu starter kit nằm trong `docs/` hoặc máy local khác, script không chạy.

Mức độ: `High` nếu muốn chạy lại ngay.

Gợi ý:

- Thêm CLI arg `--starter-kit-dir`.
- Hoặc document rõ vị trí starter kit trong `AI/README.md`.

### 6.5 Script training/eval hardcode dataset path

Files:

```text
AI/scripts/eval_practice.py
AI/scripts/extract_features.py
AI/scripts/train_ttc_model.py
```

Có path kiểu:

```python
DATA = AI_ROOT / "Dataset" / "Dataset" / "Practice_Dataset 2"
KIT = AI_ROOT / "Dataset" / "Dataset" / "Package_starterkit" / "package_starterkit"
```

Vấn đề:

- Không portable.
- Máy thành viên khác dễ fail.
- CI/handoff khó chạy.

Mức độ: `Medium/High`.

Gợi ý:

- Đưa dataset path thành CLI args.
- Hoặc dùng config/env.

### 6.6 YOLO weights auto-download là rủi ro môi trường

Config:

```yaml
weights: yolov8n.pt
```

Vấn đề:

- Ultralytics có thể cần tải model lần đầu.
- Nếu môi trường offline hoặc bị chặn mạng, detector không dùng được.
- Pipeline fallback về ROI baseline, nhưng chất lượng có thể thấp.

Mức độ: `Medium`.

Gợi ý:

- Lưu weight local hoặc ghi rõ cách chuẩn bị.
- Log rõ khi đang fallback baseline.

### 6.7 `run_inference.py` có thể che lỗi lớn bằng cách ghi toàn `inf`

File:

```text
AI/scripts/run_inference.py
```

Đoạn:

```python
except Exception as e:
    logger.warning("frame %d failed: %s", frame.frame_id, e)
    ttc = float("inf")
```

Điểm tốt:

- Một frame lỗi không làm chết cả trip.

Rủi ro:

- Nếu lỗi xảy ra ở nhiều frame/toàn trip, script vẫn có thể xuất CSV toàn `inf`.
- Người chạy có file output nhưng chất lượng gần như không dùng được.

Mức độ: `Medium`.

Gợi ý:

- Đếm fail frame.
- Nếu fail rate vượt ngưỡng, exit non-zero.
- Report tỷ lệ `inf` trong CSV.

### 6.8 `format_ttc()` đúng cho CSV nhưng cần chú ý khi qua Backend JSON

File:

```text
AI/core/challenge1_road/predict_ttc.py
```

Hiện tại:

```python
if ttc is None or not math.isfinite(ttc):
    return "inf"
```

Điều này đúng cho CSV Challenge 1.

Nhưng Backend JSON boundary đang dùng:

```json
"Infinity"
```

Rủi ro:

- Nếu copy `"inf"` thẳng vào JSON contract Backend có thể lệch schema.
- Không được biến `inf` thành `0`.

Mức độ: `Low/Medium`.

### 6.9 Chưa có test tự động riêng cho Challenge 1

Hiện chưa thấy:

```text
AI/tests/
```

Rủi ro:

- Không có smoke test import core.
- Không có test `format_ttc`.
- Không có test CSV columns.
- Không có test fallback khi detector unavailable.

Mức độ: `Medium`.

Gợi ý:

- Test `format_ttc`.
- Test `predict_ttc` telemetry fallback.
- Test `run_inference` với fake/minimal dataset nếu chưa có dataset thật.

### 6.10 Chưa có output adapter sang full submission/fusion

Challenge 1 output đúng phạm vi:

```csv
frame_id,timestamp,predicted_ttc
```

Nhưng full system cần:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Mức độ: `Medium`.

Gợi ý:

- Không sửa Challenge 1 để tự biết driver/risk.
- Tạo fusion/export layer ở Challenge 3 hoặc shared script.
- Backend/AI integration nhận TTC từ Challenge 1 và ghép với Challenge 2/3.

### 6.11 Lưu ý mới: config và tuning script có thể đang lệch giá trị

File:

```text
AI/configs/challenge1.yaml
AI/scripts/loto_postprocess.py
```

Config hiện ghi:

```yaml
no_detection_floor: 15.0
danger_confirm_frames: 8
danger_confirm_band: 3.0
danger_demote_to: 2.5
```

Nhưng trong `loto_postprocess.py` phần committed config vẫn có:

```python
committed = dict(hold_frames=6, floor=12.0, confirm_frames=8, confirm_band=3.0, demote_to=2.5)
```

Vấn đề:

- Có thể điểm mà team báo dựa trên config khác với config đang chạy thật.
- Cần xác nhận `eval_practice.py` đang chạy đúng `AI/configs/challenge1.yaml`.
- Khi báo điểm, phải ghi rõ config/version nào được dùng.

Mức độ: `Medium`.

Gợi ý:

- AI team gửi kèm log `eval_practice.py`.
- Ghi rõ commit/config dùng để tạo prediction.
- Nếu `floor=15.0` là giá trị chốt, cập nhật script validation cho đồng bộ.

## 7. Smoke test nên yêu cầu AI team bổ sung

Cần một command tối thiểu để chứng minh Challenge 1 chạy được:

```bash
cd AI
python scripts/run_inference.py \
  --trip-dir <path-to-one-trip> \
  --out predictions/FPTU_DMS_Vision \
  --config configs/challenge1.yaml
```

Expected:

```text
predictions/FPTU_DMS_Vision/<trip_id>.csv
```

Và CSV có:

```csv
frame_id,timestamp,predicted_ttc
```

Nên có thêm check:

```bash
python - <<'PY'
import pandas as pd
p = "predictions/FPTU_DMS_Vision/T01d.csv"
df = pd.read_csv(p)
print(df.head())
print(df.shape)
print(df.columns.tolist())
PY
```

## 8. Việc nên làm tiếp cho Challenge 1

Ưu tiên cao:

1. Thêm `AI/requirements.txt`.
2. Thêm `AI/README.md` hướng dẫn chạy Challenge 1.
3. Chuẩn hóa dataset/starter-kit path.
4. Thêm smoke test một trip.
5. Ghi rõ output format và `inf` convention.

Ưu tiên trung bình:

1. Chuyển hardcoded path trong scripts sang CLI args.
2. Lưu model/weights/artifact rõ ràng.
3. Thêm script validate CSV Challenge 1.
4. Thêm adapter sang Backend contract.

Ưu tiên sau:

1. Tối ưu model learned TTC.
2. Benchmark từng trip.
3. Tạo realtime predictor wrapper cho demo.

## 9. Gợi ý tích hợp với Backend sau này

Backend không nên gọi thẳng script CSV trong request realtime.

Nên có adapter/service riêng:

```text
AI Road Predictor
  ↓
Challenge1FrameResult
  ↓
Backend AITrip canonical frame
```

Schema adapter gợi ý:

```json
{
  "frame_id": 120,
  "timestamp": 6.0,
  "min_ttc": "Infinity",
  "road_debug": {
    "source": "challenge1_road",
    "use_detector": true,
    "n_obs": 2,
    "n_in_cone": 1
  }
}
```

Backend sau đó ghép với:

- Challenge 2 driver state.
- Challenge 3 risk score.
- Metadata/telemetry.

## 10. Kết luận

Challenge 1 AI đã có nền tảng tốt cho TTC estimation:

- detector/tracker;
- stereo depth;
- TTC temporal engine;
- inference CSV;
- config;
- hướng learned model.

Nhưng hiện tại vẫn là **Challenge 1 standalone foundation**, chưa phải pipeline AI full để Backend/HMI dùng ngay.

Trước khi Backend phụ thuộc chính thức, cần AI team bổ sung dependency, README chạy, path dataset chuẩn, smoke test và adapter output sang contract chung.
