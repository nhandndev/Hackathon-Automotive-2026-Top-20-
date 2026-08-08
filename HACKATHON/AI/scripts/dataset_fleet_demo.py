"""Replay every valid BTC-style trip in a folder as one fleet demo session.

Trips are registered together so the Dashboard can show the whole fleet.  AI
inference runs sequentially to keep GPU/RAM usage bounded; Backend keeps each
completed trip's latest frames, timeline and DecisionEvents.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import time
import threading
import concurrent.futures
from pathlib import Path

import cv2
import numpy as np
import yaml

AI_ROOT = Path(__file__).resolve().parents[1]
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))

from core.btc_trip import TripDataset  # noqa: E402
from integrations.se_client import SEApiClient  # noqa: E402
from core.runtime.model_registry import resolve_driver_model
from core.runtime.demo_engine import DemoInferenceEngine
from core.challenge1_road.predict_ttc import format_ttc
from scripts.trip_visual_demo import (
    CSV_FIELDS, draw_dashboard, draw_face, draw_right, draw_road,
    project_kitti_labels, InterventionOverlayState, _poll_interventions,
    draw_intervention_overlay,
)

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
        default=None,
        help="Challenge-2 Random Forest .joblib artifact",
    )
    parser.add_argument(
        "--road-config", type=Path, default=AI_ROOT / "configs" / "challenge1.yaml"
    )
    parser.add_argument(
        "--driver-config", type=Path, default=AI_ROOT / "configs" / "challenge2.yaml"
    )
    parser.add_argument(
        "--decision-config", type=Path, default=AI_ROOT / "configs" / "decision_engine.yaml"
    )
    parser.add_argument(
        "--runtime-config", type=Path, default=AI_ROOT / "configs" / "runtime_demo.yaml"
    )
    parser.add_argument(
        "--runtime-mode", choices=("auto", "fixed", "full"), default="auto"
    )
    parser.add_argument(
        "--target-fps", type=float, default=20.0
    )
    parser.add_argument(
        "--dashboard-stream-fps",
        type=float,
        default=5.0,
        help="JPEG/snapshot publish rate to Fleet Dashboard; 0 disables live media",
    )
    parser.add_argument(
        "--road-interval-ms", type=int, default=150
    )
    parser.add_argument(
        "--driver-interval-ms", type=int, default=75
    )
    parser.add_argument(
        "--fleet-execution-mode", choices=("shared", "subprocess"), default="shared"
    )
    
    # legacy fallbacks
    parser.add_argument(
        "--road-inference-interval", type=int, default=5,
    )
    parser.add_argument(
        "--face-detector-interval", type=int, default=10,
    )
    args = parser.parse_args()
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

    # Resolve model path
    try:
        driver_model_path = resolve_driver_model(AI_ROOT, args.driver_model)
    except Exception as e:
        print(f"Model resolver error: {e}", file=sys.stderr)
        return 1

    # Register trips to fleet dashboard
    se_endpoint = args.se_endpoint
    if se_endpoint:
        client = SEApiClient(
            se_endpoint,
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
            print("Fleet registered:", ", ".join(trip.trip_id for trip in trips))
        except Exception as e:
            print(f"[WARNING] SE backend registration failed: {e}. Running offline.")
            se_endpoint = None
        finally:
            client.close()
            
    # Resolve se_endpoint in arguments for engine
    se_endpoint_engine = se_endpoint
    
    if args.fleet_execution_mode == "shared":
        # Shared process execution mode (Section 68)
        engine = DemoInferenceEngine(
            driver_model_path=driver_model_path,
            road_config_path=args.road_config,
            driver_config_path=args.driver_config,
            decision_config_path=args.decision_config,
            runtime_config_path=args.runtime_config,
            runtime_mode=args.runtime_mode,
            road_interval_ms=args.road_interval_ms,
            driver_interval_ms=args.driver_interval_ms,
            target_fps=args.target_fps,
            se_endpoint=se_endpoint_engine
        )
        
        first_trip = True
        media_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        media_future = None
        try:
            for index, trip in enumerate(trips, start=1):
                print(f"\n[{index}/{len(trips)}] Replay {trip.trip_id}")
                
                csv_path = args.output_dir / f"{trip.trip_id}.csv"
                event_path = args.output_dir / f"{trip.trip_id}.events.jsonl"
                event_path.parent.mkdir(parents=True, exist_ok=True)
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                
                engine.start_trip(trip.trip_id, trip.load_calibration(), trip.metadata, speed_limit_kmh=None, trip_dir=trip.trip_dir)
                if first_trip:
                    engine.warmup_benchmark(trip, frames_count=8)
                    first_trip = False
                    # Restart trip officially
                    engine.start_trip(trip.trip_id, trip.load_calibration(), trip.metadata, speed_limit_kmh=None, trip_dir=trip.trip_dir)
                
                rows = []
                processed = 0
                records = list(trip.iter_frames())
                source_index = 0
                fps = float(trip.metadata.get("fps", args.target_fps) or args.target_fps)
                next_frame_due = time.perf_counter()
                next_dashboard_publish_ms = 0.0
                ai_alert_event = None
                ai_alert_expires = 0.0
                intervention_overlay = InterventionOverlayState()
                intervention_stop = threading.Event()
                intervention_thread = threading.Thread(
                    target=_poll_interventions,
                    args=(
                        intervention_overlay,
                        trip.trip_id,
                        intervention_stop,
                        args.se_endpoint.rstrip("/") + "/interventions/pending",
                    ),
                    daemon=True,
                )
                intervention_thread.start()
                
                try:
                    with event_path.open("w", encoding="utf-8") as event_stream:
                        while source_index < len(records):
                            frame = records[source_index]

                            cabin = trip.load_driver(frame.frame_id)
                            left_frame = trip.load_left(frame.frame_id)
                            right_frame = trip.load_right(frame.frame_id)

                            res = engine.process_display_frame(
                                frame_id=frame.frame_id,
                                timestamp=frame.timestamp,
                                speed_kmh=frame.speed_kmh,
                                longitudinal_accel=frame.longitudinal_accel,
                                lateral_accel=frame.lateral_accel,
                                cabin_frame=cabin,
                                left_frame=left_frame,
                                right_frame=right_frame,
                            )

                            cached_ttc = res["cached_ttc"]
                            cached_road_debug = res["cached_road_debug"]
                            cached_driver_out = res["cached_driver_out"]
                            fleet_out = res["fleet_out"]
                            events_fired = res["events_fired"]
                            last_snapshot = res["last_snapshot"]
                            live_timestamp_ms = res["live_timestamp_ms"]

                            for ev in events_fired:
                                ai_alert_event = ev
                                ai_alert_expires = time.perf_counter() + 3.0
                                event_stream.write(json.dumps(ev.transport_dict(), ensure_ascii=False) + "\n")
                                event_stream.flush()

                            rows.append({
                                "frame_id": frame.frame_id,
                                "timestamp": f"{frame.timestamp:.3f}",
                                "predicted_ttc": format_ttc(cached_ttc),
                                "predicted_driver_state": cached_driver_out["state"],
                                "predicted_risk_score": fleet_out.risk_score,
                            })

                            annotated_cabin = None
                            annotated_road = None
                            should_publish = (
                                engine.client is not None
                                and args.dashboard_stream_fps > 0
                                and live_timestamp_ms >= next_dashboard_publish_ms
                                and (media_future is None or media_future.done())
                            )
                            if should_publish or not args.no_display:
                                annotated_cabin = draw_face(cabin, cached_driver_out)
                                annotations = (
                                    []
                                    if cached_road_debug.get("objects")
                                    else project_kitti_labels(
                                        trip, frame.frame_id, left_frame.shape
                                    )
                                )
                                annotated_road = draw_road(
                                    left_frame,
                                    cached_ttc,
                                    cached_road_debug,
                                    annotations,
                                )

                            if should_publish and annotated_cabin is not None and annotated_road is not None:
                                cabin_ok, cabin_jpeg = cv2.imencode(
                                    ".jpg",
                                    annotated_cabin,
                                    [cv2.IMWRITE_JPEG_QUALITY, 78],
                                )
                                road_ok, road_jpeg = cv2.imencode(
                                    ".jpg",
                                    annotated_road,
                                    [cv2.IMWRITE_JPEG_QUALITY, 78],
                                )
                                if cabin_ok and road_ok:
                                    media_future = media_executor.submit(
                                        engine.client.send_live_update,
                                        cabin_jpeg=cabin_jpeg.tobytes(),
                                        road_jpeg=road_jpeg.tobytes(),
                                        snapshot=last_snapshot.model_dump(mode="json"),
                                    )
                                next_dashboard_publish_ms = (
                                    live_timestamp_ms + 1000.0 / args.dashboard_stream_fps
                                )

                            if media_future is not None and media_future.done():
                                try:
                                    media_future.result()
                                except Exception as exc:
                                    print(
                                        f"[WARNING] Dashboard live publish failed: {exc}. "
                                        "Continuing offline for media."
                                    )
                                    media_future = None
                                    next_dashboard_publish_ms = live_timestamp_ms + 1000.0

                            if not args.no_display:
                                canvas = np.vstack([
                                    np.hstack([annotated_road, draw_right(trip.load_right(frame.frame_id))]),
                                    np.hstack([annotated_cabin, draw_dashboard(trip.trip_id, frame, cached_ttc, cached_driver_out, fleet_out.risk_score, args.speed, False)]),
                                ])
                                if ai_alert_event and time.perf_counter() < ai_alert_expires:
                                    cw, ch = canvas.shape[1], canvas.shape[0]
                                    box_w, box_h = 600, 160
                                    x1, y1 = (cw - box_w) // 2, (ch - box_h) // 2 - 40
                                    color = (40, 40, 255) if ai_alert_event.severity == "critical" else (0, 140, 255)
                                    overlay = canvas.copy()
                                    cv2.rectangle(overlay, (x1, y1), (x1 + box_w, y1 + box_h), color, -1)
                                    cv2.rectangle(overlay, (x1, y1), (x1 + box_w, y1 + box_h), (200, 200, 200), 3)
                                    cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)
                                    alert_title = f"AI DECISION: {ai_alert_event.alert_type.replace('_', ' ').upper()}"
                                    text_size = cv2.getTextSize(alert_title, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 3)[0]
                                    cv2.putText(canvas, alert_title, (x1 + (box_w - text_size[0]) // 2, y1 + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 3, cv2.LINE_AA)
                                    action_text = ai_alert_event.recommended_action or ""
                                    text_size2 = cv2.getTextSize(action_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                                    cv2.putText(canvas, action_text, (x1 + (box_w - text_size2[0]) // 2, y1 + 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2, cv2.LINE_AA)
                                active_cmd = intervention_overlay.get_active()
                                if active_cmd is not None:
                                    canvas = draw_intervention_overlay(
                                        canvas,
                                        active_cmd,
                                        intervention_overlay.remaining(),
                                    )
                                cv2.imshow("FLEET TRIP REPLAY", canvas)
                                wait_ms = max(1, int((next_frame_due - time.perf_counter()) * 1000))
                                key = cv2.waitKey(wait_ms) & 0xFF
                                if key in (ord("q"), 27):
                                    break
                                if key in (ord("c"), ord("C")):
                                    intervention_overlay.clear()
                                    ai_alert_expires = 0.0

                            processed += 1
                            realtime_pacing = not args.no_display or engine.client is not None
                            if realtime_pacing:
                                frame_period = 1.0 / (fps * args.speed)
                                next_frame_due += frame_period
                                remaining = next_frame_due - time.perf_counter()
                                if remaining > 0:
                                    time.sleep(remaining)

                            if args.max_frames and processed >= args.max_frames:
                                break

                            source_index += 1
                            if realtime_pacing:
                                frame_period = 1.0 / (fps * args.speed)
                                behind = time.perf_counter() - next_frame_due
                                if behind >= frame_period:
                                    skipped = min(int(behind / frame_period), len(records) - source_index)
                                    source_index += skipped
                                    next_frame_due += skipped * frame_period

                        engine.end_trip(event_stream)
                finally:
                    intervention_stop.set()
                    intervention_overlay.clear()
                    
                with csv_path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
                    writer.writeheader()
                    writer.writerows(rows)
        finally:
            media_executor.shutdown(wait=True, cancel_futures=False)
            engine.close()
            cv2.destroyAllWindows()
            
    else:
        # Subprocess execution mode fallback
        runner = Path(__file__).with_name("end_to_end_demo.py")
        for index, trip in enumerate(trips, start=1):
            print(f"\n[{index}/{len(trips)}] Replay {trip.trip_id}")
            command = [
                sys.executable,
                str(runner),
                "--trip-dir", str(trip.trip_dir),
                "--driver-source", "dataset",
                "--driver-model", str(driver_model_path),
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
