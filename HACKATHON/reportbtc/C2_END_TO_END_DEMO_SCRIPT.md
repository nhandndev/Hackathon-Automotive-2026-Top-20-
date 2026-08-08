# Runbook demo end-to-end C2

> Chạy bằng Windows PowerShell từ
> `E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON`.

## 1. Chuẩn bị một lần

### 1.1 Phần mềm phải cài trên máy mới

- Git.
- **CPython 3.13 x64**. Không dùng Microsoft Store alias.
- **Node.js LTS x64 (22 trở lên)** và npm để chạy Fleet Dashboard.
- NVIDIA driver mới nếu máy có GPU NVIDIA; không bắt buộc để chạy CPU fallback.

Tải nhanh Python 3.13.14 Windows x64 dạng `.exe` từ Python.org:

```text
https://www.python.org/ftp/python/3.13.14/python-3.13.14-amd64.exe
```

Khi chạy installer, chọn `Add python.exe to PATH` và `Install launcher for all
users`, sau đó mở PowerShell mới. Có thể tải và mở installer bằng lệnh:

```powershell
$pythonInstaller = Join-Path $env:TEMP "python-3.13.14-amd64.exe"
Invoke-WebRequest `
  -Uri "https://www.python.org/ftp/python/3.13.14/python-3.13.14-amd64.exe" `
  -OutFile $pythonInstaller
Start-Process -FilePath $pythonInstaller -Wait
```

Cài Node.js LTS tự động bằng Windows Package Manager:

```powershell
winget install --id OpenJS.NodeJS.LTS --exact --source winget `
  --accept-package-agreements --accept-source-agreements
```

Nếu máy không có `winget`, tải installer Windows x64 tại:

```text
https://nodejs.org/en/download
```

Đóng và mở lại PowerShell sau khi cài Python/Node.

Kiểm tra trước khi tạo môi trường:

```powershell
py -3.13 --version
node --version
npm --version
```

Nếu `py -3.13` không tồn tại, cài Python 3.13 x64 và mở terminal mới. Có thể
dùng trực tiếp đường dẫn `python.exe` đã cài thay cho `py -3.13`.

### 1.2 Clone và tạo `.venv`

`.venv` không được push lên Git. Mỗi máy phải tự tạo tại root `HACKATHON`:

```powershell
git clone <repository-url>
cd Hackathon-Automotive-2026\HACKATHON

py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt
```

Prompt phải có `(.venv)`. Xác nhận đúng interpreter và dependencies:

```powershell
python --version
python -c "import sys; print(sys.executable)"
python -c "import cv2, fastapi, httpx, onnxruntime, pydantic_settings, sklearn, torch, ultralytics, uvicorn, yaml; print('Python dependencies OK')"
python -c "import torch, onnxruntime as ort; print('Torch CUDA:', torch.cuda.is_available()); print('ORT:', ort.get_available_providers())"
```

`sys.executable` phải trỏ vào `HACKATHON\.venv\Scripts\python.exe`. Máy NVIDIA
nên thấy `Torch CUDA: True` và `CUDAExecutionProvider`; nếu không, hệ thống vẫn
có CPU fallback nhưng demo sẽ chậm hơn.

### 1.3 Cài Frontend

```powershell
cd SE\FE
npm install
npm run build
cd ..\..
```

### 1.4 Model artifacts và cấu hình

Ba file sau bắt buộc phải có:

```powershell
Test-Path AI\models\driver_state_current.joblib
Test-Path AI\models\face_landmark_468.onnx
Test-Path AI\models\face_detection_yunet_2023mar.onnx
```

Tất cả phải trả về `True`. Hiện hai file `.onnx` bị ignore bởi
`AI/.gitignore`, vì vậy duy trì phải phát hành chúng qua Git LFS/release hoặc
gửi kèm model package; máy clone đặt đúng vào `AI\models\` trước khi chạy.

Tạo cấu hình Backend cục bộ:

```powershell
Copy-Item SE\BE\.env.example SE\BE\.env
```

Điền CarSky external credential vào `SE/BE/.env`. Không commit hoặc chiếu secret.
APK realtime phải được cài và mở sẵn trên Android node.

### 1.5 Personalized driver profile (tùy chọn)

Nếu dùng personalization, enroll một lần:

```powershell
python AI\scripts\webcam_driver_demo.py `
  --camera 0 `
  --driver-id driver_001 `
  --enroll
```

