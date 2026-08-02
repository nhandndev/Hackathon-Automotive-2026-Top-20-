# FPTU DMS Vision — Runbook demo end-to-end C2

> Mục tiêu: chứng minh một cảnh báo do AI tạo đi xuyên suốt `AI → Backend → Fleet Dashboard + CarSky → Android HMI`.
> Các lệnh dưới đây dành cho Windows PowerShell và chạy từ Git repo root
> `E:\automotive_cc\Hackathon-Automotive-2026`, trừ khi có ghi khác.

## 1. Phân biệt hai luồng

### Luồng A — inference và evaluate BTC

```text
BTC trips → C1/C2/C3 → CSV → evaluator
```

Luồng này dùng để đo chất lượng submission. Không cần Backend, Frontend, CarSky
hay webcam. Xem mục 8.

### Luồng B — demo sản phẩm end-to-end

```text
BTC road-left/right + telemetry ─┐
webcam + driver profile ─────────┼→ C1/C2/C3 → Decision Engine
                                 └→ DecisionEvent
                                      │ POST /api/v1/alerts
                                      ▼
                                  Backend SE
                                   ├→ WebSocket → Dashboard live
                                   └→ CarSky VSS → Android HMI
```

Luồng B mới là demo kết nối toàn sản phẩm. CSV/evaluator không phải thành phần
trung gian của luồng này.

## 2. Quyền sở hữu contract

- AI quyết định `alert_type`, `severity`, `audiences`, `recommended_action`,
  evidence và lifecycle `open/update/resolved`.
- Backend chỉ validate, chống gửi trùng, lưu recent, broadcast và map sang tên
  signal CarSky; Backend không tính lại severity/risk.
- Dashboard nhận canonical DecisionEvent qua WebSocket.
- CarSky/HMI nhận signal đã dịch từ chính DecisionEvent đó.
- Muốn đổi field hoặc semantics phía AI phải thống nhất với AI owner trước.

Endpoint sử dụng:

```text
POST http://127.0.0.1:8000/api/v1/alerts
GET  http://127.0.0.1:8000/api/v1/alerts/recent
WS   ws://127.0.0.1:8000/api/v1/alerts/live
```

## 3. Chuẩn bị một lần

### 3.1 AI

```powershell
conda activate automotive
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON
pip install -r AI\requirements.txt
python -c "import cv2, onnxruntime, sklearn, ultralytics; print('AI OK')"
```

Kiểm tra các artifact bắt buộc:

```powershell
Test-Path AI\models\driver_state_rf_v3_onnx.joblib
Test-Path AI\models\face_landmarker_192.onnx
Test-Path AI\models\face_detection_yunet_2023mar.onnx
```

Cả ba lệnh phải trả về `True`. Dataset BTC có thể nằm ngoài repo, ví dụ
`E:\automotive_cc\Practice_Dataset\T01-Sample`.

### 3.2 Backend

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\BE
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Điền `.env` trên máy operator, không commit và không chiếu secret:

```dotenv
CARSKY_ENABLED=true
CARSKY_MODE=external
CARSKY_BASE_URL=https://hackathon-1.carsky.io
CARSKY_API_KEY=<secret>
CARSKY_AUTH_MODE=bearer
CARSKY_ROOM_ID=<room-id>
CARSKY_NODE_KEY=<signal-broker-node-key>
CARSKY_ANDROID_NODE_KEY=<android-node-key>
```

Nếu tài khoản CarSky dùng `X-API-Key`, đổi `CARSKY_AUTH_MODE=x-api-key`.

### 3.3 Frontend

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\FE
npm install
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
```

`.env.local` cần:

```dotenv
VITE_ALERTS_WS_URL=ws://127.0.0.1:8000/api/v1/alerts/live
```

### 3.4 Driver profile

Profile là tùy chọn nhưng nên có trong demo personalized. Enrollment chỉ cần làm
một lần cho mỗi `driver-id`:

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON
conda activate automotive
python AI\scripts\webcam_driver_demo.py --camera 0 --driver-id driver_001 --enroll
```

Làm đúng hành động trên UI; chỉ bấm `Space` khi indicator hợp lệ. Nếu profile cũ
báo `Unsupported profile schema`, chạy enrollment lại để tạo schema v3.

### 3.5 Build và cài HMI realtime

HMI chính thức đọc VHAL từ CarSky bridge và không có mock fallback. Build APK mới
bằng Android Studio hoặc Gradle:

Nếu chỉ cần cài ngay qua CarSky ADB, dùng file đã chuẩn bị:

```text
SE/HMI/release/adb_install_realtime_hmi.txt
```

