# FPTU DMS Vision - Reviewer README

> Connected Car Hackathon 2026 - DMS-10 Driver Intelligence Platform  
> This README is written for BTC/judges/mentors who want to understand the project, run the system end-to-end, and evaluate it on their own dataset.
> Team Overview

| Member | Main role | Primary ownership |
|---|---|---|
| Doan Ngoc Nhan | Team Leader / Backend / CarSky Integration | Backend architecture, AI-to-Backend pipeline, API contracts, reliability evidence, CarSky signal mapping and HMI integration path |
| Phan Le Thanh Hung | AI Engineer | Challenge 2 and Challenge 3 AI/model pipeline, driver-state model work, risk/fusion logic, evaluation support |
| Duong Thi My Tam | AI Engineer | Challenge 1 model/pipeline, TTC and road-risk related AI work, AI evaluation support |
| To Dan | Business Value / Pitching / Enterprise Solution / Embedded| Business narrative, enterprise value proposition, solution positioning, final report and submission coordination |
| Nguyen Tri Thien | Frontend Engineer / Fleet Dashboard | Fleet Dashboard UI, dashboard workflows, business-facing visualization, fleet-management solution presentation |


---


## 1. Project Overview

**FPTU DMS Vision** is a driver intelligence and fleet safety platform. The system combines road perception, driver monitoring and vehicle telemetry to detect risky driving conditions and deliver them to both fleet operators and in-vehicle HMI.

The product answers one core question:

> Is this trip becoming unsafe, and what action should the driver or fleet manager take now?

The project has two output modes:

| Mode | Purpose | Output |
|---|---|---|
| BTC evaluation mode | Run model inference on BTC-style trip folders | CSV with `frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score` |
| Product demo mode | Show the full safety workflow | AI visualization, FastAPI Backend, Fleet Dashboard, AI Copilot Report, CarSky/Android HMI |

---

## 2. End-to-End Flow

```text
BTC road cameras + cabin camera + telemetry
        |
        v
AI Core
  - Challenge 1: TTC prediction
  - Challenge 2: driver state prediction
  - Challenge 3: risk/safe score
        |
        v
Decision Engine
  - quality gates
  - temporal rules
  - alert lifecycle: open/update/resolved
        |
        v
FastAPI Backend
  - /api/v1/alerts
  - /api/v1/alerts/snapshot
  - WebSocket live stream
        |
        +--> Fleet Dashboard + AI Copilot Report
        |
        +--> CarSky Signal API / KUKSA -> VHAL -> Android HMI
```

CarSky path in the current demo:

```text
Backend
  -> CarSky REST Signal API
  -> KUKSA / DMS Signal Broker
  -> Vehicle.Speed speed-mux
  -> DMS HMI Bridge
  -> VHAL PERF_VEHICLE_SPEED
  -> Android CarPropertyManager
  -> DMS Android HMI
```

Important caveat: the CarSky demo uses a verified `Vehicle.Speed speed-mux` fallback path. It does not claim production-ready custom DMS VSS properties or physical vehicle actuation.

---

## 3. AI Models and Runtime

| Module | Implementation | Main output |
|---|---|---|
| Challenge 1 - Road/TTC | Road detection/tracking, depth/TTC engine, collision-cone filtering | `predicted_ttc` |
| Challenge 2 - Driver state | Random Forest 5-class driver state model with landmark features | `predicted_driver_state` |
| Challenge 3 - Risk fusion | Formula-based causal running scorer using TTC and telemetry | `predicted_risk_score` |
| Decision Engine | Product layer after C1/C2/C3 with policy thresholds and event lifecycle | `DecisionEvent` |

Production driver-state artifact:

```text
AI/models/candidate_013.joblib
```

The model registry also points to this artifact:

```text
AI/configs/model_registry.yaml
```

Driver state classes:

```text
alert | drowsy | yawning | distracted | microsleep
```

The BTC CSV contract is defined in:

```text
AI/scripts/run_inference.py
```

The product event contract is defined in:

```text
AI/core/decision_engine/schemas.py
SE/BE/app/modules/ai_alerts/router.py
```

---

## 4. Technology Stack

| Layer | Tech |
|---|---|
| AI runtime | Python, OpenCV, PyTorch, ONNX Runtime, scikit-learn, Ultralytics, Pydantic |
| Backend | FastAPI, Uvicorn, Pydantic, REST API, WebSocket |
| Frontend | React, TypeScript, Vite, Node.js server |
| AI Copilot | AWS Bedrock-compatible server-side integration with fallback |
| Connected car | CarSky REST Signal API, KUKSA, Script Node bridge, VHAL, Android Automotive `CarPropertyManager` |
| Android HMI | Android APK artifact under `SE/HMI/release/` |
| Evidence/testing | Pytest, JUnit XML, command logs, golden payloads, screenshots, runtime traces |

