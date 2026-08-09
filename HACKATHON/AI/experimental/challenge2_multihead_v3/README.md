# Challenge 2 Experimental Multi-Head V3

This folder is a new experimental rail for Challenge 2. It does not replace the
stable AI pipeline yet.

## Why this exists

The current production Challenge 2 flow uses a single Random Forest model. This
experiment splits driver-state detection into smaller heads:

- `microsleep`: rule-based eye closure duration
- `yawning`: rule-based mouth-open duration
- `distracted`: rule-based head/hand attention evidence
- `drowsy`: optional binary Random Forest over temporal eye features
- `alert`: fallback when no risk head is active

Then a fusion engine applies:

- quality gates
- hysteresis
- priority: microsleep → yawning/distracted → drowsy → alert
- conflict resolution between yawning and distracted

## Protected legacy pipeline

Do not edit the stable pipeline while working here. See:

```text
AI/LEGACY_PIPELINE_PROTECTED.md
```

Rollback model:

```text
AI/models/candidate_013.joblib
```

## Files in this experiment

```text
multihead_driver_state_v3.py   Core engine: personalization, temporal features, heads, fusion
multihead_config.yaml          Thresholds and profile defaults
demo_multihead_v3_smoke.py     Small synthetic smoke test, no training
train_drowsy_head_rf.py        Train optional binary RF for Drowsy Head
infer_multihead_v3.py          BTC-style inference using the experimental multi-head engine
_trip_adapter.py               Trip reader + legacy extractor adapter, read-only import
```

## Smoke test only

Run from `HACKATHON`:

```powershell
python AI\experimental\challenge2_multihead_v3\demo_multihead_v3_smoke.py --max-frames 80
```

This only verifies the new state machine. It does not train any model and does
not modify the production demo/inference flow.

Optional binary drowsy model:

```powershell
python AI\experimental\challenge2_multihead_v3\demo_multihead_v3_smoke.py `
  --drowsy-model AI\experimental\challenge2_multihead_v3\models\drowsy_head_rf.joblib `
  --max-frames 80
```

If no drowsy model is provided, the Drowsy head is disabled instead of faking a
probability.

## Train Drowsy Head RF

Drowsy Head is trained as a separate binary model:

```text
drowsy -> 1
alert / yawning / distracted / microsleep -> 0
```

The model uses only these temporal features:

```text
PERCLOS_5s
blink_duration_mean_5s
eye_openness_mean_5s
eye_openness_std_5s
blink_rate_10s
long_closure_count_10s
```

Short safety test first:

```powershell
python AI\experimental\challenge2_multihead_v3\train_drowsy_head_rf.py `
  --dataset-dir ..\Practice_Dataset `
  --samples-only `
  --max-trips 2 `
  --max-frames-per-trip 5 `
  --n-iter 0 `
  --output AI\experimental\challenge2_multihead_v3\artifacts\smoke_models\drowsy_head_rf_smoke.joblib `
  --report AI\experimental\challenge2_multihead_v3\artifacts\smoke_models\drowsy_head_rf_smoke_report.json `
  --verbose
```

Full training when ready:

```powershell
python AI\experimental\challenge2_multihead_v3\train_drowsy_head_rf.py `
  --dataset-dir ..\experiment\dataset-v2 `
  --output AI\experimental\challenge2_multihead_v3\models\drowsy_head_rf.joblib `
  --report AI\experimental\challenge2_multihead_v3\models\drowsy_head_rf_report.json `
  --n-iter 12 `
  --cv 3 `
  --verbose
```

If `--dataset-dir` contains `train/valid`, the script automatically trains on
`train` and reports holdout metrics on `valid`. Frames with missing/unsupported
driver labels are skipped.

This does not modify `AI/models/candidate_013.joblib`.

## Experimental inference

Single trip:

```powershell
python AI\experimental\challenge2_multihead_v3\infer_multihead_v3.py `
  --trip-dir ..\Practice_Dataset\T01-Sample `
  --drowsy-model AI\experimental\challenge2_multihead_v3\models\drowsy_head_rf.joblib `
  --out AI\experimental\challenge2_multihead_v3\artifacts\predictions_multihead_v3 `
  --debug-dir AI\experimental\challenge2_multihead_v3\artifacts\debug_heads
```

All sample trips:

```powershell
python AI\experimental\challenge2_multihead_v3\infer_multihead_v3.py `
  --data-dir ..\Practice_Dataset `
  --samples-only `
  --drowsy-model AI\experimental\challenge2_multihead_v3\models\drowsy_head_rf.joblib `
  --out AI\experimental\challenge2_multihead_v3\artifacts\predictions_multihead_v3 `
  --debug-dir AI\experimental\challenge2_multihead_v3\artifacts\debug_heads
```

Output CSV keeps the BTC-compatible columns:

```text
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

## Promotion rule

Only promote this into `AI/core/challenge2_driver` after:

1. Smoke tests pass.
2. We train/evaluate the binary drowsy RF separately.
3. We compare Challenge 2 metrics against the protected candidate model.
4. The user explicitly agrees to replace the production flow.