Copy từng dòng theo đúng thứ tự vào ADB widget. Bản release đã xác minh là VHAL
realtime, không chứa mock hoặc CarSky credential.

Nếu cần build lại source mới bằng Android Studio hoặc Gradle:

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\HMI
gradle :app:assembleDebug
```

Sau đó cài đúng APK mới qua helper Backend:

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\BE
.\.venv\Scripts\Activate.ps1
python scripts\carsky_phase05.py install-apk ..\HMI\app\build\outputs\apk\debug\app-debug.apk
```

Không dùng APK cũ trong `build/` nếu chưa build lại sau thay đổi này. HMI tự đổi
SAFE/WARNING/CRITICAL khi Backend dừng là dấu hiệu đang cài nhầm APK mock cũ.

## 4. Preflight trước buổi demo

### 4.1 Test Backend

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\BE
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python scripts\carsky_phase05.py status
python scripts\carsky_phase05.py nodes
python scripts\carsky_phase05.py values
```

Ba lệnh CarSky chỉ đọc trạng thái. Không tạo hoặc xóa deployment.

### 4.2 Test Frontend

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\FE
npm run lint
npm run build
```

### 4.3 Test camera và AI ngắn

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON
conda activate automotive
python AI\scripts\end_to_end_demo.py `
  --trip-dir E:\automotive_cc\Practice_Dataset\T01-Sample `
  --camera 0 `
  --driver-id driver_001 `
  --max-frames 20 `
  --events AI\artifacts\decision_events\preflight.events.jsonl
```

Bỏ `--driver-id` nếu chưa dùng personalization. Đổi `--camera 1` nếu camera 0
không đúng.

## 5. Chạy demo thật — 4 cửa sổ

### Cửa sổ 1 — Backend

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\BE
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở và kiểm tra:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/v1/alerts/recent
```

`/ready` có thể trả 503 nếu cache dataset dành cho module replay chưa đủ; điều
này không chặn endpoint DecisionEvent. Dùng `/health` làm health check demo.

### Cửa sổ 2 — Fleet Dashboard

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\FE
npm run dev
```

Mở URL Vite in ra, thường là `http://127.0.0.1:5173`. Panel `AI DECISION
ENGINE` phải hiện `LIVE`. Fleet map/trip nền hiện vẫn là mock; chỉ panel này là
event realtime từ Backend và phải nói rõ khi trình bày.

### Cửa sổ 3 — CarSky

Mở `https://hackathon-1.carsky.io/`, chọn đúng room/deployment rồi mở:

- Signal Watch;
- Android Screen/HMI;
- deployment status nếu cần chứng minh runtime đang Running.

Không mở `.env`, token hoặc API key trên màn hình.

### Cửa sổ 4 — AI hybrid runtime

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON
conda activate automotive
python AI\scripts\end_to_end_demo.py `
  --trip-dir E:\automotive_cc\Practice_Dataset\T01-Sample `
  --camera 0 `
  --driver-id driver_001 `
  --se-endpoint http://127.0.0.1:8000/api/v1/alerts `
  --output-csv AI\artifacts\predictions\T01-Sample-live.csv `
  --events AI\artifacts\decision_events\T01-Sample-live.events.jsonl
```

Màn hình AI phải cho thấy hai road cam BTC, webcam, TTC, driver state và score.
Khi temporal rule đủ điều kiện, AI ghi DecisionEvent vào JSONL và POST ngay sang
Backend.

## 6. Cách chứng minh cùng một event đi hết chuỗi

Khi event xuất hiện:

1. AI log/JSONL: ghi lại `event_id`, `alert_type`, `status`, `frame_id`.
2. Backend recent API: event có cùng các giá trị trên.
3. Dashboard live panel: hiện cùng loại alert, lifecycle, trip và frame.
4. CarSky Signal Watch: `AlertReasonCode`, `DisplaySeverity`,
   `RecommendedActionCode`, `EventTransition` đổi tương ứng.
5. Android HMI: đổi cảnh báo/hành động theo các signal đó.

Các mapping chính:

| AI alert | CarSky action |
|---|---|
| `collision_risk` | `BRAKE_SAFE` |
| `microsleep`, `driver_drowsiness` | `TAKE_BREAK` |
| `driver_distraction` | `FOCUS_FORWARD` |
| `speeding` | `REDUCE_SPEED` |
| `system_health` | `CHECK_CAMERA` |

`open/update/resolved` lần lượt map thành `START/UPDATE/END`. Backend chỉ dịch
vocabulary, không sửa quyết định AI.

