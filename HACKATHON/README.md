# FPTU DMS Vision — Driver Intelligence & Fleet Safety Platform

> **Connected Car Hackathon 2026 — DMS-10 Driver Intelligence Platform**  
> README này là trang tổng quan chính ở root repository để Ban Tổ chức/mentor mở GitHub là hiểu ngay dự án làm gì, đã hoàn thành gì và test như thế nào.

---

## 1. Dự án giải quyết bài toán gì?

Tai nạn giao thông thường không bắt đầu từ một cảnh báo đơn lẻ, mà từ nhiều tín hiệu nguy hiểm xuất hiện cùng lúc nhưng bị nhìn rời rạc:

- Tài xế mất tập trung, buồn ngủ hoặc microsleep.
- Khoảng cách với xe/vật thể phía trước giảm nhanh.
- TTC thấp, headway thấp, tốc độ cao.
- Phanh gấp, tăng tốc gắt, cua gắt, tailgating.

**FPTU DMS Vision** hợp nhất các tín hiệu từ **road camera**, **driver camera** và **telemetry** để tạo:

- Collision risk / TTC.
- Driver state.
- Unified risk score.
- Fleet Dashboard cho quản lý đội xe.
- AI Copilot giải thích rủi ro và tạo báo cáo.
- CarSky/Android HMI cảnh báo trực tiếp cho tài xế.

Mục tiêu không chỉ là “phát hiện sự kiện”, mà là **hiểu rủi ro và đưa ra hành động kịp thời**.

---

## 2. Ba challenge chính

| Challenge | Mục tiêu | Output |
|---|---|---|
| Challenge 1 — Collision Risk / TTC | Ước lượng Time-to-Collision từ road camera/telemetry | `predicted_ttc` |
| Challenge 2 — Driver Intelligence | Phân loại trạng thái tài xế | `predicted_driver_state` |
| Challenge 3 — Risk Fusion | Hợp nhất TTC, driver state và behavior thành điểm rủi ro | `predicted_risk_score` |

Submission CSV mục tiêu:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

---

## 3. Kiến trúc end-to-end

```text
BTC Dataset / Road Camera / Driver Camera / Telemetry
                         │
                         ▼
              AI Core / Decision Engine
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
 Challenge 1 TTC   Challenge 2 DMS   Challenge 3 Risk
       └─────────────────┼─────────────────┘
                         ▼
                 DecisionEvent / AITrip
                         │
                         ▼
                    FastAPI Backend
       ┌─────────────────┼────────────────────────┐
       ▼                 ▼                        ▼
 REST APIs         WebSocket realtime        CarSky Adapter
       │                 │                        │
       ▼                 ▼                        ▼
 Fleet Dashboard   Live event stream       KUKSA/VHAL/HMI
       │
       ▼
 Fleet AI Copilot qua AWS Bedrock
```

Nguyên tắc tích hợp:

- AI là nguồn sinh TTC, driver state và risk.
- Backend validate, cache, aggregate và phát event; không tự ghi đè risk output của AI.
- Dashboard dùng data thật từ Backend/dataset; không tự tạo trip giả khi bàn giao.
- CarSky dùng để chứng minh luồng cảnh báo tới HMI/driver display.

---

## 4. Cấu trúc repository

```text
HACKATHON/
├── AI/                         # AI core, challenge inference, evaluation
│   ├── core/                   # TTC, driver state, fusion/risk
│   ├── models/                 # Model artifacts/report
│   ├── scripts/                # Inference, demo, evaluation scripts
│   └── team_kit/               # BTC/team evaluation loader
├── SE/
│   ├── BE/                     # FastAPI Backend
│   │   ├── app/                # API, schemas, services, adapters
│   │   ├── scripts/            # Export, validation, CarSky scripts
│   │   └── docs/               # Phase docs, CarSky docs, runbook
│   ├── FE/                     # Fleet Dashboard + AI Copilot UI
│   │   ├── src/                # React UI
│   │   ├── server.ts           # FE server + Copilot gateway
│   │   └── docs/               # AI Copilot docs/memory
│   └── HMI/                    # Android HMI/APK handoff
├── docs/                       # Research, starter-kit notes, architecture
├── reportbtc/                  # C2/BTC reports and demo scripts
└── scripts/                    # Product demo runner
```

---

## 5. Thành phần đã triển khai

### AI

- Challenge inference/evaluation scripts.
- TTC / Driver State / Risk Fusion pipeline.
- Product demo script nối AI → Backend.
- Webcam driver demo cho luồng live camera.
- Evaluation artifacts cho driver state và practice testing.

