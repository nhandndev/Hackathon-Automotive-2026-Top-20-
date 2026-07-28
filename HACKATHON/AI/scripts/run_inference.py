"""Unified Challenge 1+2+3 inference with the official BTC CSV contract."""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

from core.challenge1_road.predict_ttc import (  # noqa: E402
    RoadTTCPredictor,
    format_ttc,
)
from core.challenge2_driver import DriverStatePredictor  # noqa: E402
from core.challenge3_fusion import predicted_risk_score  # noqa: E402

LOGGER = logging.getLogger("run_inference")
CSV_FIELDS = [
    "frame_id",
    "timestamp",
    "predicted_ttc",
    "predicted_driver_state",
    "predicted_risk_score",
]


def install_starterkit(starterkit_root: Path | None) -> None:
    candidates = []
    if starterkit_root is not None:
        candidates.append(starterkit_root.resolve())
    candidates.extend([Path.cwd(), AI_ROOT.parent])
    for candidate in candidates:
        if (candidate / "team_kit" / "dataset_loader.py").is_file():
            sys.path.insert(0, str(candidate))
            return
    raise FileNotFoundError(
        "Could not find team_kit/dataset_loader.py. Pass "
        "--starterkit-root <Package_starterkit>."
    )


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run_trip(
    trip_dir: Path,
    output_dir: Path,
    road_config: dict[str, Any],
    driver_config: Path,
    driver_model: Path,
) -> Path:
    from team_kit.dataset_loader import TripDataset

    dataset = TripDataset(trip_dir)
    road = RoadTTCPredictor(dataset.load_calibration(), road_config)
    road.set_trip_dir(trip_dir)
    road.reset()
    driver = DriverStatePredictor(driver_model, driver_config)
    rows: list[dict[str, object]] = []
    try:
        for index, frame in enumerate(dataset.iter_frames()):
            left = dataset.load_left(frame.frame_id)
            right = dataset.load_right(frame.frame_id)
            cabin = dataset.load_driver(frame.frame_id)
            try:
                ttc = road.predict_frame(
                    frame.frame_id,
                    frame.timestamp,
                    left,
                    right,
                    frame.speed_kmh,
                )
            except Exception as exc:
                LOGGER.warning(
                    "%s frame %d TTC failed: %s",
                    dataset.trip_id,
                    frame.frame_id,
                    exc,
                )
                ttc = float("inf")
            driver_result = driver.predict_frame(
                frame.frame_id,
                round(frame.timestamp * 1000),
                cabin,
            )
            state = str(driver_result["state"])
            rows.append({
                "frame_id": frame.frame_id,
                "timestamp": f"{frame.timestamp:.3f}",
                "predicted_ttc": format_ttc(ttc),
                "predicted_driver_state": state,
                "predicted_risk_score": predicted_risk_score(ttc, state),
            })
            if (index + 1) % 100 == 0 or index + 1 == len(dataset):
                LOGGER.info(
                    "%s: %d/%d frames",
                    dataset.trip_id,
                    index + 1,
                    len(dataset),
                )
    finally:
        driver.close()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{dataset.trip_id}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    LOGGER.info("Wrote %d rows -> %s", len(rows), output_path)
    return output_path


def discover_trips(
    trip_dir: Path | None,
    data_dir: Path | None,
) -> list[Path]:
    if trip_dir is not None:
        return [trip_dir.resolve()]
    assert data_dir is not None
    return sorted(
        path
        for path in data_dir.resolve().iterdir()
        if path.is_dir()
        and re.match(r"^T\d+(d|-Sample)?$", path.name)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified BTC inference for Challenges 1, 2 and 3"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--trip-dir", type=Path)
    source.add_argument("--data-dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--starterkit-root",
        type=Path,
        help="Directory containing team_kit/dataset_loader.py",
    )
    parser.add_argument(
        "--road-config",
        type=Path,
        default=AI_ROOT / "configs" / "challenge1.yaml",
    )
    parser.add_argument(
        "--driver-config",
        type=Path,
        default=AI_ROOT / "configs" / "challenge2.yaml",
    )
    parser.add_argument(
        "--driver-model",
        type=Path,
        default=AI_ROOT / "models" / "driver_state_rf.joblib",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    install_starterkit(args.starterkit_root)
    trips = discover_trips(args.trip_dir, args.data_dir)
    if not trips:
        parser.error("No BTC trip directories found")
    road_config = load_yaml(args.road_config)
    for trip in trips:
        run_trip(
            trip,
            args.out,
            road_config,
            args.driver_config,
            args.driver_model,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
