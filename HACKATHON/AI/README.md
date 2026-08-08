# FPTU DMS Vision - AI Runtime

`AI/` is the official inference runtime for the product demo and BTC output.
It keeps only production code, config, trained model artifacts, lightweight
validation tools, and one reusable Challenge 2 training script.

## Runtime Flow

```text
BTC left/right road cameras -> Challenge 1 TTC
BTC or webcam cabin camera  -> Challenge 2 driver state
Telemetry + TTC             -> Challenge 3 risk/safe score
Challenge 1/2/3 outputs     -> Decision Engine -> SE Backend -> Dashboard/CarSky
```

BTC CSV output:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Driver states:

```text
alert | drowsy | yawning | distracted | microsleep
```

## Folder Layout

```text
AI/
  configs/                  Runtime configs and model registry
  core/
    challenge1_road/         Road detection, depth and TTC
    challenge2_driver/       Driver landmarks, features, RF inference, profile
    challenge3_fusion/       BTC safe/risk score formula
    decision_engine/         Alert policy and event lifecycle
    runtime/                 Shared demo/runtime helpers
  integrations/              SE client
  models/                    Production model artifacts only
  scripts/
    run_inference.py         Batch BTC inference
    webcam_driver_demo.py    Challenge 2 webcam demo/enrollment
    trip_visual_demo.py      Dataset visual demo helper
    end_to_end_demo.py       BTC road + live driver webcam demo
    dataset_fleet_demo.py    Sequential multi-trip dashboard demo
    preflight_ai.py          Environment/model sanity check
    inspect_driver_model.py  Model metadata inspection
    train_driver_state_hierarchical.py
  team_kit/                  BTC evaluation helper copied for local scoring
  artifacts/                 Generated outputs, ignored by git
```

## Production Models

Challenge 2 does not hard-code a `.joblib` path in the entrypoints. If
`--driver-model` or `--model` is omitted, all runtime scripts resolve:

```text
AI/configs/model_registry.yaml -> challenge2.production.artifact
```

Current production artifact:

```text
AI/models/driver_state_current.joblib
```

This is the current 84-feature `architect_v2` Random Forest artifact used by
the main AI pipeline. It combines the legacy 59 driver-state features with 25
compatibility hand-proxy features.

For demos and handoff, pass the model path explicitly so every machine runs the
same Random Forest artifact:

```text
AI\models\driver_state_current.joblib
```

## Setup

Run from `HACKATHON/`:

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r AI\requirements.txt
python -m pip install -r SE\BE\requirements.txt
python AI\scripts\preflight_ai.py
```

CUDA is expected for the full product demo. Random Forest itself runs on CPU,
while YOLO/ONNX parts use GPU providers when available.

## Batch Inference

Six BTC practice trips:

```powershell
python AI\scripts\run_inference.py `
  --data-dir ..\Practice_Dataset `
  --samples-only `
  --driver-model AI\models\driver_state_current.joblib `
  --out AI\artifacts\predictions_6_samples `
  --log-level INFO
```

Single trip:

```powershell
python AI\scripts\run_inference.py `
  --trip-dir ..\Practice_Dataset\T01-Sample `
  --driver-model AI\models\driver_state_current.joblib `
  --output-csv AI\artifacts\predictions\T01-Sample.csv `
  --log-level INFO
```

Override Challenge 2 model only when testing a compatible artifact:

```powershell
python AI\scripts\run_inference.py `
  --data-dir ..\Practice_Dataset `
  --samples-only `
  --driver-model AI\models\driver_state_current.joblib `
  --out AI\artifacts\predictions_test_model
```

## Evaluate

```powershell
python AI\team_kit\evaluation.py `
  --predictions AI\artifacts\predictions_6_samples `
  --data-dir ..\Practice_Dataset `
  --output AI\artifacts\predictions_6_samples\evaluation.json
```

## Challenge 2 Webcam

Create or refresh a non-biometric driver profile:

```powershell
python AI\scripts\webcam_driver_demo.py `
  --camera 0 `
  --driver-id driver_001 `
  --enroll `
  --model AI\models\driver_state_current.joblib
```

Run personalized:

```powershell
python AI\scripts\webcam_driver_demo.py `
  --camera 0 `
  --driver-id driver_001 `
  --model AI\models\driver_state_current.joblib
```

Run global:

```powershell
python AI\scripts\webcam_driver_demo.py `
  --camera 0 `
  --model AI\models\driver_state_current.joblib
```

## End-to-End Demo

BTC road cameras + live webcam driver camera:

```powershell
.\scripts\run_product_demo.ps1 `
  -TripDir ..\Practice_Dataset\T01-Sample `
  -Camera 0 `
  -DriverId driver_001 `
  -DriverModel AI\models\driver_state_current.joblib `
  -OpenDashboard
```

Dataset fleet demo:

```powershell
.\scripts\run_product_demo.ps1 `
  -Mode dataset-fleet `
  -DataDir ..\Practice_Dataset `
  -DriverModel AI\models\driver_state_current.joblib `
  -OpenDashboard
```

Keep this runner terminal open while inspecting Fleet Dashboard. When the
runner exits, it stops the local SE Backend, and the browser will show
`ERR_CONNECTION_REFUSED` for `127.0.0.1:8000`.

## Training Challenge 2

Keep training outside production outputs. The reusable training script is:

```text
AI/scripts/train_driver_state_hierarchical.py
```

Example:

```powershell
python AI\scripts\train_driver_state_hierarchical.py `
  --dataset-dir ..\experiment\dataset-v2 `
  --output-dir ..\experiment\training_outputs\new_driver_state_model `
  --n-iterations 50 `
  --feature-workers 2 `
  --require-cuda
```

After training, inspect the candidate:

```powershell
python AI\scripts\inspect_driver_model.py `
  --model ..\experiment\training_outputs\new_driver_state_model\best\best_model.joblib
```

Only copy/promote a model into `AI/models/` after the feature schema,
landmark backend, labels and metrics are verified.

## Production Rules

- Do not commit datasets, predictions, driver profiles, webcam data or secrets.
- Do not keep experimental `.joblib` files in `AI/models/`.
- Do not hard-code dataset paths in scripts or README commands.
- Do not let Backend recompute AI risk/severity; AI sends canonical events.
- Reset temporal state between trips.