File tiêu biểu:

- `AI/scripts/run_inference.py`
- `AI/scripts/end_to_end_demo.py`
- `AI/scripts/dataset_fleet_demo.py`
- `AI/scripts/webcam_driver_demo.py`
- `AI/team_kit/evaluation.py`

### Backend

- FastAPI Backend.
- Health/readiness.
- AI contract/schema validation.
- REST APIs cho trip/alert/fleet.
- WebSocket realtime.
- CarSky integration script.
- Submission/export validation utilities.

File tiêu biểu:

- `SE/BE/app/main.py`
- `SE/BE/app/domain/schemas/ai_contract.py`
- `SE/BE/scripts/export_submission_csv.py`
- `SE/BE/scripts/validate_submission.py`
- `SE/BE/scripts/carsky_phase05.py`

### Fleet Dashboard

- Dashboard hiển thị trạng thái fleet/trip.
- Driver Ranking.
- Trip Detail.
- Alerts.
- Messages / Fleet AI Copilot UI.
- Report page mở tab mới.
- AI Copilot gọi AI thật qua AWS Bedrock ở server-side.

File tiêu biểu:

- `SE/FE/src/App.tsx`
- `SE/FE/src/components/AICopilotDrawer.tsx`
- `SE/FE/src/components/CopilotFleetReportPage.tsx`
- `SE/FE/src/components/DriverRankingView.tsx`
- `SE/FE/server.ts`

### Fleet AI Copilot

- Endpoint `/api/copilot`.
- Endpoint `/api/copilot/report`.
- AWS Bedrock Bearer Token support.
- Model mặc định: `deepseek.v3.2`.
- Region theo BTC: `ap-southeast-2`.

Biến môi trường cần có trong `SE/FE/.env.local`:

```env
AWS_BEARER_TOKEN_BEDROCK=bedrock-api-key-...
AWS_DEFAULT_REGION=ap-southeast-2
BEDROCK_MODEL_ID=deepseek.v3.2
```

Không commit token thật lên repository.

### CarSky / Android HMI

- Đã triển khai CarSky Blueprint với các node:
  - DMS Signal Broker
  - DMS HMI Bridge
  - DMS Android HMI
- KUKSA custom signals hiển thị được trong Signal Watch.
- Script gửi scenario safe/warning/critical lên CarSky.
- Android HMI APK có UI cảnh báo an toàn/cảnh báo/nguy hiểm.

Các bài học kỹ thuật quan trọng:

- VSS artifact cho KUKSA phải là object/map `{...}`, không phải array `[...]`.
- Nếu gặp `ParseError("invalid type: sequence, expected a map")`, nguyên nhân là file VSS sai format.
- Android CarProperty/VHAL cần property được register đúng trong car service.

---

## 6. KPI và số liệu hiện tại

| Nhóm KPI | Kết quả hiện tại | Ghi chú |
|---|---:|---|
| Challenge 1 — TTC | Composite khoảng **65.5/100**, danger F1 retest khoảng **69.9%** | Cần đồng bộ artifact retest cuối vào repo trước final |
| Challenge 2 — Driver State | Practice composite retest khoảng **87.2/100** | Cần giữ evaluation log/checksum |
| Driver state augmented holdout | Accuracy **78.47%**, macro-F1 **80.28%** | Không trộn với hidden/BTC practice score |
| Challenge 3 — Risk Fusion | Evaluator practice **100/100** | Không kết luận hoàn hảo tuyệt đối vì có hiện tượng clip safe score |
| Backend tests | Đã từng pass 13/13 ở Phase 01; cần rerun trước final | Tùy môi trường dataset |
| Frontend build | `npm run build` pass | Có warning bundle size, không phải lỗi runtime |
| CarSky deploy | Đã có deployment running 3/3 nodes trong cấu hình fixed VSS | HMI realtime còn phụ thuộc VHAL bridge/runtime |
| Bedrock Copilot | Key/model/region test pass với `deepseek.v3.2`, `ap-southeast-2` | Short-term key có hạn dùng |

---

## 7. Setup môi trường

### 7.1 Yêu cầu

- Python 3.11+ hoặc Python 3.13.
- Node.js LTS.
- npm.
- Git.
- Dataset BTC/practice nếu chạy full trip thật.
- Webcam nếu chạy driver camera live.
- CarSky credential nếu test HMI.
- AWS Bedrock short-term key nếu test AI Copilot thật.

