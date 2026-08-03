"""
Direction A — learned TTC model, step 1: feature extraction.

Runs the full detection+depth+tracking pipeline over the 6 full-GT Practice
trips and dumps, per frame, a vector of INFERENCE-SAFE features (things also
computable on the redacted scored trips) alongside the ground-truth min_ttc
label. The learned regressor (train_ttc_model.py) then maps features → TTC,
replacing the hand-tuned thresholds that plateaued around composite 46.

Writes one parquet per trip to artifacts/features/ as it goes, so a killed
session keeps completed trips.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import yaml

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))
KIT = AI_ROOT / "Package_starterkit" / "Package_starterkit" / "package_starterkit"
DATA = AI_ROOT / "Practice_Dataset" / "Practice_Dataset"
OUT = AI_ROOT / "artifacts" / "features"
sys.path.insert(0, str(KIT))

# Deliberately self-contained -- do NOT import from scripts/run_inference.py.
# That script was rewritten upstream into a unified Challenge 1+2+3 script
# that pulls in core.challenge2_driver (needs joblib etc.), which is out of
# scope here and not installed in every environment this runs in (e.g. the
# GPU venv used for YOLO fine-tuning). Same fix as eval_practice.py.
from team_kit.dataset_loader import TripDataset   # noqa: E402
from core.challenge1_road.predict_ttc import RoadTTCPredictor  # noqa: E402
from core.challenge1_road.ttc_engine import FEATURE_KEYS       # noqa: E402


def _load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def extract_trip(trip_dir: Path, cfg: dict) -> pd.DataFrame:
    ds = TripDataset(trip_dir)
    p = RoadTTCPredictor(ds.load_calibration(), cfg)
    p.set_trip_dir(trip_dir)
    p.reset()
    rows = []
    for fr in ds.iter_frames():
        left = ds.load_left(fr.frame_id)
        right = ds.load_right(fr.frame_id)
        # Drives the pipeline and populates engine.last_features for this frame.
        p.predict_frame(fr.frame_id, fr.timestamp, left, right, fr.speed_kmh)
        feats = dict(p.engine.last_features) if p.engine.last_features else {
            k: 0.0 for k in FEATURE_KEYS
        }
        gt = fr.min_ttc
        feats.update({
            "trip_id": trip_dir.name,
            "frame_id": fr.frame_id,
            # extra ego context not in the engine snapshot
            "ego_long_accel": fr.longitudinal_accel,
            "ego_lat_accel": fr.lateral_accel,
            # labels
            "gt_ttc": 99.0 if not math.isfinite(gt) else float(gt),
            "gt_inv_ttc": 0.0 if not math.isfinite(gt) else 1.0 / max(gt, 0.1),
        })
        rows.append(feats)
    return pd.DataFrame(rows)


def main() -> int:
    import logging
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = _load_config(AI_ROOT / "configs" / "challenge1.yaml")

    trips = sorted(p for p in DATA.iterdir() if p.is_dir() and p.name.endswith("-Sample"))
    all_parts = []
    for trip in trips:
        out_path = OUT / f"{trip.name}.parquet"
        df = extract_trip(trip, cfg)
        df.to_parquet(out_path, index=False)
        n_crit = int(((df["gt_ttc"] < 3.0)).sum())
        print(f"  {trip.name}: {len(df)} frames, {n_crit} critical → {out_path.name}", flush=True)
        all_parts.append(df)

    combined = pd.concat(all_parts, ignore_index=True)
    combined.to_parquet(OUT / "all_trips.parquet", index=False)
    print(f"\nTotal: {len(combined)} frames across {len(trips)} trips → all_trips.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
