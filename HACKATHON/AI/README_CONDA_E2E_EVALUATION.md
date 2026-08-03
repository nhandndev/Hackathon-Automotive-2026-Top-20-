# Conda environment cho End-to-End và chấm Challenge 1–2–3

File này chỉ quản lý environment Conda `dms-e2e-eval`. Environment này dành
cho AI inference, chạy luồng end-to-end và chấm local bằng evaluator BTC trong
`AI/team_kit`. Nó không thay thế `.venv` Python 3.11 của Backend.

## 1. Các file thuộc môi trường này

- `AI/environment.e2e-eval.yml`: dependency Conda dùng chung.
- `AI/README_CONDA_E2E_EVALUATION.md`: hướng dẫn đang đọc.
- Conda environment trên máy: `dms-e2e-eval`.

Không commit environment vật lý vào Git. Chỉ commit hai file ở trên.

## 2. Cài Miniforge nếu máy chưa có Conda

Kiểm tra:

```bash
conda --version
```

Máy macOS hiện tại cài Miniforge tại:

```text
/Users/lilnhan/miniforge3
```

Nạp Conda cho terminal hiện tại:

```bash
source /Users/lilnhan/miniforge3/etc/profile.d/conda.sh
```

Nếu muốn terminal mới tự nhận `conda`:

```bash
/Users/lilnhan/miniforge3/bin/conda init zsh
exec zsh
```

## 3. Tạo environment

Chạy từ thư mục gốc `HACKATHON`:

```bash
source /Users/lilnhan/miniforge3/etc/profile.d/conda.sh
conda env create -f AI/environment.e2e-eval.yml
conda activate dms-e2e-eval
```

Nếu environment đã tồn tại và file YAML vừa được cập nhật:

```bash
source /Users/lilnhan/miniforge3/etc/profile.d/conda.sh
conda env update -n dms-e2e-eval -f AI/environment.e2e-eval.yml --prune
conda activate dms-e2e-eval
```

## 4. Kiểm tra environment trước khi chạy

```bash
python --version
python -c "import cv2, joblib, numpy, onnxruntime, pandas, sklearn, torch, yaml; print('DMS AI environment OK'); print('torch:', torch.__version__); print('onnxruntime:', onnxruntime.__version__)"
python -c "from AI.team_kit.dataset_loader import TripDataset; from AI.team_kit.evaluation import evaluate; print('BTC Starter Kit imports OK')"
```

Kết quả mong đợi:

```text
DMS AI environment OK
BTC Starter Kit imports OK
```

## 5. Dataset và giới hạn điểm local

Đặt BTC Practice Dataset ngoài Git repository. Ví dụ:

```text
/duong-dan/Practice_Dataset/
├── T01-Sample/
├── T02-Sample/
├── T03-Sample/
├── T04-Sample/
├── T05-Sample/
└── T06-Sample/
```

Chỉ sáu trip `T01-Sample` đến `T06-Sample` có Ground Truth để chấm local.
Các trip scored/redacted dùng Hidden Ground Truth nên chỉ BTC có thể trả điểm
chính thức.

## 6. Chạy inference Challenge 1–2–3

Kích hoạt environment và chạy từ Git root:

```bash
source /Users/lilnhan/miniforge3/etc/profile.d/conda.sh
conda activate dms-e2e-eval

python AI/scripts/run_inference.py \
  --trip-dir /duong-dan/Practice_Dataset/T01-Sample \
  --output-csv AI/artifacts/predictions/T01-Sample.csv
```

CSV hợp lệ cho BTC phải có contract:

```text
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Không sửa tên cột và không lấy Ground Truth ghi vào prediction.

Xem đầy đủ option nếu CLI của branch hiện tại thay đổi:

```bash
python AI/scripts/run_inference.py --help
```

## 7. Chấm một trip bằng evaluator BTC

```bash
python AI/team_kit/evaluation.py \
  --predictions AI/artifacts/predictions/T01-Sample.csv \
  --trip-dir /duong-dan/Practice_Dataset/T01-Sample \
  --output AI/artifacts/evaluation_T01-Sample.json