### 7.2 Python virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI/requirements.txt
python -m pip install -r SE/BE/requirements.txt
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt
```

### 7.3 Frontend dependencies

```bash
cd SE/FE
npm install
npm run build
cd ../..
```

---

## 8. Cấu hình `.env`

### Backend

```bash
cp SE/BE/.env.example SE/BE/.env
```

Các biến chính:

```env
APP_ENV=development
API_V1_PREFIX=/api/v1
DATASET_DIR=./data
OUTPUT_SUBMISSION_DIR=./submissions
STREAM_FPS=20
AI_SOURCE_MODE=file
CARSKY_ENABLED=false
```

Nếu test CarSky thật, điền credential CarSky vào `SE/BE/.env`.

### Frontend / Bedrock Copilot

```bash
cp SE/FE/.env.example SE/FE/.env.local
```

```env
AWS_BEARER_TOKEN_BEDROCK=bedrock-api-key-...
AWS_DEFAULT_REGION=ap-southeast-2
BEDROCK_MODEL_ID=deepseek.v3.2
```

Lưu ý:

- Bedrock key là short-term key, có thể hết hạn.
- Không đưa `.env`, `.env.local`, API key hoặc token lên GitHub/public report.

---

## 9. Cách test

### 9.1 Test Backend

```bash
cd SE/BE
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal khác:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

Kỳ vọng `/health`:

```json
{
  "status": "ok",
  "service": "dms-backend",
  "version": "1.0.0",
  "stream_fps": 20.0
}
```

Chạy test:

```bash
cd SE/BE
source .venv/bin/activate
pytest
```

### 9.2 Test Fleet Dashboard

```bash
cd SE/FE
npm run lint
npm run build
npm run dev
```

Mở:

```text
http://127.0.0.1:3000
```

Kỳ vọng:

- Dashboard mở được.
- Driver Ranking hiển thị theo trip/data đang có.
- Trip Detail/Alerts/Messages hoạt động.
- AI Copilot Drawer mở được.

### 9.3 Test AWS Bedrock Copilot

Từ `SE/FE`, sau khi điền `.env.local`:

```bash
python3 - <<'PY'
import os
from pathlib import Path
for line in Path(".env.local").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")

import boto3
os.environ["AWS_BEARER_TOKEN_BEDROCK"] = (
    os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "")
    .replace("\n", "")
    .replace(" ", "")
    .strip()
)

client = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-2"),
)
response = client.converse(
    modelId=os.environ.get("BEDROCK_MODEL_ID", "deepseek.v3.2"),
    messages=[{"role": "user", "content": [{"text": "Xin chào, trả lời đúng một câu tiếng Việt."}]}],
)
print(response["output"]["message"]["content"][0]["text"])
PY
```

Kỳ vọng:

- Bedrock trả lời bằng tiếng Việt.
- Nếu lỗi `Authentication failed`, kiểm tra key còn hạn, region và model.

### 9.4 Test AI inference / submission

```bash
python AI/scripts/run_inference.py \
  --data-dir <PATH_TO_PRACTICE_DATASET> \
  --samples-only \
  --out AI/artifacts/predictions_6_samples
```

Đánh giá:

```bash
python AI/team_kit/evaluation.py \
  --predictions AI/artifacts/predictions_6_samples \
  --data-dir <PATH_TO_PRACTICE_DATASET> \
  --output AI/artifacts/evaluation_6_samples.json
```

### 9.5 Test product demo end-to-end

Windows PowerShell từ root `HACKATHON`:

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode hybrid-live `
  -TripDir <PATH_TO_PRACTICE_DATASET>\T01-Sample `
  -Camera 0 `
  -DriverId driver_001 `
  -OpenDashboard
```

Chế độ nhiều trip:

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir <PATH_TO_PRACTICE_DATASET> `
  -OpenDashboard
