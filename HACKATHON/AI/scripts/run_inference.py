"""
Challenge 1 — run TTC inference on one or more trips and write submission CSVs.

Usage:
    # single trip
    python scripts/run_inference.py --trip-dir "<path>/T01-Sample" \
        --out predictions/FPTU_DMS_Vision

    # batch (all T*/ trips under a data root)
    python scripts/run_inference.py --data-dir "<path>/Practice_Dataset 2" \
        --out predictions/FPTU_DMS_Vision

Output: <out>/<trip_id>.csv with columns frame_id,timestamp,predicted_ttc
(the minimal Challenge-1 submission format).
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# --- make the AI package importable regardless of CWD ---
AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

from core.challenge1_road.predict_ttc import RoadTTCPredictor, format_ttc  # noqa: E402

logger = logging.getLogger("run_inference")


def _find_team_kit() -> Optional[Path]:
    """Locate the starter-kit `team_kit/` (holds dataset_loader.py)."""
    for cand in AI_ROOT.rglob("team_kit/dataset_loader.py"):
        return cand.parent.parent  # dir to add to sys.path
    return None


def _load_config(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    try:
        import yaml
        return yaml.safe_load(path.read_text()) or {}
    except ModuleNotFoundError:
        logger.warning("pyyaml not installed — using built-in defaults, ignoring %s", path)
        return {}


def run_trip(trip_dir: Path, out_dir: Path, config: Dict[str, Any]) -> Path:
    from team_kit.dataset_loader import TripDataset

    ds = TripDataset(trip_dir)
    calib = ds.load_calibration()
    if not calib:
        raise RuntimeError(f"No calibration_info.txt in {trip_dir}/kitti/")

    predictor = RoadTTCPredictor(calib, config)
    predictor.set_trip_dir(trip_dir)
    if not predictor.use_detector:
        logger.warning(
            "YOLO detector unavailable (%s) — falling back to stereo-ROI baseline.",
            predictor.detector.load_error,
        )
    predictor.reset()

    rows = []
    n = len(ds)
    for i, frame in enumerate(ds.iter_frames()):
        left = ds.load_left(frame.frame_id)
        right = ds.load_right(frame.frame_id)
        try:
            ttc = predictor.predict_frame(
                frame.frame_id, frame.timestamp, left, right, frame.speed_kmh
            )
        except Exception as e:  # never let one frame kill the whole trip
            logger.warning("frame %d failed: %s", frame.frame_id, e)
            ttc = float("inf")
        rows.append(
            {
                "frame_id": frame.frame_id,
                "timestamp": round(frame.timestamp, 3),
                "predicted_ttc": format_ttc(ttc),
            }
        )
        if i % 100 == 0 or i == n - 1:
            logger.info("%s: frame %d/%d  ttc=%s", ds.trip_id, i, n - 1, rows[-1]["predicted_ttc"])

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ds.trip_id}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["frame_id", "timestamp", "predicted_ttc"])
        writer.writeheader()
        writer.writerows(rows)
    logger.info("wrote %d rows → %s", len(rows), out_path)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Challenge 1 TTC inference → submission CSV.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--trip-dir", type=Path, help="single trip directory")
    g.add_argument("--data-dir", type=Path, help="root containing multiple T*/ trip dirs")
    ap.add_argument("--out", type=Path, required=True, help="output dir for CSVs")
    ap.add_argument("--config", type=Path, default=AI_ROOT / "configs" / "challenge1.yaml")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING"])
    args = ap.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    kit = _find_team_kit()
    if kit is None:
        logger.error("Could not find team_kit/dataset_loader.py under %s", AI_ROOT)
        return 2
    sys.path.insert(0, str(kit))

    config = _load_config(args.config if args.config.exists() else None)

    if args.trip_dir:
        run_trip(args.trip_dir, args.out, config)
    else:
        import re
        trips = sorted(
            p for p in args.data_dir.iterdir()
            if p.is_dir() and re.match(r"^T\d+d?(-Sample)?$", p.name)
        )
        if not trips:
            logger.error("No trip dirs found under %s", args.data_dir)
            return 2
        for trip in trips:
            run_trip(trip, args.out, config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
