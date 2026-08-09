# FPTU DMS Vision — README tổng quát dự án & hướng dẫn test cho BTC

> Tài liệu này dành cho Ban Tổ chức/mentor đọc nhanh để hiểu giải pháp, phạm vi đã triển khai, cách chạy kiểm thử và các điểm còn cần hỗ trợ.  
> Repository: `Hackathon-Automotive-2026/HACKATHON`  
> Team: **FPTU DMS Vision**  
> Chủ đề: **DMS-10 — Driver Intelligence Platform**

---

## 1. Tóm tắt giải pháp

**FPTU DMS Vision** là nền tảng giám sát an toàn tài xế và đội xe, kết hợp:

- **Road camera** để ước lượng nguy cơ va chạm và TTC.
- **Driver/cabin camera** để nhận diện trạng thái tài xế.
- **Telemetry** để hiểu tốc độ, gia tốc, hành vi phanh/góc cua/bám đuôi.
- **Risk Fusion** để hợp nhất các tín hiệu thành điểm rủi ro 0–100.
- **Backend/Fleet Dashboard** để xem live trip, cảnh báo, ranking tài xế và báo cáo.
- **Fleet AI Copilot** để giải thích dữ liệu fleet bằng AI thật qua AWS Bedrock.
- **CarSky HMI** để hiển thị cảnh báo tài xế trong môi trường xe/Android HMI.

Thông điệp chính của giải pháp:

> Tai nạn không bắt đầu bằng một cảnh báo đơn lẻ, mà bằng nhiều tín hiệu nguy hiểm bị nhìn riêng rẽ. DMS Vision hợp nhất driver state, road risk và telemetry thành một quyết định có thể hành động.

---

## 2. Phạm vi bài toán và output

Dự án xử lý 3 challenge chính:

| Challenge | Mục tiêu | Output chính |
|---|---|---|
| Challenge 1 — Collision Risk / TTC | Ước lượng Time-to-Collision từ road camera/telemetry | `predicted_ttc` |
| Challenge 2 — Driver Intelligence | Phân loại trạng thái tài xế | `predicted_driver_state` |
| Challenge 3 — Risk Fusion | Hợp nhất TTC, driver state và behavior thành điểm rủi ro | `predicted_risk_score` |

Submission CSV mục tiêu:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Ngoài submission, nhóm xây thêm product demo end-to-end:

