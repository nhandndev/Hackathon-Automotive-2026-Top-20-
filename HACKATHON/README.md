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


---

## 15. Báo Cáo Nghiệm Thu Chi Tiết Chỉ Số Production & Reliability (Evidence)

Dưới đây là báo cáo bằng chứng kỹ thuật (evidence) đầy đủ và chi tiết nhất về các thay đổi mã nguồn nhằm tích hợp môi trường Production (14.3), cải tiến độ tin cậy (12.2) và tiêu chuẩn chạy thực tế trên thiết bị Edge (DoD):

### 15.1 Chỉ Số Hiệu Năng Thực Tế Của AI Copilot (Phần 14.3)
*Các thông số dưới đây được ghi nhận qua kết nối AWS Bedrock Converse API với mô hình `deepseek.v3.2` tại vùng `ap-southeast-2` (Đơn giá: Input $0.0008 / 1k tokens | Output $0.0016 / 1k tokens):*

| Loại Yêu Cầu (Request Type) | Số Lượng Token Vào (Input) | Số Lượng Token Ra (Output) | Latency p50 | Latency p95 | Chi Phí Thực Tế (Cost) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Quick Chat Query** | **17 tokens** | **42 tokens** | **2,414 ms** | **3,024 ms** | **~$0.00008** |
| **Single Driver Report** | **65 tokens** | **163 tokens** | **6,068 ms** | **7,344 ms** | **~$0.00031** |
| **Fleet Maintenance Report** | **159 tokens** | **292 tokens** | **7,141 ms** | **14,552 ms** | **~$0.00059** |

---

### 15.2 Chi Tiết Triển Khai Kỹ Thuật (Bằng Chứng FE/server.ts)

Để đạt được các tiêu chuẩn kiểm thử của môi trường Production, chúng tôi đã chỉnh sửa mã nguồn file [server.ts](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/server.ts) như sau:

#### A. 30s Timeout Guardrail (Chống treo request vô hạn)
Tích hợp `AbortController` vào cuộc gọi `fetch()` gọi tới AWS Bedrock, tự động ngắt kết nối sau **30 giây**:
```typescript
// Định nghĩa trong hàm callBedrockConverse
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000);

const response = await fetch(endpoint, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": `Bearer ${token}`,
  },
  body: JSON.stringify({
    messages: [{ role: "user", content: [{ text: prompt }] }],
  }),
  signal: controller.signal, // Nhúng tín hiệu hủy request
});
clearTimeout(timeoutId);
```

#### B. Trích Xuất Dữ Liệu Token Tiêu Thụ Thật (Token Usage Parsing)
```typescript
const payload = await response.json().catch(() => ({}));
const text = payload?.output?.message?.content?.[0]?.text || "";

// Trích xuất số lượng token thật từ đối tượng usage của Bedrock
const inputTokens = payload?.usage?.inputTokens || 0;
const outputTokens = payload?.usage?.outputTokens || 0;
```

#### C. Phân Quyền Endpoint AI (Access Control)
Đăng ký middleware `verifyCopilotAuth` trên cả hai endpoint `/api/copilot` và `/api/copilot/report` để chặn các request không có Bearer Token hợp lệ:
```typescript
const verifyCopilotAuth = (req: express.Request, res: express.Response, next: express.NextFunction) => {
  const token = req.headers["authorization"];
  const expectedToken = process.env.COPILOT_API_TOKEN;
  
  if (expectedToken) {
    if (!token || token !== `Bearer ${expectedToken}`) {
      res.status(401).json({ error: "Unauthorized: Invalid COPILOT_API_TOKEN" });
      return;
    }
  }
  next();
};
```

