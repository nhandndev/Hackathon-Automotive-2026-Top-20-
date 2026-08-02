"""Unified Challenge 1+2+3 inference with the official BTC CSV contract."""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
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
from core.challenge3_fusion import FleetSafeDrivingScorer  # noqa: E402
from core.decision_engine import (  # noqa: E402
    DecisionEngine,
    DecisionPolicy,
    DecisionSnapshot,
)
from core.btc_trip import TripDataset  # noqa: E402

LOGGER = logging.getLogger("run_inference")
CSV_FIELDS = [
    "frame_id",
    "timestamp",
    "predicted_ttc",
    "predicted_driver_state",
    "predicted_risk_score",
]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run_trip(
    trip_dir: Path,
    output_path: Path,
    road_config: dict[str, Any],
    driver_config: Path,
    driver_model: Path,
    speed_limit_override: float | None = None,
    decision_config: Path | None = None,
    decision_events_path: Path | None = None,
    driver_id: str | None = None,
) -> Path:
    detector_config = road_config.get("detector", {})
    if detector_config.get("device") in (None, "cpu"):
        try:
            import torch
            if not torch.cuda.is_available():
                torch.set_num_threads(int(detector_config.get("cpu_threads", 4)))
        except (ImportError, RuntimeError, ValueError):
            pass
    dataset = TripDataset(trip_dir)
    LOGGER.info(
        "%s: input=%s frames=%d",
        dataset.trip_id,
        dataset.trip_dir,
        len(dataset),
    )
    road = RoadTTCPredictor(dataset.load_calibration(), road_config)
    road.set_trip_dir(trip_dir)
    road.reset()
    driver = DriverStatePredictor(driver_model, driver_config)
    try:
        speed_limit_kmh = (
            float(speed_limit_override)
            if speed_limit_override is not None
            else float(dataset.metadata["speed_limit_kmh"])
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"{dataset.trip_id}: metadata.speed_limit_kmh is required "
            "for BTC Challenge 3"
        ) from exc
    fleet = FleetSafeDrivingScorer(speed_limit_kmh)
    decision = (
        DecisionEngine(
            DecisionPolicy.load(decision_config),
            model_versions={
                "challenge1": str(road_config.get("detector", {}).get("weights", "unknown")),
                "challenge2": driver_model.name,
                "challenge3": "btc_behavior_scorer_v1",
            },
        )
        if decision_config is not None and decision_events_path is not None
        else None
    )
    decision_events: list[dict[str, Any]] = []
    last_decision_snapshot: DecisionSnapshot | None = None
    rows: list[dict[str, object]] = []
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    try:
        for index, frame in enumerate(dataset.iter_frames()):
            left = dataset.load_left(frame.frame_id)
            right = dataset.load_right(frame.frame_id)
            cabin = dataset.load_driver(frame.frame_id)
            road_future = executor.submit(
                road.predict_frame,
                frame.frame_id,
                frame.timestamp,
                left,
                right,
                frame.speed_kmh,
            )
            driver_future = executor.submit(
                driver.predict_frame,
                frame.frame_id,
                round(frame.timestamp * 1000),
                cabin,
            )
            try:
                ttc = road_future.result()
                road_quality_status = "valid"
            except Exception as exc:
                LOGGER.warning(
                    "%s frame %d TTC failed: %s",
                    dataset.trip_id,
                    frame.frame_id,
                    exc,
                )
                ttc = float("inf")
                road_quality_status = "invalid"
            driver_result = driver_future.result()
            state = str(driver_result["state"])
            fleet_score = fleet.update(
                predicted_ttc=ttc,
                speed_kmh=frame.speed_kmh,
                longitudinal_accel=frame.longitudinal_accel,
                lateral_accel=frame.lateral_accel,
            )
            if decision is not None:
                features = driver_result.get("features", {})
                last_decision_snapshot = DecisionSnapshot(
                    trip_id=dataset.trip_id,
                    frame_id=frame.frame_id,
                    timestamp_ms=round(frame.timestamp * 1000),
                    driver_id=driver_id,
                    speed_kmh=frame.speed_kmh,
                    speed_limit_kmh=speed_limit_kmh,
                    longitudinal_accel=frame.longitudinal_accel,
                    lateral_accel=frame.lateral_accel,
                    predicted_ttc_sec=ttc,
                    # Challenge 1 already applies its configured danger
                    # confirmation before returning a sub-2s TTC.
                    ttc_confirmed=True,
                    road_quality_status=road_quality_status,
                    driver_state=state,
                    driver_confidence=float(driver_result["confidence"]),
                    alertness_score=float(driver_result["alertness_score"]),
                    driver_quality_status=str(driver_result["quality_status"]),
                    face_detected=bool(driver_result.get("face_detected", False)),
                    left_eye_valid=bool(driver_result.get("left_eye_valid", False)),
                    right_eye_valid=bool(driver_result.get("right_eye_valid", False)),
                    monitoring_available=bool(
                        driver_result.get("monitoring_available", False)
                    ),
                    valid_window_ratio=float(
                        driver_result.get("valid_window_ratio", 0.0)
                    ),
                    continuous_eye_closure_ms=int(
                        features.get("continuous_eye_closure_ms", 0) or 0
                    ),
                    perclos_30s=float(features.get("perclos_30s", 0.0) or 0.0),
                    off_road_duration_ms=int(
                        features.get("off_road_duration_ms", 0) or 0
                    ),
                    mouth_state=str(driver_result.get("mouth_state", "normal")),
                    mouth_open_duration_ms=int(
                        features.get("mouth_open_duration_ms", 0) or 0
                    ),
                    c3_risk_score=fleet_score.risk_score,
                    c3_safe_score=fleet_score.safe_driving_score,
                )
                decision_events.extend(
                    event.transport_dict()
                    for event in decision.update(last_decision_snapshot)
                )
            rows.append({
                "frame_id": frame.frame_id,
                "timestamp": f"{frame.timestamp:.3f}",
                "predicted_ttc": format_ttc(ttc),
                "predicted_driver_state": state,
                # BTC's CSV calls this a risk score. We emit accumulated
                # penalty points; 100 - the last row is the trip safe score.
                "predicted_risk_score": fleet_score.risk_score,
            })
            if (index + 1) % 50 == 0 or index + 1 == len(dataset):
                LOGGER.info(
                    "%s: %d/%d frames",
                    dataset.trip_id,
                    index + 1,
                    len(dataset),
                )
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
        driver.close()

    if decision is not None and last_decision_snapshot is not None:
        decision_events.extend(
            event.transport_dict()
            for event in decision.resolve_all(last_decision_snapshot)
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    LOGGER.info("Wrote %d rows -> %s", len(rows), output_path)
    if decision_events_path is not None:
        decision_events_path.parent.mkdir(parents=True, exist_ok=True)
        with decision_events_path.open("w", encoding="utf-8") as stream:
            for event in decision_events:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        LOGGER.info(
            "Wrote %d decision event(s) -> %s",
            len(decision_events),
            decision_events_path,
        )
    final = fleet.snapshot()
    LOGGER.info(
        "%s: [C3] safe=%.1f risk=%.1f near_miss=%d harsh=%d/%d/%d "
        "speeding=%.1f%%",
        dataset.trip_id,
        final.safe_driving_score,
        final.risk_score,
        final.near_miss_count,
        final.harsh_brake_count,
        final.harsh_accel_count,
        final.harsh_corner_count,
        final.speeding_pct_time,
    )
    return output_path


def discover_trips(
    trip_dir: Path | None,
    data_dir: Path | None,
    samples_only: bool = False,
    scored_only: bool = False,
) -> list[Path]:
    if trip_dir is not None:
        return [trip_dir.resolve()]
    assert data_dir is not None
    trips = sorted(
        path
        for path in data_dir.resolve().iterdir()
        if path.is_dir()
        and re.match(r"^T\d+(d|-Sample)?$", path.name)
    )
    if samples_only:
        trips = [
            path for path in trips
            if re.fullmatch(r"T\d{2}-Sample", path.name)
        ]
    elif scored_only:
        trips = [
            path for path in trips
            if re.fullmatch(r"T\d{2}d", path.name)
        ]
    return trips


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified BTC inference for Challenges 1, 2 and 3"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--trip-dir", type=Path)
    source.add_argument("--data-dir", type=Path)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--samples-only",
        action="store_true",
        help="With --data-dir, run only T01-Sample through T06-Sample",
    )
    selection.add_argument(
        "--scored-only",
        action="store_true",
        help="With --data-dir, run only organizer scored trips T01d...T10d",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=AI_ROOT / "artifacts" / "predictions",
        help="Output directory (used for --data-dir or as single-trip default)",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        help="Exact output CSV path; valid only with --trip-dir",
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
        default=AI_ROOT / "models" / "driver_state_rf_v3_onnx.joblib",
    )
    parser.add_argument(
        "--speed-limit-kmh",
        type=float,
        help=(
            "Override metadata.speed_limit_kmh; intended only for derived "
            "demo trips whose mixed-source metadata omits a speed limit"
        ),
    )
    parser.add_argument(
        "--decision-events-dir",
        type=Path,
        help=(
            "Enable the post-C3 Decision Engine and write one JSONL event "
            "file per trip into this directory"
        ),
    )
    parser.add_argument(
        "--decision-config",
        type=Path,
        default=AI_ROOT / "configs" / "decision_engine.yaml",
    )
    parser.add_argument(
        "--driver-id",
        help="Optional non-biometric driver ID included in decision events",
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
    if args.trip_dir is not None and (
        args.samples_only or args.scored_only
    ):
        parser.error("--samples-only/--scored-only require --data-dir")
    trips = discover_trips(
        args.trip_dir,
        args.data_dir,
        samples_only=args.samples_only,
        scored_only=args.scored_only,
    )
    if not trips:
        parser.error("No BTC trip directories found")
    LOGGER.info(
        "Discovered %d trip(s): %s",
        len(trips),
        ", ".join(path.name for path in trips),
    )
    if args.output_csv is not None and args.trip_dir is None:
        parser.error("--output-csv requires --trip-dir")
    road_config = load_yaml(args.road_config)
    for trip in trips:
        output_path = (
            args.output_csv
            if args.output_csv is not None
            else args.out / f"{trip.name}.csv"
        )
        run_trip(
            trip,
            output_path,
            road_config,
            args.driver_config,
            args.driver_model,
            args.speed_limit_kmh,
            decision_config=(
                args.decision_config
                if args.decision_events_dir is not None
                else None
            ),
            decision_events_path=(
                args.decision_events_dir / f"{trip.name}.events.jsonl"
                if args.decision_events_dir is not None
                else None
            ),
            driver_id=args.driver_id,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