```text
AI → Backend → Fleet Dashboard → AI Copilot → CarSky HMI
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

Nguyên tắc thiết kế:

- AI là nguồn sinh kết quả risk/TTC/driver state.
- Backend validate, cache, aggregate và phát event; không tự ghi đè `risk.final_risk_score`.
- Dashboard dùng data thật từ Backend hoặc dataset local đang có.
- Không tự tạo thêm trip giả trong FE khi bàn giao cho máy có full dataset.
- CarSky dùng để chứng minh luồng cảnh báo tới HMI/driver display.

---

## 4. Cấu trúc repository

```text
HACKATHON/
├── AI/                         # AI core, challenge inference, evaluation
│   ├── core/                   # TTC, driver state, fusion/risk
│   ├── models/                 # Model artifacts, report
│   ├── scripts/                # Inference/demo/evaluation scripts
│   └── team_kit/               # BTC/team evaluation loader
├── SE/
│   ├── BE/                     # FastAPI Backend
│   │   ├── app/                # API, schemas, services, adapters
│   │   ├── scripts/            # Export, CarSky, validation scripts
│   │   └── docs/               # Phase docs, CarSky docs, runbook
│   ├── FE/                     # Fleet Dashboard + AI Copilot UI
│   │   ├── src/                # React UI
│   │   ├── server.ts           # FE server + Copilot gateway
│   │   └── docs/               # AI Copilot memory/docs
│   └── HMI/                    # Android HMI/APK handoff
├── docs/                       # Research, starter kit notes, architecture
├── reportbtc/                  # C2/BTC reports and demo scripts
└── scripts/                    # Product demo runner
```

---

## 5. Thành phần đã triển khai

### 5.1 AI Core

Đã có:

- Script inference/evaluation cho challenge.
- Driver state pipeline và model report.
- TTC/risk fusion script.
- Product demo script kết nối AI → SE.
- Webcam driver demo cho luồng live camera.

File tiêu biểu:

- `AI/scripts/run_inference.py`
- `AI/scripts/end_to_end_demo.py`
- `AI/scripts/dataset_fleet_demo.py`
- `AI/scripts/webcam_driver_demo.py`
- `AI/team_kit/evaluation.py`
- `AI/models/driver_state_rf_v3_onnx_test_report.json`

### 5.2 Backend

Đã có:

- FastAPI Backend.
- Health endpoint.
- AI contract/schema.
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

### 5.3 Fleet Dashboard

Đã có:

- Dashboard hiển thị trạng thái fleet/trip.
- Driver Ranking.
- Trip Detail.
- Alerts.
- Messages/Copilot UI.
- Report page mở tab mới.
- AI Copilot gọi AI thật qua AWS Bedrock ở server-side.

File tiêu biểu:

- `SE/FE/src/App.tsx`
- `SE/FE/src/components/AICopilotDrawer.tsx`
- `SE/FE/src/components/CopilotFleetReportPage.tsx`
- `SE/FE/src/components/DriverRankingView.tsx`
- `SE/FE/server.ts`

### 5.4 Fleet AI Copilot

Đã có:

- Server-side `/api/copilot`.
- Server-side `/api/copilot/report`.
- AWS Bedrock Bearer Token support.
- Model mặc định: `deepseek.v3.2`.
- Region mặc định theo BTC: `ap-southeast-2`.
- Có fallback/provider error rõ ràng nếu token hết hạn hoặc cấu hình sai.

Biến môi trường cần có trong `SE/FE/.env.local`:

```env
AWS_BEARER_TOKEN_BEDROCK=bedrock-api-key-...
AWS_DEFAULT_REGION=ap-southeast-2
BEDROCK_MODEL_ID=deepseek.v3.2
```

Không commit token thật lên repository.

### 5.5 CarSky / Android HMI

Đã có:

- CarSky Blueprint deploy được với 3 nodes ready trong cấu hình đã fix:
  - DMS Signal Broker
  - DMS HMI Bridge
  - DMS Android HMI
- KUKSA custom signals hiển thị được trong Signal Watch.
- Backend/script gửi scenario critical/safe lên CarSky được.
- Android HMI APK có UI cảnh báo an toàn/cảnh báo/critical.

Các bài học kỹ thuật quan trọng:

- `dms-vss-signals.json` phải là object/map `{...}`, không phải array `[...]`.
- Nếu KUKSA Broker báo `ParseError("invalid type: sequence, expected a map")`, nguyên nhân là artifact VSS sai format.
- Android CarProperty chỉ nhận những VHAL property được register trong car service; custom VSS cần bridge phù hợp.

Docs liên quan:

- `SE/BE/docs/CARSKY_BROKER_FIX_GUIDE.md`
- `SE/BE/docs/CARSKY_KUKSA_RUNTIME_INCIDENT.md`
- `SE/BE/docs/AI_REALTIME_TO_CARSKY_HMI_MEMORY.md`
- `SE/BE/docs/CARSKY_ECU_INTERACTION_MEMORY.md`

---

## 6. KPI và số liệu hiện tại

| Nhóm KPI | Kết quả hiện tại | Ghi chú |
|---|---:|---|
| Challenge 1 — TTC | Composite khoảng **65.5/100**, danger F1 retest khoảng **69.9%** | Cần đồng bộ artifact retest cuối vào repo trước final |
| Challenge 2 — Driver State | Practice composite retest khoảng **87.2/100** | Cần giữ evaluation log/checksum |
| Driver state augmented holdout | Accuracy **78.47%**, macro-F1 **80.28%** | Không trộn với hidden/BTC practice score |
| Challenge 3 — Risk Fusion | Evaluator practice **100/100** | Không kết luận hoàn hảo tuyệt đối vì có hiện tượng clip safe score |
| Backend tests | Đã từng pass 13/13 ở Phase 01; cần rerun trước nộp final | Tùy môi trường dataset |
| Frontend build | `npm run build` pass | Có warning bundle size, không phải lỗi runtime |
| CarSky deploy | Đã có deployment running 3/3 nodes trong cấu hình fixed VSS | HMI realtime còn phụ thuộc VHAL bridge/runtime |
| Bedrock Copilot | Key/model/region test pass với `deepseek.v3.2`, `ap-southeast-2` | Short-term key có hạn dùng |

---

## 7. Chuẩn bị môi trường test

### 7.1 Yêu cầu phần mềm

- Python 3.11+ hoặc Python 3.13 tùy máy demo.
- Node.js LTS.
- npm.
- Git.
- Dataset BTC/practice nếu muốn chạy full trip thật.
- Webcam nếu test driver camera live.
- CarSky account/token nếu test HMI.
- AWS Bedrock short-term API key nếu test AI Copilot thật.

### 7.2 Tạo Python virtual environment

Từ root repo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI/requirements.txt
python -m pip install -r SE/BE/requirements.txt
```

