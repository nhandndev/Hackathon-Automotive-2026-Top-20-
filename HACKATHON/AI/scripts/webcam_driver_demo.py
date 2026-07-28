"""Real-time cabin-camera demo using the production DriverStatePredictor."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import yaml

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

from core.challenge2_driver import DriverStatePredictor  # noqa: E402


def overlay(frame, result):
    canvas = cv2.flip(frame, 1)
    state = str(result["state"])
    color = (
        (30, 210, 30)
        if state == "alert"
        else (0, 180, 255)
        if state in {"yawning", "drowsy"}
        else (30, 30, 240)
    )
    rows = [
        f"DRIVER STATE: {state.upper()}",
        f"confidence: {result['confidence']:.2f}",
        f"rule state: {result['rule_state']}",
        f"alertness: {result['alertness_score']:.2f}",
        f"eye: {result['eye_state']}",
        f"mouth: {result['mouth_state']}",
        f"head: {result['head_pose']}",
        f"quality: {result['quality_status']}",
    ]
    cv2.rectangle(
        canvas, (12, 12), (500, 50 + 25 * len(rows)), (15, 15, 15), -1
    )
    for index, text in enumerate(rows):
        cv2.putText(
            canvas,
            text,
            (25, 43 + index * 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.64 if index == 0 else 0.53,
            color if index == 0 else (235, 235, 235),
            2 if index == 0 else 1,
        )
    cv2.putText(
        canvas,
        "Q/ESC: quit | R: reset",
        (15, canvas.shape[0] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (220, 220, 220),
        1,
    )
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser(description="Challenge 2 webcam demo")
    parser.add_argument("--camera", type=int)
    parser.add_argument(
        "--config",
        type=Path,
        default=AI_ROOT / "configs" / "challenge2.yaml",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=AI_ROOT / "models" / "driver_state_rf.joblib",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=AI_ROOT / "artifacts" / "webcam_driver_state.jsonl",
    )
    parser.add_argument("--max-frames", type=int, default=0)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    camera_index = (
        int(config["camera"]["index"])
        if args.camera is None
        else args.camera
    )
    capture = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, config["camera"]["width"])
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config["camera"]["height"])
    if not capture.isOpened():
        raise RuntimeError(
            f"Cannot open webcam index {camera_index}; try --camera 1"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    predictor = DriverStatePredictor(args.model, args.config)
    started = time.perf_counter_ns()
    frame_id = 0
    try:
        with args.output.open("w", encoding="utf-8") as stream:
            while True:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Webcam stopped returning frames")
                timestamp_ms = (
                    time.perf_counter_ns() - started
                ) // 1_000_000
                result = predictor.predict_frame(
                    frame_id, timestamp_ms, frame
                )
                stream.write(json.dumps({
                    "frame_id": frame_id,
                    "timestamp_ms": timestamp_ms,
                    **result,
                }, ensure_ascii=False, default=str) + "\n")
                stream.flush()
                cv2.imshow(
                    "FPTU DMS Vision - Driver Camera",
                    overlay(frame, result),
                )
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("r"):
                    predictor.reset()
                    started = time.perf_counter_ns()
                frame_id += 1
                if args.max_frames and frame_id >= args.max_frames:
                    break
    finally:
        predictor.close()
        capture.release()
        cv2.destroyAllWindows()
    print(f"Wrote {frame_id} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
