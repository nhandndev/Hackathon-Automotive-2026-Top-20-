"""Replay every valid BTC-style trip in a folder as one fleet demo session.

Trips are registered together so the Dashboard can show the whole fleet.  AI
inference runs sequentially to keep GPU/RAM usage bounded; Backend keeps each
completed trip's latest frames, timeline and DecisionEvents.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))

from core.btc_trip import TripDataset  # noqa: E402
from integrations.se_client import SEApiClient  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sequential multi-trip dataset replay for Fleet Dashboard"
    )
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--se-endpoint",
        default="http://127.0.0.1:8000/api/v1/alerts",
    )
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--max-trips", type=int, default=0)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument(
        "--output-dir", type=Path,
        default=AI_ROOT / "artifacts" / "fleet_demo",
    )
    parser.add_argument(
        "--driver-model", type=Path,
        default=AI_ROOT / "models" / "driver_state_rf_v3_onnx.joblib",
    )
    parser.add_argument(
        "--road-inference-interval", type=int, default=5,
    )
    parser.add_argument(
        "--face-detector-interval", type=int, default=10,
    )
    args = parser.parse_args()
    if args.speed <= 0 or args.max_trips < 0 or args.max_frames < 0:
        parser.error("speed must be positive and limits must be non-negative")
    return args


def discover_trips(data_dir: str | Path) -> list[TripDataset]:
    root = Path(data_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset folder not found: {root}")
    trips: list[TripDataset] = []
    for child in sorted(root.iterdir(), key=lambda path: path.name.casefold()):
        if not child.is_dir():
            continue
        if not (
            (child / f"{child.name}.json").is_file()
            or (child / f"{child.name}.json.gz").is_file()
        ):
            continue
        trip = TripDataset(child)
        required = (
            trip.image_left_dir,
            trip.image_right_dir,
            trip.driver_dir,
            trip.trip_dir / "kitti" / "calibration_info.txt",
        )
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(
                f"{trip.trip_id}: incomplete BTC trip; missing {missing}"
            )
        trips.append(trip)
    if not trips:
        raise RuntimeError(
            f"No BTC-style trip folders found directly under {root}"
        )
    return trips


def main() -> int:
    args = parse_args()
    trips = discover_trips(args.data_dir)
    if args.max_trips:
        trips = trips[: args.max_trips]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    client = SEApiClient(
        args.se_endpoint,
        api_key=os.getenv("FPTU_SE_API_KEY"),
        bearer_token=os.getenv("FPTU_SE_BEARER_TOKEN"),
    )
    try:
        client.register_trips(
            [
                {"trip_id": trip.trip_id, "metadata": trip.metadata}
                for trip in trips
            ],
            reset_existing=True,
        )
    finally:
        client.close()

    print("Fleet registered:", ", ".join(trip.trip_id for trip in trips))
    runner = Path(__file__).with_name("end_to_end_demo.py")
    for index, trip in enumerate(trips, start=1):
        print(f"\n[{index}/{len(trips)}] Replay {trip.trip_id}")
        command = [
            sys.executable,
            str(runner),
            "--trip-dir", str(trip.trip_dir),
            "--driver-source", "dataset",
            "--driver-model", str(args.driver_model),
            "--se-endpoint", args.se_endpoint,
            "--speed", str(args.speed),
            "--road-inference-interval", str(args.road_inference_interval),
            "--face-detector-interval", str(args.face_detector_interval),
            "--output-csv", str(args.output_dir / f"{trip.trip_id}.csv"),
            "--events", str(args.output_dir / f"{trip.trip_id}.events.jsonl"),
        ]
        if args.max_frames:
            command.extend(("--max-frames", str(args.max_frames)))
        if args.no_display:
            command.append("--no-display")
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                f"{trip.trip_id} failed with exit code {completed.returncode}"
            )

    print(f"\nFleet demo completed: {len(trips)} trips")
    print(f"Artifacts: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