---

## 5. Repository Layout

```text
HACKATHON/
├── AI/
│   ├── core/                   # C1 TTC, C2 driver state, C3 risk, Decision Engine
│   ├── configs/                # runtime configs and model registry
│   ├── models/                 # model artifacts
│   ├── scripts/                # inference/demo/evaluation scripts
│   └── team_kit/               # BTC evaluation helper
├── SE/
│   ├── BE/                     # FastAPI Backend and CarSky integration
│   ├── FE/                     # Fleet Dashboard and AI Copilot UI
│   └── HMI/                    # Android HMI/APK handoff
├── scripts/
│   └── run_product_demo.ps1    # main end-to-end product demo runner
├── reportbtc/
│   ├── C2_END_TO_END_DEMO_SCRIPT.md
│   └── README_MASTER_BTC_END_TO_END.md
└── docs/
```

Evidence is stored at repository root:

```text
evidence/
```

---

## 6. Environment Requirements

Recommended OS for the prepared demo script: **Windows PowerShell**.

Required:

- Git.
- CPython 3.13 x64.
- Node.js LTS x64, recommended Node 22+.
- npm.
- BTC Practice Dataset or another BTC-format dataset.

Optional:

- NVIDIA GPU and driver for faster inference. CPU fallback is supported but slower.
- Webcam for `hybrid-live` demo.
- CarSky API credential for full connected-car HMI demo.
- AWS Bedrock key for live AI Copilot responses.

Required AI artifacts:

```powershell
Test-Path AI\models\candidate_013.joblib
Test-Path AI\models\face_landmark_468.onnx
Test-Path AI\models\face_detection_yunet_2023mar.onnx
```

All three should return `True`. If ONNX files are not included in the Git checkout, place the released model package files into `HACKATHON/AI/models/`.

---

## 7. Setup From a Fresh Clone

From the repository root:

```powershell
cd Hackathon-Automotive-2026\HACKATHON
```

Create Python environment:

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt
```

Verify Python dependencies:

```powershell
python -c "import cv2, fastapi, httpx, onnxruntime, pydantic_settings, sklearn, torch, ultralytics, uvicorn, yaml; print('Python dependencies OK')"
python -c "import torch, onnxruntime as ort; print('Torch CUDA:', torch.cuda.is_available()); print('ORT:', ort.get_available_providers())"
```

Install frontend dependencies:

```powershell
Push-Location SE\FE
npm install
npm run build
Pop-Location
```

Create local backend env:

```powershell
if (!(Test-Path SE\BE\.env)) {
  Copy-Item SE\BE\.env.example SE\BE\.env
}
```

For local demo, keep CarSky offline and use `-SkipCarSkyPreflight`.

### 7.1. `.env.example` reference

Backend env template:

```text
SE/BE/.env.example
```

Recommended local/offline reviewer config:

```env
APP_ENV=development
API_V1_PREFIX=/api/v1
DATASET_DIR=./data
OUTPUT_SUBMISSION_DIR=./submissions
STREAM_FPS=20
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000

AI_SOURCE_MODE=file
AI_API_BASE_URL=
AI_API_PATH=/v1/analyze/trip
AI_API_KEY=
AI_API_TIMEOUT_SEC=30
AI_API_MAX_RETRIES=2
AI_API_CONCURRENCY=4
AI_FALLBACK_TO_FILE=true

LLM_PROVIDER=none
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=

CARSKY_ENABLED=false
CARSKY_MODE=offline
CARSKY_BASE_URL=
CARSKY_API_KEY=
CARSKY_AUTH_MODE=bearer
CARSKY_ROOM_ID=
CARSKY_NODE_KEY=
CARSKY_ANDROID_NODE_KEY=
CARSKY_TIMEOUT_SEC=1.5
CARSKY_MAX_RETRIES=2
CARSKY_QUEUE_SIZE=100
CARSKY_TELEMETRY_INTERVAL_SEC=1.0
```

For full CarSky demo, change only the CarSky block in `SE/BE/.env`:

```env
CARSKY_ENABLED=true
CARSKY_MODE=external
CARSKY_BASE_URL=https://<carsky-domain>
CARSKY_API_KEY=<secret>
CARSKY_AUTH_MODE=bearer
CARSKY_ROOM_ID=<room-id>
CARSKY_NODE_KEY=<signal-node-key>
CARSKY_ANDROID_NODE_KEY=<android-node-key>
CARSKY_TIMEOUT_SEC=1.5
CARSKY_MAX_RETRIES=2
CARSKY_QUEUE_SIZE=100
CARSKY_TELEMETRY_INTERVAL_SEC=1.0
```

Frontend/Copilot env template:

```text
SE/FE/.env.example
```

Create local frontend env only if BTC wants live AI Copilot/provider testing:

```powershell
if (!(Test-Path SE\FE\.env.local)) {
  Copy-Item SE\FE\.env.example SE\FE\.env.local
}
```

Example `SE/FE/.env.local`:

```env
AWS_BEARER_TOKEN_BEDROCK="bedrock-api-key-PASTE_SHORT_TERM_KEY_HERE"
AWS_DEFAULT_REGION="ap-southeast-2"
BEDROCK_MODEL_ID="deepseek.v3.2"