```

Report sẽ chứa metric theo phần dự thi có dữ liệu hợp lệ:

- Challenge 1: TTC MAE, critical-zone MAE, RMSE, Precision, Recall, F1 và composite score.
- Challenge 2: Accuracy, per-class F1, macro-F1 và composite score.
- Challenge 3: trip-level safe-driving score và composite score theo evaluator công khai.

## 8. Chấm batch sáu Sample trip

Trước tiên phải có sáu CSV tương ứng trong cùng một thư mục:

```text
AI/artifacts/predictions_6_samples/
├── T01-Sample.csv
├── T02-Sample.csv
├── T03-Sample.csv
├── T04-Sample.csv
├── T05-Sample.csv
└── T06-Sample.csv
```

Chạy evaluator:

```bash
python AI/team_kit/evaluation.py \
  --predictions AI/artifacts/predictions_6_samples \
  --data-dir /duong-dan/Practice_Dataset \
  --output AI/artifacts/evaluation_6_samples.json
```

Có thể chạy vòng practice riêng của Challenge 1:

```bash
python AI/scripts/eval_practice.py --help
```

## 9. Chạy product end-to-end

Backend vẫn chạy bằng môi trường riêng:

```bash
cd SE/BE
source .venv/bin/activate
uvicorn app.main:app --reload
```

Mở terminal khác, từ Git root:

```bash
source /Users/lilnhan/miniforge3/etc/profile.d/conda.sh
conda activate dms-e2e-eval

python AI/scripts/end_to_end_demo.py \
  --trip-dir /duong-dan/Practice_Dataset/T01-Sample \
  --camera 0 \
  --driver-id driver_001
```

Đây là luồng thật: Challenge 1 + Challenge 2 + Challenge 3 → Decision Engine →
Backend/Fleet Dashboard. Không dùng mock để thay output của ba challenge.

Kiểm tra option chính xác của branch hiện tại:

```bash
python AI/scripts/end_to_end_demo.py --help
```

## 10. CPU, Apple Silicon và NVIDIA

File YAML mặc định dùng runtime cross-platform/CPU để evaluator chạy ổn định trên
macOS Apple Silicon. Chấm CSV không cần CUDA.

Máy NVIDIA dùng để inference realtime có thể cài PyTorch CUDA và
`onnxruntime-gpu` theo driver/CUDA thực tế của máy đó. Không cài đồng thời
`onnxruntime` và `onnxruntime-gpu` nếu chưa xác định runtime cần dùng. Sau khi
thay runtime phải chạy lại toàn bộ lệnh kiểm tra tại mục 4.

## 11. Lỗi thường gặp

### `conda: command not found`

```bash
source /Users/lilnhan/miniforge3/etc/profile.d/conda.sh
```

### `ModuleNotFoundError: pandas`

Environment chưa được tạo/cập nhật từ YAML:

```bash
conda env update -n dms-e2e-eval -f AI/environment.e2e-eval.yml --prune
```

### Evaluator không hiện Challenge 2 hoặc Challenge 3

Kiểm tra CSV có dữ liệu dùng được trong các cột:

```text
predicted_driver_state
predicted_risk_score
```

### Không thể tự tái tạo điểm BTC hidden test

Đây là đúng thiết kế. Local evaluator chỉ đo trên Sample Ground Truth; điểm
hidden chính thức phải do BTC chấm.

## 12. Xoá environment về sau

Khi được yêu cầu “xoá Conda environment chấm Challenge 1–2–3”, chạy:

```bash
source /Users/lilnhan/miniforge3/etc/profile.d/conda.sh
conda deactivate
conda env remove -n dms-e2e-eval -y
```

Kiểm tra đã xoá:

```bash
conda env list
```

Nếu người dùng yêu cầu xoá luôn tài liệu/cấu hình của environment này thì chỉ
xoá hai file sau, không xoá code AI hoặc Starter Kit BTC:

```text
AI/environment.e2e-eval.yml
AI/README_CONDA_E2E_EVALUATION.md
```

Không tự xoá Miniforge vì các Conda environment khác có thể đang sử dụng nó.