#### D. Ghi Nhật Ký & Tự Động Dọn Dẹp (Request Logging & 90-Day Data Retention)
Lưu trữ nhật ký vào file cấu trúc JSON `copilot_audit_logs.json` ở root thư mục Frontend, tự động áp dụng bộ lọc thời gian để xóa log cũ quá **90 ngày**:
```typescript
function logCopilotRequest(type: string, inputTokens: number, outputTokens: number, latencyMs: number) {
  try {
    const logPath = path.join(process.cwd(), "copilot_audit_logs.json");
    let logs: any[] = [];
    if (fs.existsSync(logPath)) {
      const content = fs.readFileSync(logPath, "utf-8");
      logs = JSON.parse(content || "[]");
    }
    
    const now = new Date();
    logs.push({ timestamp: now.toISOString(), type, inputTokens, outputTokens, latencyMs });
    
    // Xóa log cũ quá 90 ngày (Retention Policy)
    const ninetyDaysAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
    logs = logs.filter(log => new Date(log.timestamp) > ninetyDaysAgo);
    
    fs.writeFileSync(logPath, JSON.stringify(logs, null, 2), "utf-8");
  } catch (err) {
    console.error("Failed to write audit log:", err);
  }
}
```

#### E. Ẩn Danh Hóa Thông Tin Lái Xe (PII Redaction)
Mã hóa driver profile thật thành định danh pseudonyms dạng `driver_<trip_id>` trước khi gửi dữ liệu lên internet cho nhà cung cấp LLM:
```typescript
const buildTripContext = (vehicles: TripSummary[]) => {
  return JSON.stringify(
    vehicles.map((vehicle) => {
      const tripIdSafe = vehicle.trip_id.toLowerCase().replace(/[^a-z0-9]/g, "_");
      const redactedMetadata = vehicle.metadata ? {
        ...vehicle.metadata,
        driver_profile: `driver_${tripIdSafe}`
      } : undefined;

      return {
        trip_id: vehicle.trip_id,
        metadata: redactedMetadata,
        driver_summary: vehicle.driver_summary ? {
          ...(vehicle.driver_summary as any),
          subject_id: `driver_${tripIdSafe}`
        } : undefined,
        trip_aggregate: vehicle.trip_aggregate,
      };
    }),
    null, 2
  );
};
```

---

### 15.3 Chỉ Số Tin Cậy Hệ Thống (Phần 12.2 Reliability Backlog)

| Hạng mục | Hiện trạng kỹ thuật | Tiêu chí nghiệm thu (Acceptance Criteria) |
| :--- | :--- | :--- |
| **Persistent Outbox** | RAM/cache; chưa chứng minh qua restart | **0% mất mát sự kiện** khi máy chủ restart đột ngột hoặc mất kết nối mạng liên tục trong **24 giờ** (kiểm thử thành công với ít nhất **50+ lần restart** liên tục). |
| **Delivery Status** | Chưa khóa đầy đủ | Quản lý trạng thái truyền phát rõ ràng: `Sent/Acked/Failed/Retry` kèm theo thông tin `timestamp` và `reason` (lý do lỗi) chi tiết cho mỗi sự kiện, tự động retry **tối đa 5 lần** với exponential backoff. |
| **Latency** | Chưa có p95 end-to-end chính thức | Độ trễ truyền dẫn từ AI Decision Engine đến Fleet Dashboard Consumer: **p50 < 100ms**, **p95 < 350ms**, **p99 < 800ms** trên môi trường máy demo chạy carla/live. |
| **Backpressure** | Chưa công bố | Hàng đợi (Queue depth) tối đa **10.000 sự kiện**, áp dụng chính sách **Drop Oldest** khi tràn hàng đợi, thời gian phục hồi hệ thống hoàn toàn sau nghẽn mạng **< 5 giây**. |
| **Schema Evolution** | Có contract nhưng cần versioning policy | Đảm bảo tương thích ngược ít nhất **3 phiên bản gần nhất** (Backward compatibility) kèm theo kiểm thử tự động và tài liệu ghi chú chuyển đổi dữ liệu (Migration Note). |
| **Observability** | Log hiện có | Tích hợp mã định danh tương quan (**Correlation ID**) xuyên suốt từ AI Engine đến UI, cấu trúc log dạng JSON, đo đạc metrics trung gian, và ping kiểm tra sức khỏe Dashboard (Healthcheck) định kỳ mỗi **5 giây**. |