GEMINI_API_KEY=""
APP_URL="http://127.0.0.1:3000"

VITE_ALERTS_WS_URL="ws://127.0.0.1:8000/api/v1/alerts/live"
VITE_ROAD_FRAME_URL="http://127.0.0.1:8000/api/v1/alerts/road-frame"
VITE_CABIN_FRAME_URL="http://127.0.0.1:8000/api/v1/alerts/cabin-frame"
VITE_LIVE_SNAPSHOT_URL="http://127.0.0.1:8000/api/v1/alerts/snapshot"
```

Never commit real `CARSKY_API_KEY`, `AWS_BEARER_TOKEN_BEDROCK`, or other secrets.

---

## 8. Run the Full Product Demo

The detailed operator runbook is:

```text
reportbtc/C2_END_TO_END_DEMO_SCRIPT.md
```

### 8.1. Demo A - BTC road trip + live driver webcam

This mode replays one BTC road trip while using a live webcam for driver monitoring.

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode hybrid-live `
  -TripDir ..\Practice_Dataset\T01-Sample `
  -Camera 0 `
  -DriverId driver_001 `
  -DriverModel AI\models\candidate_013.joblib `
  -OpenDashboard `
  -SkipCarSkyPreflight
```

Expected result:

- AI visualization starts.
- Backend is available at `http://127.0.0.1:8000`.
- Fleet Dashboard opens at `http://127.0.0.1:3000`.
- Dashboard shows trip state, live metrics and alerts.

### 8.2. Demo B - Dataset fleet replay

This mode replays multiple BTC trip folders as a fleet.

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir ..\Practice_Dataset `
  -DriverModel AI\models\candidate_013.joblib `
  -OpenDashboard `
  -SkipCarSkyPreflight
```

Expected result:

- Multiple trips appear in the Fleet Dashboard.
- Trips move through `pending`, `running`, and `completed`.
- Ranking, trip detail, performance insights and reports have data.

### 8.3. Full demo with CarSky

Only use this when real CarSky credentials are configured in `SE\BE\.env`:

```env
CARSKY_ENABLED=true
CARSKY_MODE=external
CARSKY_BASE_URL=...
CARSKY_API_KEY=...
CARSKY_ROOM_ID=...
CARSKY_NODE_KEY=...
CARSKY_ANDROID_NODE_KEY=...
```

Run:

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir ..\Practice_Dataset `
  -DriverModel AI\models\candidate_013.joblib `
  -OpenDashboard `
  -RequireCarSky
```

Expected CarSky evidence:

- Deployment is running.
- Nodes are visible: `DMS Signal Broker`, `DMS HMI Bridge`, `DMS Android HMI`.
- Signal Watch shows `Vehicle.Speed` updates.
- Bridge logs show forwarding to VHAL.
- Android HMI changes SAFE/WARNING/CRITICAL state.

Do not expose API keys during recording or judging.

---

## 9. Run Inference for BTC Evaluation

Use this section if BTC wants to evaluate only the model outputs without running Backend, Dashboard or CarSky.

### 9.1. Expected dataset format

The dataset should be BTC-style, with one or more trip folders. Each trip should contain the expected metadata, road images, driver images and calibration files. Typical structure:

```text
Practice_Dataset/
├── T01-Sample/
│   ├── T01-Sample.json or T01-Sample.json.gz
│   ├── driver/
│   └── kitti/
│       ├── image_2/
│       ├── image_3/
│       └── calib/
├── T02-Sample/
└── ...
```

If your dataset path is different, replace `..\Practice_Dataset` in the commands below.

### 9.2. Run inference on BTC's dataset

For all sample trips under a dataset folder:

