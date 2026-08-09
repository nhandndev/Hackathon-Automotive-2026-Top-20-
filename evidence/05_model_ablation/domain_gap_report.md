# E-42: Model drift / domain gap — Challenge 1 (Road/TTC)

**Owner:** Tâm/Hùng
**Scope:** `HACKATHON/AI` Challenge 1 YOLO detector + TTC pipeline only.

## Data provenance

Both sources are **fully synthetic CARLA simulation output** — no real
people, no PII, no consent requirement:

| Source | Trips | CARLA version | Role |
|---|---|---|---|
| `Practice_Dataset/` | 6 | 0.9.15 (UE4) | Organizer-provided, matches the real BTC-scored trip domain |
| `extra_trips/` | 1 (`T01-Sample-leadbrake`) | 0.9.15 (UE4) | Team-collected, same engine/domain as above |
| `Data_train/` | 50 | 0.10.0 (UE5) | Organizer-provided supplementary training pool |

`Data_train/` was present on disk when the experiments below ran
(2026-08-08/09) but was not present when this report and
`psi_ks_metrics.csv` were finalized — see **Note on data availability**
below for how the drift metrics were still computed.

## Why this matters: three regressions traced to this exact gap

The production model (`yolov8s_finetuned_carla_v2.pt`, composite 73.6
in-sample / 72.4 LOTO) was fine-tuned only on the CARLA 0.9.15 sources.
Three separate attempts to additionally train on `Data_train` were tried
and validated against the same 6 Practice trips:

| Version | Strategy | Composite | vs v2 |
|---|---|---|---|
| v2 (production) | fine-tune on Practice+extra only | **73.6** | baseline |
| v3 | from-scratch on raw 57-trip mix (87% Data_train frames) | 68.2 | regressed |
| v4 | continue-from-v2, LR=0.0002, raw mix | 66.3 | regressed (worse than v3) |
| v5 | continue-from-v2, LR=0.0005, **domain-rebalanced ~50/50** | 68.9 | regressed (best of the 3, still below v2) |

Rebalancing epoch exposure (v5) recovered some of the gap versus the raw
87/13 mix (v3/v4) but did not close it, meaning volume skew alone does not
explain the regression.

### Root-caused mechanism (v5, trip T01)

`Data_train`'s KITTI labels include `Van`/`Truck` classes that
`Practice_Dataset`/`extra_trips` essentially don't exercise. v3/v4/v5 all
mapped `Van→car`, `Truck→truck` when building the YOLO dataset
(`scripts/prepare_yolo_finetune.py`), so those weights learned to detect
trucks/vans that v2 had never been trained to recognize.

Direct trace on T01 frame ~135-140: a parked delivery truck at the frame
edge, correctly detected by v5 (conf 0.89, a real object v2 is blind to).
But `RoadTTCPredictor`'s collision-cone + SGBM-depth logic — tuned only
against `car`/`pedestrian`/`cyclist` since v1/v2 — misjudged the
stationary off-path truck as an imminent collision:

```
frame=134 gt_min_ttc=inf  pred_ttc=2.500
frame=135 gt_min_ttc=inf  pred_ttc=0.339   <- false danger alarm
frame=136 gt_min_ttc=inf  pred_ttc=0.393   <- false danger alarm
frame=137 gt_min_ttc=inf  pred_ttc=0.402   <- false danger alarm
```

Ground truth is `inf` (safe) at every one of these frames. This is a false
positive that specifically hurts the F1(danger<2s) term of the composite
score. **More correct detections regressed the score because the TTC
engine's collision-cone/depth logic was never validated against
object classes beyond car/pedestrian/cyclist** — not because the detector
itself got worse.

**v6** (in progress at time of writing) reverts the label mapping to only
`Car`/`Pedestrian`/`Cyclist` (matching v1/v2) while keeping v5's 50/50
domain rebalancing, to isolate whether Data_train's scenery/lighting
diversity helps once the class mismatch is removed. Results pending —
see `configs/challenge1.yaml` (currently pinned to v2) for the adopted
weight at any given time.

