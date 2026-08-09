# AI Legacy Pipeline Protected Manifest

This file marks the current stable AI pipeline that must stay untouched while
Challenge 2 multi-head fusion is developed in parallel.

## Stable Challenge 2 rollback point

Use this if the experimental flow fails:

```powershell
python AI\scripts\run_inference.py `
  --data-dir ..\Practice_Dataset `
  --samples-only `
  --driver-model AI\models\candidate_013.joblib `
  --out AI\artifacts\predictions_6_samples
```

```powershell
python AI\team_kit\evaluation.py `
  --predictions AI\artifacts\predictions_6_samples `
  --data-dir ..\Practice_Dataset `
  --output AI\artifacts\evaluation_6_samples.json
```

## Protected files / folders

Do not edit these while developing the experimental Challenge 2 architecture:

- `AI\models\candidate_013.joblib`
- `AI\models\driver_state_current.joblib`
- `AI\configs\challenge2.yaml`
- `AI\core\challenge2_driver\dms_core.py`
- `AI\core\challenge2_driver\predict_state.py`
- `AI\core\challenge2_driver\ml_features.py`
- `AI\core\challenge2_driver\driver_profile.py`
- `AI\core\challenge2_driver\face_landmarker.py`
- `AI\core\challenge2_driver\hand_landmarker.py`
- `AI\scripts\run_inference.py`
- `AI\scripts\webcam_driver_demo.py`
- `AI\scripts\end_to_end_demo.py`
- `AI\scripts\dataset_fleet_demo.py`
- `AI\core\runtime\demo_engine.py`
- `AI\team_kit\evaluation.py`

## Experimental rail

New work for the multi-head architecture lives here:

- `AI\experimental\challenge2_multihead_v3\`

The experimental rail may import stable code for reading/extraction later, but
it must not modify stable code until we explicitly decide to promote it.