```powershell
python AI\scripts\run_inference.py `
  --data-dir <PATH_TO_BTC_DATASET> `
  --samples-only `
  --driver-model AI\models\candidate_013.joblib `
  --out AI\artifacts\predictions_btc_review
```

For one trip only:

```powershell
python AI\scripts\run_inference.py `
  --trip-dir <PATH_TO_BTC_DATASET>\T01-Sample `
  --driver-model AI\models\candidate_013.joblib `
  --output-csv AI\artifacts\predictions_btc_review\T01-Sample.csv
```

Output files are written under:

```text
AI/artifacts/predictions_btc_review/
```

Each output CSV follows:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

### 9.3. Run evaluation

If BTC uses the included evaluator helper:

```powershell
python AI\team_kit\evaluation.py `
  --predictions AI\artifacts\predictions_btc_review `
  --data-dir <PATH_TO_BTC_DATASET> `
  --output AI\artifacts\evaluation_btc_review.json
```

Result:

```text
AI/artifacts/evaluation_btc_review.json
```

### 9.4. Submission packaging note

For BTC-style evaluation, the primary reviewer path is the output folder from `run_inference.py`:

```text
AI/artifacts/predictions_btc_review/
```

Each trip is exported as a CSV with the required 5 columns. This is the recommended output to pass to the evaluator.

There are also Backend utility scripts under `SE/BE/scripts/`, but in this checkout they use their built-in default paths rather than command-line arguments:

```powershell
python SE\BE\scripts\export_submission_csv.py
python SE\BE\scripts\validate_submission.py
```

For reviewer evaluation on a custom dataset, use `AI/scripts/run_inference.py` + `AI/team_kit/evaluation.py` first, because those commands accept explicit dataset and output paths.

---

## 10. Run Backend and Frontend Separately

Use this if BTC wants to inspect APIs/UI without the product runner.

Backend:

```powershell
Push-Location SE\BE
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Pop-Location
```

Check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/alerts/recent
Invoke-RestMethod http://127.0.0.1:8000/api/v1/alerts/trips
```

Frontend:

```powershell
Push-Location SE\FE
npm run dev
Pop-Location
```

Open:

```text
http://127.0.0.1:3000
```

---

## 11. Run Tests

Backend tests:

```powershell
Push-Location SE\BE
..\..\.venv\Scripts\python.exe -m pytest
Pop-Location
```

Frontend lint/build:

```powershell
Push-Location SE\FE
npm run lint
npm run build
Pop-Location
```

Known evidence from the repository:

```text
evidence/E-15/derived/test_summary.json
```

This evidence records backend pytest, frontend lint/build and HMI APK artifact/static scan from the captured run.

---

## 12. CarSky Manual Check

Use this only when `SE\BE\.env` contains valid external CarSky credentials.

```powershell
.\.venv\Scripts\python.exe SE\BE\scripts\carsky_phase05.py status
.\.venv\Scripts\python.exe SE\BE\scripts\carsky_phase05.py nodes
.\.venv\Scripts\python.exe SE\BE\scripts\carsky_phase05.py scenario critical
```

Pass condition:

```text
ok=true
mode=vehicle-speed-mux
sent=14
```

What to observe in CarSky:

- Signal Watch: `Vehicle.Speed` changes.
- Bridge logs: `Vehicle.Speed` is received and forwarded.
- Android HMI: state changes to WARNING/CRITICAL.

Evidence:

```text
evidence/E-24/raw/carsky_scenario_critical_parsed.json
evidence/E-24/reports/mapping.md
evidence/E-24/raw/hmi_apk_static_scan.log
```

---

## 13. Evidence Map

| Topic | Evidence |
|---|---|
| Architecture | `evidence/E-02/`, `evidence/E-02/derived/as_is_architecture.pdf` |
| AI pipeline/model output contract | `evidence/README_AI_PIPELINE_MODEL_OUTPUT_CONTRACT.md` |
| Technical quality/execution | `evidence/README_TECHNICAL_QUALITY_EXECUTION_EVIDENCE.md` |
| API schema/golden payloads | `evidence/E-03/` |
| Decision Engine | `evidence/E-05/` |
| C2 model/dependencies | `evidence/E-08/`, `evidence/E-27/` |
| C3 formula | `evidence/E-07/` |
| Backend reliability/WebSocket | `evidence/E-14/` |
| Automated tests/build/APK | `evidence/E-15/` |
| Failure handling/fallback | `evidence/E-16/` |
| Dashboard/report UI | `evidence/E-21/`, `evidence/E-22/`, `evidence/E-23/` |
| CarSky runtime path | `evidence/E-04/`, `evidence/E-24/` |
| Reproducibility/environment | `evidence/E-26/` |

---

## 14. Known Limitations

| Area | Current limitation |
|---|---|
| Backend persistence | Recent alerts/live trips are kept in memory for demo; this is not durable production storage |
| CarSky custom VSS | Current demo uses `Vehicle.Speed speed-mux`; custom DMS VSS properties are not claimed production-ready |
| Android HMI rebuild | APK artifact/static scan is verified; a clean-room APK rebuild is not claimed from this checkout |
| AI Copilot | Bedrock is an explanation layer; local JSON/AI telemetry remains the canonical metric source |
| Intervention | The system provides warning/review workflow; it does not claim autonomous braking or physical actuation |
| C2 generalization | Evidence is provided, but subject-disjoint real-world generalization is not claimed without additional validation |

---

## 15. Troubleshooting

| Problem | Suggested fix |
|---|---|
| PowerShell blocks scripts | `Set-ExecutionPolicy -Scope Process Bypass` |
| Python dependency missing | Activate `.venv`, reinstall `AI\requirements.txt` and `SE\BE\requirements.txt` |
| Model file missing | Place released model artifacts under `AI\models\` |
| Frontend dependency missing | `Push-Location SE\FE; npm install; npm run build; Pop-Location` |
| Backend port 8000 already used | Stop the old backend process and rerun the demo |
| Dashboard unavailable | Check `http://127.0.0.1:3000/api/health` and logs under `AI\artifacts\runtime_logs` |
| CarSky preflight fails | For local demo use `-SkipCarSkyPreflight`; for full demo verify `.env` credentials |
| Android HMI does not change | Check deployment status, Signal Watch `Vehicle.Speed`, bridge logs and app state |
| Bedrock authentication fails | Verify token, region `ap-southeast-2`, model `deepseek.v3.2`, and remove whitespace/newlines |