## Quantified domain shift

See `psi_ks_metrics.csv` in this folder for PSI (Population Stability
Index) and two-sample KS-test results comparing `practice`
(Practice_Dataset + extra_trips) vs `data_train`, on three features:

- `mean_luminance` — per-frame grayscale mean (lighting/time-of-day shift)
- `boxes_per_frame` — object count per labeled frame (scene density)
- `box_height_norm` — YOLO-normalized box height across all boxes (object
  scale/depth distribution)

PSI interpretation (standard convention, no CARLA-specific baseline
exists): <0.1 no significant shift, 0.1–0.25 moderate, >0.25 major.

### Results (2026-08-09 run, see `psi_ks_metrics.csv`)

| Feature | practice mean±std | data_train mean±std | PSI | KS stat | KS p-value |
|---|---|---|---|---|---|
| mean_luminance | 80.0 ± 50.4 | 51.0 ± 17.8 | **8.56** | 0.58 | ~4e-63 |
| boxes_per_frame | 1.34 ± 0.74 | 3.66 ± 2.22 | **1.82** | 0.62 | ~0 |
| box_height_norm | 0.116 ± 0.101 | 0.067 ± 0.091 | **0.83** | 0.33 | ~0 |

All three features land far past the "major shift" PSI threshold
(>0.25) and are statistically significant at any reasonable alpha. In
plain terms:

- **Lighting**: `data_train` frames average ~36% darker (51.0 vs 80.0
  mean grayscale), consistent with more scenes shot at dusk/night —
  matches the visual side-by-side done during triage (a `data_train`
  twilight residential scene vs a `practice` bright-daylight downtown
  scene).
- **Scene density**: `data_train` frames carry ~2.7x more labeled objects
  per frame (3.66 vs 1.34) — busier scenes with more
  cars/pedestrians/cyclists in view at once. This is consistent with, and
  likely compounds, the false-positive mechanism found on T01 (more
  objects per frame in training biases the detector toward firing more
  detections at inference, including on off-path objects the TTC engine
  mishandles).
- **Object scale**: `data_train` boxes are ~43% smaller on average in
  normalized height (0.067 vs 0.116) — objects tend to appear farther
  from camera / smaller in frame than in `practice`, a plausible
  contributor to the depth/TTC misjudgment on the T01 truck (a model
  trained more on small/distant boxes may generalize its depth cues
  differently for a large, close, off-path object).

**Conclusion:** the domain gap between `Data_train` (CARLA 0.10.0) and
`Practice_Dataset`/`extra_trips` (CARLA 0.9.15) is not a minor
distributional nuance — it is a large, statistically overwhelming shift
across lighting, scene density, and object scale simultaneously. This is
consistent with the repeated real-world regressions (v3/v4/v5) and
supports keeping `configs/challenge1.yaml` pinned to v2 (trained only on
the matching-domain sources) as the default until a `Data_train`-inclusive
variant is validated to beat 73.6/72.4 end-to-end, not just on training
loss.

## Note on data availability

`Data_train/` was not present under `HACKATHON/AI/` when
`compute_drift_metrics.py` was run to produce the attached CSV. Rather
than block on that, the script reads from
`datasets/yolo_finetune/images/{train,val}/` and
`datasets/yolo_finetune/labels/{train,val}/` instead — the physical copies
`scripts/prepare_yolo_finetune.py` made of every source frame it drew
from, identifiable by their `Data_train_...` / `Practice_Dataset_...` /
`extra_trips_...` filename prefixes. This is a faithful proxy for the same
frames, not a re-sample, so the PSI/KS numbers are unaffected by the
original folder's absence.

**Open item for Owner (Tâm/Hùng):** confirm why `Data_train/` is missing
from disk (not committed to git — likely excluded via `.gitattributes` or
never synced on this machine) and, if the team wants v6 (or further
`Data_train`-mixing attempts) validated end-to-end again later, re-fetch
it from the original source before re-running
`scripts/prepare_yolo_finetune.py`.