Nếu dùng Windows PowerShell:

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt
```

### 7.3 Cài Frontend

```bash
cd SE/FE
npm install
npm run build
cd ../..
```

---

## 8. Cấu hình `.env`

### 8.1 Backend

Tạo file:

```bash
cp SE/BE/.env.example SE/BE/.env
```

Các biến thường dùng:

```env
APP_ENV=development
API_V1_PREFIX=/api/v1
DATASET_DIR=./data
OUTPUT_SUBMISSION_DIR=./submissions
STREAM_FPS=20
AI_SOURCE_MODE=file
CARSKY_ENABLED=false
```

Nếu test CarSky thật thì điền thêm credential vào `SE/BE/.env`.

### 8.2 Frontend / AI Copilot

Tạo file:

```bash
cp SE/FE/.env.example SE/FE/.env.local
```

Điền Bedrock:

```env
AWS_BEARER_TOKEN_BEDROCK=bedrock-api-key-...
AWS_DEFAULT_REGION=ap-southeast-2
BEDROCK_MODEL_ID=deepseek.v3.2
```

Lưu ý:

- `AWS_BEARER_TOKEN_BEDROCK` là short-term key, có thể hết hạn sau vài giờ.
- Không đưa `.env.local` lên GitHub hoặc vào báo cáo PDF.
- Nếu lỗi `Authentication failed`, kiểm tra token còn hạn, region và whitespace/newline.

---

## 9. Cách chạy test từng tầng

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

Chạy test Backend:

```bash
cd SE/BE
source .venv/bin/activate
pytest
```

### 9.2 Test Frontend/Fleet Dashboard

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
- Menu trái không bị double-active sai.
- Driver Ranking hiển thị đúng số trip có trong data/backend.
- AI Copilot Drawer mở được.
- Nếu chưa có nhiều trip thật, Copilot phải hỏi lại `trip_id` thay vì tự tạo trip giả.

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

client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-2"))
response = client.converse(
    modelId=os.environ.get("BEDROCK_MODEL_ID", "deepseek.v3.2"),
    messages=[{"role": "user", "content": [{"text": "Xin chào, trả lời đúng một câu tiếng Việt."}]}],
)
print(response["output"]["message"]["content"][0]["text"])
PY
```

Kỳ vọng:

- Bedrock trả một câu tiếng Việt.
- Nếu lỗi `Unable to locate credentials`, cần dùng đúng biến `AWS_BEARER_TOKEN_BEDROCK`.
- Nếu lỗi `AccessDeniedException`, kiểm tra key/region/model.

### 9.4 Test AI inference / submission

Ví dụ chạy inference theo dataset:

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

Trên Windows PowerShell, từ root `HACKATHON`:

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode hybrid-live `
  -TripDir <PATH_TO_PRACTICE_DATASET>\T01-Sample `
  -Camera 0 `
  -DriverId driver_001 `
  -DriverModel AI\models\driver_state_current.joblib `
  -OpenDashboard `
  -SkipCarSkyPreflight
```

Chế độ nhiều trip:

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir <PATH_TO_PRACTICE_DATASET> `
  -DriverModel AI\models\driver_state_current.joblib `
  -OpenDashboard `
  -SkipCarSkyPreflight