* **Bằng chứng phân tích mã nguồn gốc tại Backend (BE/router.py):**
  - **RAM Outbox:** Tại file [router.py:L90-95](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app/modules/ai_alerts/router.py#L90-L95), dữ liệu hiện tại chỉ lưu tạm trên RAM với `deque(maxlen=1000)`. Do đó, nếu tiến trình bị kill/restart, toàn bộ cảnh báo sẽ biến mất hoàn toàn. Tiêu chí Persistent Outbox đề xuất thay đổi sang bảng lưu trữ DB trước khi Go-live.
  - **Delivery Status:** Dẫn chứng tại file [router.py:L131-158](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app/modules/ai_alerts/router.py#L131-L158) chỉ kiểm tra tính trùng lặp `idempotency_key` tĩnh trên RAM, không quản lý các trạng thái ACK/nACK hay theo dõi lịch trình retry giữa AI Engine và Consumer Dashboard.

---

### 15.4 Tiêu Chí Nghiệm Thu Thiết Bị Edge/Demo (DoD)
* **Definition of Done (DoD):** Hệ thống đạt tiêu chuẩn hoàn thành nghiệm thu phần cứng khi chạy ổn định liên tục tối thiểu **60 phút** trên thiết bị Edge/Demo đảm bảo: **FPS >= 10**, **độ trễ xử lý p95 < 120ms**, **tỷ lệ CPU/GPU/RAM < 85%**, và **nhiệt độ SoC < 80°C** không bị sụt giảm hiệu năng (thermal throttling).
* **Bằng chứng khả thi:**
  - Endpoint đo FPS thực tế `/health` của dịch vụ backend tại file [main.py:L169-175](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app/main.py#L169-L175).
  - Giả lập giả tải liên tiếp bằng script điều phối kịch bản `run_product_demo.ps1`.

---

### 15.5 Lộ Trình Triển Khai Thực Tế & Tối Ưu Hóa Hệ Thống (Production Roadmap)

Nhóm phát triển đề xuất lộ trình tối ưu và triển khai thực tế (hardening) hệ thống lên môi trường sản xuất theo các mục tiêu hành động sau:

#### 1. Persistent Outbox, Session & Audit
* **Mục tiêu:** Đảm bảo hệ thống phục hồi và không mất mát dữ liệu khi mất điện hoặc mất mạng cục bộ.
* **Chi tiết kỹ thuật:**
  - Chuyển đổi bộ nhớ đệm RAM `deque` hiện tại sang bảng lưu trữ vật lý trong Database (PostgreSQL/SQLite) áp dụng mô hình Transactional Outbox Pattern.
  - Xây dựng cơ chế khôi phục phiên (Session recovery) cho phép tự động đồng bộ lại các cảnh báo nhỡ (delivery status) từ hàng đợi khi kết nối mạng được tái thiết lập.
  - Triển khai kịch bản chạy thử nghiệm phát lại tự động (Replay test) để chứng minh tính toàn vẹn dữ liệu qua tối thiểu 50 lần ngắt kết nối vật lý ngẫu nhiên.

#### 2. Chỉ Số KPI Chi Tiết (Granular Performance Metrics)
* **Mục tiêu:** Đo lường chính xác năng lực cốt lõi của động cơ AI nhận diện hành vi.
* **Chi tiết kỹ thuật:**
  - Thiết lập ma trận đánh giá hiệu quả nhận diện phân loại tài xế (Per-class Precision, Recall, và False Alarm Rate - FAR) đối với từng trạng thái vi phạm (Drowsy, Yawn, Distracted).
  - Giám sát độ trễ xử lý sự kiện (Event processing latency) từ khi camera ghi nhận frame đến khi phát thành công tín hiệu cảnh báo ra cổng giao tiếp.
  - Xây dựng hệ thống tự động từ chối sự kiện trùng lặp (Duplicate rejection rate) dựa trên cơ chế `idempotency_key` đã lập trình.

#### 3. Chính Sách Truyền Thông & Bảo Mật Quyền Riêng Tư (Media & Privacy Policy)
* **Mục tiêu:** Tuân thủ pháp lý về việc thu thập hình ảnh và bảo vệ thông tin cá nhân.
* **Chi tiết kỹ thuật:**
  - Tích hợp biểu mẫu chấp thuận (User Consent) hiển thị trên màn hình HMI khi bắt đầu hành trình.
  - Thiết lập chính sách lưu trữ video và hình ảnh cabin (Retention Policy) tự động xóa sạch dữ liệu ghi hình thô sau 24 giờ và chỉ giữ lại dữ liệu sự kiện rủi ro ẩn danh hóa.
  - Kiểm soát quyền truy cập hình ảnh (Access Control) chặt chẽ bằng giao thức Token hóa và dán nhãn dữ liệu thử nghiệm (Demo data labeling) rõ ràng để tránh rò rỉ dữ liệu vận hành thật của tài xế.

#### 4. Hardening AI Copilot & Báo Cáo
* **Mục tiêu:** Đảm bảo chất lượng nội dung báo cáo AI sản sinh và quản lý chi phí vận hành.
* **Chi tiết kỹ thuật:**
  - Xây dựng tập dữ liệu đối chiếu chuẩn (Golden-set) để thực hiện kiểm toán độ chính xác thông tin (Factual audit) định kỳ, giảm thiểu tỷ lệ ảo giác của LLM.
  - Thiết lập ngưỡng kiểm soát tài chính tự động (Cost/Latency limits) dựa trên lượng token thực bóc tách qua `payload?.usage`.
  - Tối ưu luồng fallback tự động sang mô hình cục bộ hoặc rule-based khi Bedrock mất mạng và tích hợp phân quyền truy cập báo cáo theo vai trò (Role-Based Access Control - RBAC).

#### 5. Thử Nghiệm Thực Tế (Field Pilot)
* **Mục tiêu:** Đánh giá độ hiệu quả thực tế và tỷ lệ thu hồi vốn (ROI) đối với doanh nghiệp vận tải.
* **Chi tiết kỹ thuật:**
  - Khởi động giai đoạn chạy thử nghiệm bóng (Shadow Pilot) - hệ thống ghi nhận sự kiện ngầm nhưng chưa can thiệp cảnh báo trực tiếp để lấy dữ liệu baseline.
  - Chuyển dịch sang thử nghiệm hỗ trợ (Assisted Pilot) để cảnh báo chủ động và đo lường trực tiếp các chỉ số kinh doanh như: tỷ lệ giảm số vụ va chạm, số lần tài xế ngủ gật, giảm hao mòn phụ tùng và tỷ lệ chấp thuận của kiểm duyệt viên.

#### 6. Tối Ưu Hóa Phần Cứng (Hardware Optimization)
* **Mục tiêu:** Đảm bảo toàn bộ luồng xử lý chạy mượt mà, ổn định trên thiết bị nhúng phần cứng Edge mục tiêu.
* **Chi tiết kỹ thuật:**
  - Tối ưu hóa runtime để hệ thống chạy ổn định 24/7 trên bộ kít phát triển **Jetson Orin Nano 8GB Developer Kit**.
  - Cấu hình biên dịch mô hình AI (như YOLOv8/RF) sang định dạng **TensorRT** để tối ưu hóa hiệu năng suy luận (Inference optimization) và giảm lượng điện năng tiêu thụ.
  - Tài liệu hóa toàn bộ môi trường triển khai phần cứng nhúng và quy trình cài đặt chuẩn (Reproducible setup guide) để đội ngũ kỹ thuật dễ dàng tái tạo.



