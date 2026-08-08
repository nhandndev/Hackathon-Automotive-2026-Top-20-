"""Hybrid product demo: BTC road/telemetry + live driver webcam with Hardware Adaptive Inference.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from pathlib import Path
import threading
import concurrent.futures

import cv2
import numpy as np
import yaml

AI_ROOT = Path(__file__).resolve().parents[1]
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))

from core.btc_trip import TripDataset
from core.challenge1_road.predict_ttc import format_ttc
from core.challenge2_driver.driver_profile import ProfileStore
from core.runtime.model_registry import resolve_driver_model
from core.runtime.demo_engine import DemoInferenceEngine
from core.runtime.paths import resolve_csv_output
from scripts.trip_visual_demo import (
    CSV_FIELDS, WINDOW_NAME, draw_dashboard, draw_face, draw_right, draw_road,
    project_kitti_labels, InterventionOverlayState, _poll_interventions, draw_intervention_overlay,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="End-to-end demo using BTC road cameras and a live webcam"
    )
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--driver-source", choices=("webcam", "dataset"), default="webcam")
    parser.add_argument("--driver-id")
    parser.add_argument("--profiles-dir", type=Path, default=AI_ROOT / "artifacts" / "driver_profiles")
    parser.add_argument("--road-config", type=Path, default=AI_ROOT / "configs" / "challenge1.yaml")
    parser.add_argument("--driver-config", type=Path, default=AI_ROOT / "configs" / "challenge2.yaml")
    parser.add_argument("--driver-model", type=Path, default=None)
    parser.add_argument("--decision-config", type=Path, default=AI_ROOT / "configs" / "decision_engine.yaml")
    parser.add_argument("--runtime-config", type=Path, default=AI_ROOT / "configs" / "runtime_demo.yaml")
    
    parser.add_argument("--runtime-mode", choices=("auto", "fixed", "full"), default="auto")
    parser.add_argument("--road-interval-ms", type=int, default=150)
    parser.add_argument("--driver-interval-ms", type=int, default=75)
    parser.add_argument("--target-fps", type=float, default=20.0)

    parser.add_argument("--se-endpoint")
    parser.add_argument("--speed-limit-kmh", type=float)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--dashboard-stream-fps", type=float, default=5.0)
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--events", type=Path, default=AI_ROOT / "artifacts" / "decision_events" / "live.events.jsonl")
    
    # legacy fallbacks
    parser.add_argument("--road-inference-interval", type=int, default=5)
    parser.add_argument("--face-detector-interval", type=int, default=10)
    
    args = parser.parse_args()
    return args

def main() -> int:
    args = parse_args()
    dataset = TripDataset(args.trip_dir.resolve())
    
    # Resolve model path
    try:
        driver_model_path = resolve_driver_model(AI_ROOT, args.driver_model)
    except Exception as e:
        print(f"Model resolver error: {e}", file=sys.stderr)
        return 1
        
    profile = None
    if args.driver_id:
        store = ProfileStore(args.profiles_dir)
        if not store.exists(args.driver_id):
            print(f"Driver profile '{args.driver_id}' does not exist.")
            print("Run webcam_driver_demo.py --enroll first.")
            return 1
        profile = store.load(args.driver_id)

    # Initialize shared DemoInferenceEngine
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
        se_endpoint=args.se_endpoint,
        driver_profile=profile
    )
    
    speed_limit = float(args.speed_limit_kmh) if args.speed_limit_kmh is not None else float(dataset.metadata["speed_limit_kmh"])
    
    print("\n[Startup] Running Warmup benchmark...")
    engine.start_trip(dataset.trip_id, dataset.load_calibration(), dataset.metadata, speed_limit_kmh=speed_limit, trip_dir=dataset.trip_dir)
    engine.warmup_benchmark(dataset, frames_count=8)
    
    # Restart trip officially
    engine.start_trip(dataset.trip_id, dataset.load_calibration(), dataset.metadata, speed_limit_kmh=speed_limit, trip_dir=dataset.trip_dir)
    
    capture = None
    if args.driver_source == "webcam":
        capture = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
        
    args.events.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    last_snapshot = None
    processed = 0
    paused = False
    fps = float(dataset.metadata.get("fps", args.target_fps) or args.target_fps)
    
    media_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    media_future = None
    next_dashboard_publish_ms = 0.0
    trip_finished = False
    
    ai_alert_event = None
    ai_alert_expires = 0.0

    intervention_overlay = InterventionOverlayState()
    _stop_poll = threading.Event()
    intervention_endpoint = args.se_endpoint.rstrip("/") + "/interventions/pending"
    _poll_thread = threading.Thread(
        target=_poll_interventions,
        args=(intervention_overlay, dataset.trip_id, _stop_poll, intervention_endpoint),
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
                else:
                    cabin = dataset.load_driver(frame.frame_id)
                    
                left_frame = dataset.load_left(frame.frame_id)
                right_frame = dataset.load_right(frame.frame_id)
                
                # Execute engine
                res = engine.process_display_frame(
                    frame_id=frame.frame_id,
                    timestamp=frame.timestamp,
                    speed_kmh=frame.speed_kmh,
                    longitudinal_accel=frame.longitudinal_accel,
                    lateral_accel=frame.lateral_accel,
                    cabin_frame=cabin,
                    left_frame=left_frame,
                    right_frame=right_frame
                )
                
                cached_ttc = res["cached_ttc"]
                cached_road_debug = res["cached_road_debug"]
                cached_driver_out = res["cached_driver_out"]
                fleet_out = res["fleet_out"]
                last_snapshot = res["last_snapshot"]
                events_fired = res["events_fired"]
                road_confirmed = res["road_confirmed"]
                live_timestamp_ms = res["live_timestamp_ms"]
                
                for event in events_fired:
                    ai_alert_event = event
                    ai_alert_expires = time.perf_counter() + 3.0
                    event_stream.write(json.dumps(event.transport_dict(), ensure_ascii=False) + "\n")
                    event_stream.flush()

                # Process state updates using caches
                annotated_cabin = draw_face(cabin, cached_driver_out)
                
                left = dataset.load_left(frame.frame_id)
                annotations = [] if cached_road_debug.get("objects") else project_kitti_labels(dataset, frame.frame_id, left.shape)
                annotated_road = draw_road(left, cached_ttc, cached_road_debug, annotations)
                
                # Async Media Publishing
                if engine.client and args.dashboard_stream_fps > 0 and live_timestamp_ms >= next_dashboard_publish_ms and (media_future is None or media_future.done()):
                    cabin_ok, cabin_jpeg = cv2.imencode(".jpg", annotated_cabin, [cv2.IMWRITE_JPEG_QUALITY, 78])
                    road_ok, road_jpeg = cv2.imencode(".jpg", annotated_road, [cv2.IMWRITE_JPEG_QUALITY, 78])
                    if cabin_ok and road_ok:
                        media_future = media_executor.submit(
                            engine.client.send_live_update, cabin_jpeg=cabin_jpeg.tobytes(), road_jpeg=road_jpeg.tobytes(),
                            snapshot=last_snapshot.model_dump(mode="json")
                        )
                    next_dashboard_publish_ms = live_timestamp_ms + 1000.0 / args.dashboard_stream_fps

                rows.append({
                    "frame_id": frame.frame_id, "timestamp": f"{frame.timestamp:.3f}",
                    "predicted_ttc": format_ttc(cached_ttc), "predicted_driver_state": cached_driver_out["state"],
                    "predicted_risk_score": fleet_out.risk_score,
                })
                
                canvas = np.vstack([
                    np.hstack([annotated_road, draw_right(dataset.load_right(frame.frame_id))]),
                    np.hstack([annotated_cabin, draw_dashboard(dataset.trip_id, frame, cached_ttc, cached_driver_out, fleet_out.risk_score, args.speed, paused)]),
                ])

                # Overlay Perf Stats
                perf_text = f"UI {engine.scheduler.get_display_fps():.1f} FPS | C1 {1000/max(1, engine.scheduler.road.interval_ms):.1f} Hz | C2 {1000/max(1, engine.scheduler.driver.interval_ms):.1f} Hz | {args.runtime_mode.upper()}"
                cv2.putText(canvas, perf_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                if ai_alert_event and time.perf_counter() < ai_alert_expires:
                    cw, ch = canvas.shape[1], canvas.shape[0]
                    box_w, box_h = 600, 160
                    x1, y1 = (cw - box_w) // 2, (ch - box_h) // 2 - 40
                    color = (40, 40, 255) if ai_alert_event.severity == "critical" else (0, 140, 255)
                    overlay = canvas.copy()
                    cv2.rectangle(overlay, (x1, y1), (x1+box_w, y1+box_h), color, -1)
                    cv2.rectangle(overlay, (x1, y1), (x1+box_w, y1+box_h), (200, 200, 200), 3)
                    cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)
                    alert_title = f"AI DECISION: {ai_alert_event.alert_type.replace('_', ' ').upper()}"
                    text_size = cv2.getTextSize(alert_title, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 3)[0]
                    cv2.putText(canvas, alert_title, (x1 + (box_w - text_size[0]) // 2, y1 + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 3, cv2.LINE_AA)
                    action_text = ai_alert_event.recommended_action or ""
                    text_size2 = cv2.getTextSize(action_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                    cv2.putText(canvas, action_text, (x1 + (box_w - text_size2[0]) // 2, y1 + 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2, cv2.LINE_AA)
                
                active_cmd = intervention_overlay.get_active()
                if active_cmd is not None:
                    canvas = draw_intervention_overlay(canvas, active_cmd, intervention_overlay.remaining())
                
                processed += 1
                realtime_pacing = not args.no_display or engine.client is not None
                if realtime_pacing:
                    frame_period = 1.0 / (fps * args.speed)
                    next_frame_due += frame_period
                    
                if not args.no_display:
                    cv2.imshow(WINDOW_NAME + " - LIVE DRIVER", canvas)
                    wait_ms = max(1, int((next_frame_due - time.perf_counter()) * 1000))
                    key = cv2.waitKey(wait_ms) & 0xFF
                    if key in (ord("q"), 27): break
                    if key in (ord("+"), ord("=")):
                        args.speed = min(8.0, args.speed * 2.0)
                        next_frame_due = time.perf_counter()
                    elif key in (ord("-"), ord("_")):
                        args.speed = max(0.25, args.speed / 2.0)
                        next_frame_due = time.perf_counter()
                    elif key in (ord("c"), ord("C")):
                        intervention_overlay.clear()
                        ai_alert_expires = 0.0
                elif realtime_pacing:
                    remaining = next_frame_due - time.perf_counter()
                    if remaining > 0: time.sleep(remaining)
                
                if args.max_frames and processed >= args.max_frames: break
                
                source_index += 1
                if realtime_pacing:
                    frame_period = 1.0 / (fps * args.speed)
                    behind = time.perf_counter() - next_frame_due
                    if behind >= frame_period:
                        skipped = min(int(behind / frame_period), len(records) - source_index)
                        source_index += skipped
                        next_frame_due += skipped * frame_period

            engine.end_trip(event_stream)
            trip_finished = True
    finally:
        _stop_poll.set()
        intervention_overlay.clear()
        media_executor.shutdown(wait=True, cancel_futures=False)
        engine.close()
        if capture is not None: capture.release()
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
