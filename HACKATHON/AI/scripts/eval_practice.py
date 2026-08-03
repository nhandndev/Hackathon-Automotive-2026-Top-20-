"""
Run Challenge-1-ONLY inference on all 6 full-GT Practice trips, score each
with the organizer's evaluation.py, and print a per-trip + average composite
table. This is the local self-check loop for tuning (file 03/04 workflow).

Deliberately self-contained: scripts/run_inference.py was rewritten upstream
into a unified Challenge 1+2+3 script that always also runs the driver-state
and risk-score models, which is out of scope here (this repo's Challenge 1
work stays isolated from Challenge 2/3, per team split). This script calls
RoadTTCPredictor directly and writes only the minimal
frame_id,timestamp,predicted_ttc columns -- a valid Challenge-1-only
submission per evaluation.py's own rules (extra columns are optional).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

KIT = AI_ROOT / "Package_starterkit" / "Package_starterkit" / "package_starterkit"
DATA = AI_ROOT / "Practice_Dataset" / "Practice_Dataset"
OUT = AI_ROOT / "predictions" / "FPTU_DMS_Vision"
sys.path.insert(0, str(KIT))

from core.challenge1_road.predict_ttc import RoadTTCPredictor, format_ttc  # noqa: E402
from team_kit.dataset_loader import TripDataset  # noqa: E402
from team_kit.evaluation import evaluate  # noqa: E402


def run_trip_ch1_only(trip_dir: Path, out_dir: Path, config: dict) -> Path:
    ds = TripDataset(trip_dir)
    predictor = RoadTTCPredictor(ds.load_calibration(), config)
    predictor.set_trip_dir(trip_dir)
    predictor.reset()
    rows = []
    for fr in ds.iter_frames():
        left, right = ds.load_left(fr.frame_id), ds.load_right(fr.frame_id)
        ttc = predictor.predict_frame(fr.frame_id, fr.timestamp, left, right, fr.speed_kmh)
        rows.append({"frame_id": fr.frame_id, "timestamp": round(fr.timestamp, 3),
                      "predicted_ttc": format_ttc(ttc)})
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ds.trip_id}.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["frame_id", "timestamp", "predicted_ttc"])
        w.writeheader()
        w.writerows(rows)
    return out_path


def main() -> int:
    import logging
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    config = yaml.safe_load((AI_ROOT / "configs" / "challenge1.yaml").read_text()) or {}
    trips = sorted(p for p in DATA.iterdir() if p.is_dir() and p.name.endswith("-Sample"))

    rows = []
    for trip in trips:
        run_trip_ch1_only(trip, OUT, config)
        report = evaluate(OUT / f"{trip.name}.csv", DATA, None)
        m = report.per_trip[0]
        rows.append((trip.name, m.mae_critical, m.f1, m.inv_ttc_mae, m.composite_score))
        print(f"  {trip.name}: MAE-crit={m.mae_critical:.2f} F1={m.f1:.2f} "
              f"inv={m.inv_ttc_mae:.3f} composite={m.composite_score:.1f}", flush=True)

    print("\n==== SUMMARY ====")
    print(f"{'Trip':<14}{'MAE-crit':<10}{'F1':<7}{'inv':<8}{'Composite':<10}")
    for name, mae, f1, inv, comp in rows:
        print(f"{name:<14}{mae:<10.2f}{f1:<7.2f}{inv:<8.3f}{comp:<10.1f}")
    avg = sum(r[4] for r in rows) / len(rows)
    print(f"\nAVERAGE COMPOSITE: {avg:.1f} / 100")
    return 0


if __name__ == "__main__":
    sys.exit(main())