```

Kỳ vọng:

1. AI sinh TTC, driver state và risk.
2. Backend nhận event.
3. Dashboard cập nhật trip/alert.
4. AI Copilot tạo insight/report khi có Bedrock key.
5. CarSky Signal Watch/HMI đổi trạng thái nếu CarSky external đang enabled và deployment running.

### 9.6 Test CarSky

```bash
cd SE/BE
source .venv/bin/activate
python scripts/carsky_phase05.py status
python scripts/carsky_phase05.py nodes
python scripts/carsky_phase05.py scenario critical
```

Kỳ vọng:

- Deployment status là `RUNNING`.
- Signal Watch thấy các signal:
  - `Vehicle.Speed`
  - `Vehicle.ADAS.FinalRiskScore`
  - `Vehicle.Driver.State`
  - `Vehicle.ADAS.DisplaySeverity`
  - `Vehicle.ADAS.AIStatus`
- HMI đổi trạng thái safe/warning/critical theo signal.

---

## 10. Lỗi thường gặp

| Lỗi | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `Port 3000 is already in use` | FE server cũ còn chạy | Kill process port 3000/23000 rồi chạy lại `npm run dev` |
| `Port 8000 is already in use` | Backend cũ còn chạy | Kill process port 8000 rồi chạy lại uvicorn |
| Backend `/ready` trả 503 | Dataset/cache chưa đủ hoặc external config thiếu | Kiểm tra `DATASET_DIR`, trip cache, CarSky/AI mode |
| Bedrock `Authentication failed` | Key hết hạn/sai region/copy dính whitespace | Tạo key mới, dùng `ap-southeast-2`, strip newline |
| Bedrock `Unable to locate credentials` | SDK chưa nhận Bearer Token | Dùng biến `AWS_BEARER_TOKEN_BEDROCK` |
| CarSky KUKSA `invalid type: sequence, expected a map` | VSS artifact là array `[...]` | Upload VSS dạng object/map `{...}` |
| CarSky deployment pending lâu | Node/artifact/runtime chưa apply xong hoặc hạ tầng đang lỗi | Xem Dashboard/Logs, gửi BTC nếu stuck > 5–10 phút |
| Android HMI không nghe voice | AAOS image thiếu TTS engine/default synth | Cần TTS engine APK hoặc xác nhận audio route từ BTC |
| HMI không update nhưng Signal Watch có data | Android CarProperty/VHAL bridge chưa map đúng property | Kiểm tra HMI Bridge log và registered VHAL property |

---

## 11. Những phần còn đang phát triển / cần hỗ trợ

| Hạng mục | Trạng thái | Cần hỗ trợ/việc còn lại |
|---|---|---|
| Full dataset trên mọi máy | Một số máy local chưa có full dataset | Máy chấm/demo nên có dataset đầy đủ |
| CarSky HMI realtime | Đã deploy và gửi signal được; VHAL/APK realtime cần xác minh từng deployment | BTC hỗ trợ runtime/log nếu VHAL transport lỗi |
| TTS trên Android HMI | UI có nút voice; AAOS có thể thiếu TTS engine | BTC xác nhận có hỗ trợ TTS/audio route không |
| Persistent offline outbox | Có queue/runtime MVP | Cần persistent storage qua restart |
| Final evaluation artifact | Có số liệu preview/retest | Cần đồng bộ artifact cuối, command, checksum |
| Latency chính thức | Có benchmark thành phần | Cần đo p95 end-to-end trên máy demo cuối |

---

## 12. Tiêu chí nghiệm thu demo

Một buổi demo được xem là đạt nếu chứng minh được:

1. AI chạy từ input thật hoặc dataset BTC thật.
2. Có output TTC, driver state và risk score.
3. Backend nhận và phát event đúng contract.
4. Dashboard hiển thị trip/event/ranking/report.
5. AI Copilot gọi Bedrock thật, không dùng response mock cho phần insight.
6. CarSky Signal Watch nhận signal từ Backend/script.
7. Nếu HMI/VHAL bị lỗi nền tảng, nhóm có log, nguyên nhân và fallback minh bạch.

---

## 13. Tài liệu chi tiết

- `reportbtc/README_TONG_QUAT_DU_AN_VA_HUONG_DAN_TEST.md` — bản báo cáo/test guide chi tiết cho BTC.
- `reportbtc/C2_PROGRESS_REPORT_FPTU_DMS_VISION.md` — báo cáo tiến độ C2.
- `reportbtc/C2_END_TO_END_DEMO_SCRIPT.md` — kịch bản demo end-to-end.
- `reportbtc/readmeproposal.md` — proposal gốc.
- `SE/BE/docs/README.md` — Backend docs.
- `SE/BE/docs/phases/` — Backend phase plan.
- `SE/FE/README.md` — Frontend/Fleet Dashboard.
- `SE/FE/docs/AI_COPILOT_FUNCTION_CALLING_REPORTS.md` — AI Copilot memory.
- `AI/README.md` — AI workspace.
- `reportbtc/C2_END_TO_END_DEMO_SCRIPT.md` — setup `.venv` và runbook demo.

---

## 14. Ghi chú bảo mật

- Không đưa `.env`, `.env.local`, API key, CarSky token, AWS Bedrock token vào PDF/public repo.
- Có thể ghi trong báo cáo: “BTC-provided short-term key configured locally”.
- Nếu BTC cần reproduce, gửi hướng dẫn biến môi trường, không gửi token trong README public.