```

Bỏ `-SkipCarSkyPreflight` chỉ khi `SE\BE\.env` đã có CarSky external
credential thật (`CARSKY_ENABLED=true`, `CARSKY_MODE=external`, token/room/node
đầy đủ).

Kỳ vọng end-to-end:

1. AI sinh TTC, driver state và risk.
2. Backend nhận event.
3. Dashboard cập nhật trip/alert.
4. AI Copilot tạo insight/report khi có Bedrock key.
5. CarSky Signal Watch/HMI đổi trạng thái nếu CarSky external đang enabled và deployment running.

### 9.6 Test CarSky signal/HMI

Từ `SE/BE`:

```bash
cd SE/BE
source .venv/bin/activate
python scripts/carsky_phase05.py status
python scripts/carsky_phase05.py nodes
python scripts/carsky_phase05.py scenario critical
```

Kỳ vọng:

- `status` trả `RUNNING`.
- Signal Watch thấy các signal như:
  - `Vehicle.Speed`
  - `Vehicle.ADAS.FinalRiskScore`
  - `Vehicle.Driver.State`
  - `Vehicle.ADAS.DisplaySeverity`
  - `Vehicle.ADAS.AIStatus`
- HMI đổi từ safe/warning/critical theo signal.

---

## 10. Test nhanh trước khi gửi BTC

Chạy checklist ngắn:

```bash
# Backend
cd SE/BE
source .venv/bin/activate
pytest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal khác:

```bash
curl http://127.0.0.1:8000/health
```

Frontend:

```bash
cd SE/FE
npm run lint
npm run build
npm run dev
```

AI Copilot:

```text
Mở http://127.0.0.1:3000
Vào Fleet AI Copilot
Hỏi: "Báo cáo an toàn fleet"
```

CarSky:

```bash
cd SE/BE
python scripts/carsky_phase05.py scenario critical
```

---

## 11. Các lỗi thường gặp và cách xử lý

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

## 12. Những phần còn đang phát triển / cần hỗ trợ

| Hạng mục | Trạng thái | Cần hỗ trợ/việc còn lại |
|---|---|---|
| Full dataset trên mọi máy | Một số máy local chưa có full dataset | Máy chấm/demo nên có dataset đầy đủ để FE không cần fallback local |
| CarSky HMI realtime | Đã deploy và gửi signal được; VHAL/APK realtime cần xác minh từng deployment | BTC hỗ trợ runtime/log nếu VHAL transport lỗi |
| TTS trên Android HMI | UI có nút voice; AAOS có thể thiếu TTS engine | BTC xác nhận có hỗ trợ TTS/audio route không |
| Persistent offline outbox | Có queue/runtime MVP | Cần persistent storage qua restart |
| Final evaluation artifact | Có số liệu preview/retest | Cần đồng bộ artifact cuối, command, checksum |
| Latency chính thức | Có benchmark thành phần | Cần đo p95 end-to-end trên máy demo cuối |

---

## 13. Tiêu chí nghiệm thu demo

Một buổi demo được xem là đạt nếu chứng minh được:

1. AI chạy từ input thật hoặc dataset BTC thật.
2. Có output TTC, driver state và risk score.
3. Backend nhận và phát event đúng contract.
4. Dashboard hiển thị trip/event/ranking/report.
5. AI Copilot gọi Bedrock thật, không dùng response mock cho phần insight.
6. CarSky Signal Watch nhận signal từ Backend/script.
7. Nếu HMI/VHAL bị lỗi nền tảng, nhóm có log, nguyên nhân và fallback minh bạch.

---

## 14. Link tài liệu liên quan

- `README.md` — Project constitution cho AI/SE.
- `reportbtc/C2_PROGRESS_REPORT_FPTU_DMS_VISION.md` — Báo cáo tiến độ C2.
- `reportbtc/C2_END_TO_END_DEMO_SCRIPT.md` — Kịch bản demo end-to-end.
- `reportbtc/readmeproposal.md` — Proposal gốc.
- `SE/BE/docs/README.md` — Backend docs.
- `SE/BE/docs/phases/` — Backend phase plan.
- `SE/FE/README.md` — Frontend/Fleet Dashboard.
- `SE/FE/docs/AI_COPILOT_FUNCTION_CALLING_REPORTS.md` — Memory AI Copilot.
- `AI/README.md` — AI workspace.
- `reportbtc/C2_END_TO_END_DEMO_SCRIPT.md` — Setup `.venv` và runbook demo.

---

## 15. Ghi chú bảo mật khi gửi BTC

- Không đưa `.env`, `.env.local`, API key, CarSky token, AWS Bedrock token vào PDF/public repo.
- Có thể ghi rõ “BTC-provided short-term key configured locally”.
- Nếu cần BTC reproduce, gửi hướng dẫn biến môi trường, không gửi token trong README public.