## 7. Kịch bản trình bày 7–10 phút

1. **45 giây:** nêu bài toán và hai đầu nhận cảnh báo: Fleet Manager và Driver.
2. **2 phút:** show cửa sổ AI; giải thích BTC road/telemetry + webcam thật.
3. **1 phút:** show DecisionEvent và `/alerts/recent`.
4. **1 phút:** show Dashboard panel live nhận đúng event.
5. **2 phút:** show Signal Watch và Android HMI đổi theo event.
6. **1 phút:** nêu KPI thật, hạn chế C3 saturation và latency CPU.
7. **phần còn lại:** câu hỏi/backup.

Câu chốt nên dùng:

> AI xử lý tại edge và chỉ phát canonical safety event. Backend không sửa quyết
> định mà phân phối cùng event đó đến trung tâm vận hành và màn hình trong xe.

## 8. Nhánh riêng: inference + evaluate 6 practice trips

Chạy từ `HACKATHON`:

```powershell
conda activate automotive
python AI\scripts\run_inference.py `
  --data-dir E:\automotive_cc\Practice_Dataset `
  --samples-only `
  --out AI\artifacts\predictions_6_samples `
  --log-level INFO
```

Sau khi inference hoàn tất mới evaluate:

```powershell
python AI\team_kit\evaluation.py `
  --predictions AI\artifacts\predictions_6_samples `
  --data-dir E:\automotive_cc\Practice_Dataset `
  --output AI\artifacts\evaluation_6_samples.json
```

Tham số đúng là `--output`, không phải `--output-json`. Không chạy Frontend,
Backend hoặc CarSky cho nhánh này.

## 9. Backup không giả kết quả

### Backup A — replay event AI đã sinh

Nếu webcam hoặc inference live bị chậm nhưng đã có JSONL từ rehearsal:

```powershell
python AI\scripts\send_decision_events.py `
  --events AI\artifacts\decision_events\T01-Sample-live.events.jsonl `
  --endpoint http://127.0.0.1:8000/api/v1/alerts
```

Đây là replay canonical event do AI đã sinh, phải nói rõ là replay; không gọi
là realtime inference.

### Backup B — CarSky scenario preflight

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\BE
.\.venv\Scripts\Activate.ps1
python scripts\carsky_phase05.py scenario warning
python scripts\carsky_phase05.py scenario critical
```

Hai lệnh này chỉ chứng minh CarSky/HMI transport, không chứng minh AI end-to-end.

### Evidence cần chuẩn bị

- video một lần chạy xuyên suốt;
- `*.events.jsonl` từ chính AI;
- ảnh `/alerts/recent`, Dashboard live, Signal Watch và HMI;
- evaluation JSON của 6 practice trips;
- không lưu secret trong ảnh hoặc commit.

## 10. Troubleshooting

| Hiện tượng | Cách xử lý |
|---|---|
| `No such file ... AI/scripts` | Đang đứng ở Git root: đường dẫn phải bắt đầu bằng `HACKATHON\AI`; hoặc `cd HACKATHON` rồi dùng `AI\...` |
| Profile schema 2, expected 3 | Enrollment lại bằng `--enroll` để tạo schema v3 |
| `ModuleNotFoundError: onnxruntime` | Activate conda `automotive`, cài `AI\requirements.txt` |
| Backend connection refused | Chạy Backend trước; kiểm tra `/health` |
| Dashboard `DISCONNECTED` | Kiểm tra Backend, `VITE_ALERTS_WS_URL`, rồi reload Vite |
| Dashboard không đổi fleet map | Đúng hiện trạng: map nền mock; theo dõi panel Decision Engine live |
| Backend nhận event nhưng HMI không đổi | Kiểm tra `CARSKY_ENABLED`, mode external, room/node/token và log publisher |
| Không có event ngay | Decision Engine có temporal gate; giữ hành vi đủ lâu hoặc replay JSONL rehearsal |
| C3 evaluate 100/100 | Không kết luận hoàn hảo: practice safe score prediction và GT cùng clip về 0 |

## 11. Tiêu chí pass cuối cùng

- AI chạy C1/C2/C3 và tạo ít nhất một canonical DecisionEvent.
- Backend trả `accepted=true`; gửi lại cùng idempotency key không tạo bản mới.
- Dashboard hiện `LIVE` và nhận event thật.
- Event audience `driver_display` được enqueue sang CarSky.
- Signal Watch và Android HMI đổi tương ứng.
- Team phân biệt rõ realtime, replay và mock scenario.
- Nhánh inference/evaluate sinh CSV/report độc lập và không phụ thuộc demo stack.