---

## 16. Quick Start Summary

```powershell
cd Hackathon-Automotive-2026\HACKATHON
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt

Push-Location SE\FE
npm install
npm run build
Pop-Location

.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir ..\Practice_Dataset `
  -DriverModel AI\models\candidate_013.joblib `
  -OpenDashboard `
  -SkipCarSkyPreflight
```

For pure model evaluation:

```powershell
python AI\scripts\run_inference.py `
  --data-dir <PATH_TO_BTC_DATASET> `
  --samples-only `
  --driver-model AI\models\candidate_013.joblib `
  --out AI\artifacts\predictions_btc_review

python AI\team_kit\evaluation.py `
  --predictions AI\artifacts\predictions_btc_review `
  --data-dir <PATH_TO_BTC_DATASET> `
  --output AI\artifacts\evaluation_btc_review.json
```
## 17. Responsibility Boundaries

| Area | Owner | Contribution |
|---|---|---|
| Team leadership and technical coordination | Doan Ngoc Nhan | Coordinated system integration, aligned AI/Backend/Frontend/CarSky boundaries, maintained evidence-driven implementation claims |
| Backend and API contracts | Doan Ngoc Nhan | Implemented and verified FastAPI alert/snapshot boundary, `DecisionEvent` ingestion, idempotency handling, WebSocket live stream and backend reliability traces |
| AI-to-Backend pipeline | Doan Ngoc Nhan | Connected AI/Decision Engine outputs into Backend contracts so model results can be consumed by Dashboard and CarSky/HMI |
| CarSky integration | Doan Ngoc Nhan | Implemented Backend-to-CarSky signal publishing, CarSky/KUKSA mapping, speed-mux fallback path and Android HMI integration evidence |
| Challenge 2 driver-state model | Phan Le Thanh Hung | Built and supported the driver-state model pipeline for `alert`, `drowsy`, `yawning`, `distracted`, `microsleep` predictions |
| Challenge 3 risk/fusion logic | Phan Le Thanh Hung | Worked on risk-score/fusion logic and model-output alignment for the final AI pipeline |
| Challenge 1 TTC/road-risk model | Duong Thi My Tam | Worked on TTC/road-risk model pipeline and Challenge 1 evaluation support |
| Business value and pitching | To Dan | Developed business value story, customer-facing positioning, enterprise solution angle, pitch/report narrative and submission readiness |
| Fleet Dashboard frontend | Nguyen Tri Thien | Built dashboard workflows for fleet monitoring, trip detail, driver ranking, ranking analysis, insights and reports |
| Enterprise solution display | Nguyen Tri Thien | Designed how AI safety outputs are presented to fleet managers as actionable business views |

