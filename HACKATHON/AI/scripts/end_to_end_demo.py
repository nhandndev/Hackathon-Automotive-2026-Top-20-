"""Hybrid product demo: BTC road/telemetry + live driver webcam.

The script reuses the production C1/C2/C3 cores, then sends canonical
DecisionEvents to the SE FastAPI boundary. Submission CSV remains independent.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import csv
import json
import math
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import yaml

AI_ROOT = Path(__file__).resolve().parents[1]
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))

from core.btc_trip import TripDataset  # noqa: E402
from core.challenge1_road.predict_ttc import RoadTTCPredictor, format_ttc  # noqa: E402
from core.challenge2_driver.driver_profile import ProfileStore  # noqa: E402
from core.challenge2_driver.predict_state import DriverStatePredictor  # noqa: E402
from core.challenge3_fusion.risk_engine import FleetSafeDrivingScorer  # noqa: E402
from core.decision_engine import DecisionEngine, DecisionPolicy, DecisionSnapshot  # noqa: E402
from integrations.se_client import SEApiClient  # noqa: E402
import threading
from scripts.trip_visual_demo import (  # noqa: E402
    CSV_FIELDS,
    WINDOW_NAME,
    draw_dashboard,
    draw_face,
    draw_right,
    draw_road,
    project_kitti_labels,
    InterventionOverlayState,
    _poll_interventions,
    draw_intervention_overlay,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="End-to-end demo using BTC road cameras and a live webcam"
    )
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument(
        "--driver-source", choices=("webcam", "dataset"), default="webcam",
        help="Use a live webcam or the trip's driver/frame images",
    )
    parser.add_argument("--driver-id")
    parser.add_argument(
        "--profiles-dir", type=Path,
        default=AI_ROOT / "artifacts" / "driver_profiles",
    )
    parser.add_argument(
        "--road-config", type=Path,
        default=AI_ROOT / "configs" / "challenge1.yaml",
    )
    parser.add_argument(
        "--driver-config", type=Path,
        default=AI_ROOT / "configs" / "challenge2.yaml",
    )
    parser.add_argument(
        "--driver-model", type=Path,
        default=AI_ROOT / "models" / "driver_state_rf_v4_dataset_v2.joblib",
        help="Challenge-2 Random Forest .joblib artifact",
    )
    parser.add_argument(
        "--decision-config", type=Path,
        default=AI_ROOT / "configs" / "decision_engine.yaml",
    )
    parser.add_argument(
        "--se-endpoint",
        help="Example: http://127.0.0.1:8000/api/v1/alerts",
    )
    parser.add_argument("--speed-limit-kmh", type=float)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument(
        "--road-inference-interval", type=int, default=5,
        help="Demo-only: run C1 every N displayed frames and reuse the latest result",
    )
    parser.add_argument(
        "--face-detector-interval", type=int, default=10,
        help="Demo-only: rerun YuNet every N frames; landmarks still run every frame",
    )
    parser.add_argument(
        "--dashboard-stream-fps", "--cabin-stream-fps",
        dest="dashboard_stream_fps", type=float, default=5.0,
        help="Road/cabin JPEG and metric snapshot rate sent to Dashboard; 0 disables it",
    )
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument(
        "--events", type=Path,
        default=AI_ROOT / "artifacts" / "decision_events" / "live.events.jsonl",
    )
    args = parser.parse_args()
    if args.driver_model.suffix.lower() != ".joblib" or not args.driver_model.is_file():
        parser.error(
            f"--driver-model must be an existing .joblib file: {args.driver_model}"
        )
    if (
        args.speed <= 0
        or args.max_frames < 0
        or args.dashboard_stream_fps < 0
        or args.road_inference_interval < 1
        or args.face_detector_interval < 1
    ):
        parser.error("--speed must be positive; frame limits/rates must be non-negative")
    return args


def snapshot_from_outputs(
    dataset, frame, live_timestamp_ms, speed_limit, ttc, driver, fleet,
    road_confirmed=True,
):
    features = driver.get("features", {})
    return DecisionSnapshot(
        trip_id=dataset.trip_id,
        driver_id=None,
        frame_id=frame.frame_id,
        timestamp_ms=live_timestamp_ms,
        speed_kmh=frame.speed_kmh,
        speed_limit_kmh=speed_limit,
        longitudinal_accel=frame.longitudinal_accel,
        lateral_accel=frame.lateral_accel,
        predicted_ttc_sec=ttc,
        ttc_confirmed=bool(road_confirmed),
        road_quality_status="valid" if road_confirmed else "warming_up",
        driver_state=str(driver["state"]),
        driver_confidence=float(driver["confidence"]),
        alertness_score=float(driver["alertness_score"]),
        driver_quality_status=str(driver["quality_status"]),
        face_detected=bool(driver.get("face_detected", False)),
        left_eye_valid=bool(driver.get("left_eye_valid", False)),
        right_eye_valid=bool(driver.get("right_eye_valid", False)),
        monitoring_available=bool(driver.get("monitoring_available", False)),
        valid_window_ratio=float(driver.get("valid_window_ratio", 0.0)),
        continuous_eye_closure_ms=int(features.get("continuous_eye_closure_ms", 0) or 0),
        perclos_30s=float(features.get("perclos_30s", 0.0) or 0.0),
        off_road_duration_ms=int(features.get("off_road_duration_ms", 0) or 0),
        mouth_state=str(driver.get("mouth_state", "normal")),
        mouth_open_duration_ms=int(features.get("mouth_open_duration_ms", 0) or 0),
        c3_risk_score=fleet.risk_score,
        c3_safe_score=fleet.safe_driving_score,
    )


def main() -> int:
    args = parse_args()
    dataset = TripDataset(args.trip_dir.resolve())
    road_cfg = yaml.safe_load(args.road_config.read_text(encoding="utf-8")) or {}
    detector_cfg = road_cfg.get("detector", {})
    if detector_cfg.get("device") in (None, "cpu"):
        try:
            import torch
            if not torch.cuda.is_available():
                torch.set_num_threads(int(detector_cfg.get("cpu_threads", 4)))
        except (ImportError, RuntimeError, ValueError):
            pass
    road = RoadTTCPredictor(dataset.load_calibration(), road_cfg)
    road.set_trip_dir(dataset.trip_dir)
    road.reset()

    profile = None
    if args.driver_id:
        store = ProfileStore(args.profiles_dir)
        if not store.exists(args.driver_id):
            raise FileNotFoundError(
                f"Driver profile '{args.driver_id}' is missing; enroll it with webcam_driver_demo.py first"
            )
        profile = store.load(args.driver_id)
    driver = DriverStatePredictor(
        args.driver_model,
        args.driver_config,
        driver_profile=profile,
        face_detector_interval_frames=args.face_detector_interval,
    )
    speed_limit = (
        float(args.speed_limit_kmh) if args.speed_limit_kmh is not None
        else float(dataset.metadata["speed_limit_kmh"])
    )
    fleet = FleetSafeDrivingScorer(speed_limit)
    decision = DecisionEngine(
        DecisionPolicy.load(args.decision_config),
        model_versions={"challenge2": args.driver_model.name},
    )
    client = SEApiClient(
        args.se_endpoint,
        api_key=os.getenv("FPTU_SE_API_KEY"),
        bearer_token=os.getenv("FPTU_SE_BEARER_TOKEN"),
    ) if args.se_endpoint else None

    if client:
        client.register_trips([
            {"trip_id": dataset.trip_id, "metadata": dataset.metadata}
        ])

    capture = None
    if args.driver_source == "webcam":
        capture = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
        if not capture.isOpened():
            raise RuntimeError(f"Cannot open webcam {args.camera}")
    args.events.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    last_snapshot = None
    processed = 0
    paused = False
    fps = float(dataset.metadata.get("fps", 20.0) or 20.0)
    live_started_ns = time.perf_counter_ns()
    # C1 is intentionally decoupled from the UI loop in product-demo mode.
    # Submission inference remains frame-by-frame in run_inference.py.
    road_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    road_future: concurrent.futures.Future[tuple[float, dict, int]] | None = None
    cached_ttc = float("inf")
    cached_road_debug: dict = {}
    road_confirmed = False
    media_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    media_future: concurrent.futures.Future[dict[str, object]] | None = None
    next_dashboard_publish_ms = 0.0
    trip_finished = False

    # ── Intervention overlay polling (background thread) ───────────────────
    intervention_overlay = InterventionOverlayState()
    _stop_poll = threading.Event()
    _poll_thread = threading.Thread(
        target=_poll_interventions,
        args=(intervention_overlay, dataset.trip_id, _stop_poll),
        daemon=True,
    )
    _poll_thread.start()

    try:
        with args.events.open("w", encoding="utf-8") as event_stream:
            records = list(dataset.iter_frames())
            source_index = 0
            next_frame_due = time.perf_counter()
            while source_index < len(records):
                frame = records[source_index]
                if capture is not None:
                    ok, cabin = capture.read()
                    if not ok:
                        raise RuntimeError("Webcam stopped returning frames")
                else:
                    cabin = dataset.load_driver(frame.frame_id)
                live_timestamp_ms = (
                    time.perf_counter_ns() - live_started_ns
                ) // 1_000_000
                left = dataset.load_left(frame.frame_id)
                right = dataset.load_right(frame.frame_id)
                if road_future is not None and road_future.done():
                    try:
                        cached_ttc, cached_road_debug, _ = road_future.result()
                        road_confirmed = True
                    except Exception as exc:
                        road_confirmed = False
                        print(f"Road inference warning: {exc}", file=sys.stderr)
                    road_future = None
                if (
                    road_future is None
                    and (
                        not road_confirmed
                        or processed % args.road_inference_interval == 0
                    )
                ):
                    road_frame_id = frame.frame_id
                    road_timestamp = frame.timestamp
                    road_speed = frame.speed_kmh
                    road_left = left.copy()
                    road_right = right.copy()

                    def infer_road(
                        frame_id=road_frame_id,
                        timestamp=road_timestamp,
                        speed_kmh=road_speed,
                        left_bgr=road_left,
                        right_bgr=road_right,
                    ) -> tuple[float, dict, int]:
                        value = road.predict_frame(
                            frame_id, timestamp,
                            left_bgr, right_bgr, speed_kmh,
                        )
                        return value, copy.deepcopy(road.last_debug), frame_id

                    road_future = road_executor.submit(infer_road)
                ttc = cached_ttc
                driver_out = driver.predict_frame(
                    frame.frame_id, live_timestamp_ms, cabin
                )
                annotated_cabin = draw_face(cabin, driver_out)
                fleet_out = fleet.update(
                    ttc, frame.speed_kmh,
                    frame.longitudinal_accel, frame.lateral_accel,
                )
                last_snapshot = snapshot_from_outputs(
                    dataset, frame, live_timestamp_ms, speed_limit, ttc,
                    driver_out, fleet_out, road_confirmed=road_confirmed
                ).model_copy(update={"driver_id": args.driver_id})
                for event in decision.update(last_snapshot):
                    payload = event.transport_dict()
                    event_stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
                    event_stream.flush()
                    if client:
                        client.send(event)
                annotations = [] if cached_road_debug.get("objects") else project_kitti_labels(
                    dataset, frame.frame_id, left.shape
                )
                annotated_road = draw_road(
                    left, ttc, cached_road_debug, annotations
                )
                if (
                    client
                    and args.dashboard_stream_fps > 0
                    and live_timestamp_ms >= next_dashboard_publish_ms
                    and (media_future is None or media_future.done())
                ):
                    if media_future is not None:
                        try:
                            media_future.result()
                        except Exception as exc:
                            print(f"Dashboard stream warning: {exc}", file=sys.stderr)
                    cabin_ok, cabin_jpeg = cv2.imencode(
                        ".jpg", annotated_cabin,
                        [cv2.IMWRITE_JPEG_QUALITY, 78],
                    )
                    road_ok, road_jpeg = cv2.imencode(
                        ".jpg", annotated_road,
                        [cv2.IMWRITE_JPEG_QUALITY, 78],
                    )
                    if cabin_ok and road_ok:
                        media_future = media_executor.submit(
                            client.send_live_update,
                            cabin_jpeg=cabin_jpeg.tobytes(),
                            road_jpeg=road_jpeg.tobytes(),
                            snapshot={
                                "schema_version": "1.0",
                                "trip_id": dataset.trip_id,
                                "frame_id": frame.frame_id,
                                "trip_timestamp_ms": live_timestamp_ms,
                                "speed_kmh": float(frame.speed_kmh),
                                "predicted_ttc_sec": (
                                    float(ttc) if math.isfinite(float(ttc)) else None
                                ),
                                "risk_score": float(fleet_out.risk_score),
                                "driver_state": str(driver_out["state"]),
                                "driver_confidence": float(driver_out["confidence"]),
                                "alertness_score": float(driver_out["alertness_score"]),
                            },
                        )
                    next_dashboard_publish_ms = (
                        live_timestamp_ms + 1000.0 / args.dashboard_stream_fps
                    )
                rows.append({
                    "frame_id": frame.frame_id,
                    "timestamp": f"{frame.timestamp:.3f}",
                    "predicted_ttc": format_ttc(ttc),
                    "predicted_driver_state": driver_out["state"],
                    "predicted_risk_score": fleet_out.risk_score,
                })
                canvas = np.vstack([
                    np.hstack([annotated_road, draw_right(right)]),
                    np.hstack([
                        annotated_cabin,
                        draw_dashboard(dataset.trip_id, frame, ttc, driver_out,
                                       fleet_out.risk_score, args.speed, paused),
                    ]),
                ])
                # ── Intervention overlay (drawn on full canvas before display) ─────
                active_cmd = intervention_overlay.get_active()
                if active_cmd is not None:
                    canvas = draw_intervention_overlay(
                        canvas, active_cmd, intervention_overlay.remaining()
                    )
                processed += 1
                realtime_pacing = not args.no_display or client is not None
                if realtime_pacing:
                    frame_period = 1.0 / (fps * args.speed)
                    next_frame_due += frame_period
                if not args.no_display:
                    cv2.imshow(WINDOW_NAME + " - LIVE DRIVER", canvas)
                    wait_ms = max(
                        1, int((next_frame_due - time.perf_counter()) * 1000)
                    )
                    key = cv2.waitKey(wait_ms) & 0xFF
                    if key in (ord("q"), 27):
                        break
                    if key in (ord("+"), ord("=")):
                        args.speed = min(8.0, args.speed * 2.0)
                        next_frame_due = time.perf_counter()
                        print(f"Playback speed: {args.speed:g}x")
                    elif key in (ord("-"), ord("_")):
                        args.speed = max(0.25, args.speed / 2.0)
                        next_frame_due = time.perf_counter()
                        print(f"Playback speed: {args.speed:g}x")
                elif realtime_pacing:
                    remaining = next_frame_due - time.perf_counter()
                    if remaining > 0:
                        time.sleep(remaining)
                if args.max_frames and processed >= args.max_frames:
                    break
                # If inference falls behind, discard old BTC road frames. The
                # live webcam and dashboard therefore stay close to wall time
                # instead of accumulating an ever-growing delay.
                source_index += 1
                if realtime_pacing:
                    frame_period = 1.0 / (fps * args.speed)
                    behind = time.perf_counter() - next_frame_due
                    if behind >= frame_period:
                        skipped = min(
                            int(behind / frame_period),
                            len(records) - source_index,
                        )
                        source_index += skipped
                        next_frame_due += skipped * frame_period
            if last_snapshot is not None:
                for event in decision.resolve_all(last_snapshot):
                    event_stream.write(json.dumps(event.transport_dict(), ensure_ascii=False) + "\n")
                    if client:
                        client.send(event)
                trip_finished = True
    finally:
        _stop_poll.set()
        road_executor.shutdown(wait=True, cancel_futures=True)
        media_executor.shutdown(wait=True, cancel_futures=False)
        if media_future is not None:
            try:
                media_future.result()
            except Exception as exc:
                print(f"Dashboard stream final warning: {exc}", file=sys.stderr)
        if client:
            if trip_finished:
                try:
                    client.complete_trip(dataset.trip_id)
                except Exception as exc:
                    print(f"Trip completion warning: {exc}", file=sys.stderr)
            client.close()
        driver.close()
        if capture is not None:
            capture.release()
        cv2.destroyAllWindows()

    if args.output_csv:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.output_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    print(f"{dataset.trip_id}: {processed} hybrid frames; events={args.events}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