## 2. Demo A — BTC road + webcam tài xế

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode hybrid-live `
  -TripDir E:\automotive_cc\Practice_Dataset\T01-Sample `
  -Camera 0 `
  -DriverId driver_001 `
  -OpenDashboard
```

Runner kiểm tra môi trường/CarSky, mở Backend và Dashboard rồi chạy AI. Nhấn
`Q/Esc` ở cửa sổ AI để kết thúc. Bỏ `-DriverId` để dùng global model.

## 3. Demo B — nhiều trip từ một folder

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir E:\automotive_cc\Practice_Dataset `
  -OpenDashboard
```

Mỗi thư mục con phải là trip BTC đầy đủ: `<trip_id>.json(.gz)`, `driver/`,
`kitti/image_2`, `kitti/image_3` và calibration. Chỉ cần đổi `-DataDir` để dùng
dataset khác. Tất cả trip xuất hiện ngay; AI chạy tuần tự, Dashboard giữ trip đã
hoàn thành. Sau trip cuối, nhấn Enter tại terminal mới dừng services.

## 4. Bằng chứng cần chỉ trong demo

1. Cửa sổ AI có road/cabin thật, TTC, Driver State và Risk Score.
2. Dashboard có metrics thật và trip `pending/running/completed`.
3. Một `event_id` khớp tại AI JSONL và Backend:

```text
GET http://127.0.0.1:8000/api/v1/alerts/recent
GET http://127.0.0.1:8000/api/v1/alerts/trips
WS  ws://127.0.0.1:8000/api/v1/alerts/live
```

4. CarSky Signal Watch/HMI đổi theo cùng event có audience `driver_display`.
5. Giải thích Decision Engine không gửi heartbeat: chỉ `open`, thay đổi có ý
   nghĩa và `resolved`.

Lưu ý: JPEG annotate gửi Dashboard là lựa chọn demo trực quan; canonical
DecisionEvent vẫn là contract tích hợp chính.

## 5. Nhánh submission riêng

```powershell
python AI\scripts\run_inference.py `
  --data-dir E:\automotive_cc\Practice_Dataset `
  --samples-only `
  --out AI\artifacts\predictions_6_samples

python AI\team_kit\evaluation.py `
  --predictions AI\artifacts\predictions_6_samples `
  --data-dir E:\automotive_cc\Practice_Dataset `
  --output AI\artifacts\evaluation_6_samples.json
```

Submission inference từng frame và không cần Backend, Dashboard hay CarSky.

## 6. Backup và troubleshooting

Replay event AI đã sinh nếu external runtime lỗi:

```powershell
python AI\scripts\send_decision_events.py `
  --events <file.events.jsonl> `
  --endpoint http://127.0.0.1:8000/api/v1/alerts
```

| Lỗi | Xử lý ngắn |
|---|---|
| PowerShell không chạy script | `Set-ExecutionPolicy -Scope Process Bypass` |
| Thiếu `onnxruntime` | Activate `.venv`, cài lại `AI\requirements.txt` |
| Profile schema cũ | Enroll lại với `--enroll` |
| Dashboard offline | Kiểm tra `http://127.0.0.1:8000/health` |
| HMI không đổi | Kiểm tra deployment/node/token và ADB còn mở |
| Chưa có alert | Giữ hành vi đủ temporal gate; không hạ threshold tại chỗ |
| Chỉ test Dashboard, chưa dùng CarSky | Thêm `-SkipCarSkyPreflight` và nói rõ phạm vi demo |

## 7. Tiêu chí pass

- AI sinh event thật; Backend nhận `accepted=true` và chống duplicate.
- Dashboard hiển thị ảnh/metrics/event đúng `trip_id`.
- Event `driver_display` đi đến CarSky/HMI khi external runtime khả dụng.
- Team phân biệt rõ submission, realtime demo, event replay và mock transport.
- Có video, JSONL, evaluation JSON và screenshot backup; không lộ secret.
