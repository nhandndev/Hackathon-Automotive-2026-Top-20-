"""Run the DMS pipeline on a laptop webcam and show/record driver_state."""
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

from core.challenge2_driver.predict_state import DriverStatePredictor
from core.challenge2_driver.driver_profile import (
    DriverProfile,
    ProfileStore,
    validate_driver_id,
)
from core.challenge2_driver.driver_enrollment import GuidedEnrollment
from core.runtime.model_registry import resolve_driver_model


def overlay(frame, output, mirror=True):
    canvas = cv2.flip(frame, 1) if mirror else frame.copy()
    state = output["driver_state"]
    color = (30, 210, 30) if state == "alert" else (0, 180, 255) if state in {"yawning", "drowsy"} else (30, 30, 240)
    rows = [
        f"DRIVER STATE: {state.upper()}",
        f"source: {output['prediction_source']}",
        f"driver: {output.get('driver_id') or 'session-only'}",
        f"confidence: {output['state_confidence']:.2f}",
        f"rule state: {output['rule_driver_state']}",
        f"alertness: {output['alertness_score']:.2f}",
        f"attention: {output['attention_state']}",
        f"eye: {output['eye_state']} / {output['eye_event']}",
        f"mouth: {output['mouth_state']} / {output['mouth_event']}",
        f"head: {output['head_state']}",
        f"quality: {output['observation']['quality_status']}",
    ]
    panel_height = 43 + len(rows) * 25
    cv2.rectangle(canvas, (12, 12), (500, panel_height), (15, 15, 15), -1)
    for i, text in enumerate(rows):
        cv2.putText(canvas, text, (25, 43 + i * 25), cv2.FONT_HERSHEY_SIMPLEX,
                    .64 if i == 0 else .53, color if i == 0 else (235, 235, 235), 2 if i == 0 else 1)
    cv2.putText(canvas, "Q/ESC: quit | R: reset calibration", (15, canvas.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, .5, (220, 220, 220), 1)
    return canvas


def _draw_mirrored_box(canvas, box, label, color):
    if not box or len(box) != 4:
        return
    width = canvas.shape[1]
    x1, y1, x2, y2 = (int(value) for value in box)
    mirrored_x1 = width - 1 - x2
    mirrored_x2 = width - 1 - x1
    cv2.rectangle(
        canvas, (mirrored_x1, y1), (mirrored_x2, y2), color, 2
    )
    cv2.putText(
        canvas,
        label,
        (mirrored_x1, max(18, y1 - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        color,
        1,
    )


def enrollment_overlay(frame, output, status):
    canvas = cv2.flip(frame, 1)
    boxes = output.get("visualization", {})

    cv2.rectangle(canvas, (20, 20), (830, 300), (15, 15, 15), -1)
    cv2.putText(
        canvas,
        (
            "DRIVER PROFILE ENROLLMENT  "
            f"[{status.step_number}/{status.total_steps}]"
        ),
        (35, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 210, 255),
        2,
    )
    cv2.putText(
        canvas,
        status.step.prompt,
        (35, 92),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        (240, 240, 240),
        2,
    )
    features = output.get("features", {})
    cv2.putText(
        canvas,
        (
            f"EAR {features.get('ear_robust', 0):.3f}   "
            f"MAR {features.get('mar', 0):.3f}   "
            f"Yaw {features.get('raw_yaw_deg', 0):.1f}   "
            f"Pitch {features.get('raw_pitch_deg', 0):.1f}"
        ),
        (35, 125),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (220, 220, 220),
        1,
    )
    cv2.putText(
        canvas,
        (
            f"Valid samples: {status.valid_samples}/"
            f"{status.step.minimum_samples}   "
            f"Hold: {status.elapsed_ms / 1000:.1f}/"
            f"{status.step.minimum_duration_ms / 1000:.1f}s"
        ),
        (35, 153),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (220, 220, 220),
        1,
    )
    action_text = (
        "ACTION DETECTED"
        if status.action_detected
        else "ACTION NOT DETECTED"
    )
    action_color = (
        (30, 240, 80) if status.action_detected else (30, 30, 255)
    )
    cv2.putText(
        canvas,
        action_text,
        (35, 184),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        action_color,
        2,
    )
    cv2.putText(
        canvas,
        status.evidence,
        (275, 184),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        action_color,
        1,
    )
    width = 740
    cv2.rectangle(canvas, (35, 210), (35 + width, 228), (70, 70, 70), -1)
    cv2.rectangle(
        canvas,
        (35, 210),
        (
            35 + int(width * max(0.0, min(1.0, status.progress))),
            228,
        ),
        (30, 200, 80),
        -1,
    )
    ready_text = (
        "READY - SPACE accepts this feature and moves NEXT"
        if status.ready
        else "NOT READY - SPACE clears this attempt and RETRIES"
    )
    ready_color = (30, 240, 80) if status.ready else (0, 190, 255)
    cv2.putText(
        canvas,
        ready_text,
        (35, 272),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        ready_color,
        2,
    )
    focus = status.step.key
    eye_color = (
        (30, 30, 255)
        if focus in {"blink", "closed"}
        else (255, 200, 30)
    )
    mouth_color = (
        (30, 30, 255)
        if focus in {"mouth", "yawn"}
        else (30, 180, 255)
    )
    face_color = (
        (30, 30, 255)
        if focus in {"neutral", "left", "right", "down"}
        else (40, 220, 40)
    )
    _draw_mirrored_box(
        canvas, boxes.get("face_bbox"), "FACE", face_color
    )
    _draw_mirrored_box(
        canvas, boxes.get("left_eye_bbox"), "EYE", eye_color
    )
    _draw_mirrored_box(
        canvas, boxes.get("right_eye_bbox"), "EYE", eye_color
    )
    _draw_mirrored_box(
        canvas, boxes.get("mouth_bbox"), "MOUTH", mouth_color
    )
    cv2.putText(
        canvas,
        "Q/ESC: cancel",
        (20, canvas.shape[0] - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (230, 230, 230),
        1,
    )
    return canvas


def enroll_driver(
    capture,
    config: dict,
    driver_id: str,
    store: ProfileStore,
) -> DriverProfile:
    """Run guided enrollment; only numeric primitives are persisted."""
    from core.challenge2_driver.dms_core import DMSCore
    guide = GuidedEnrollment(driver_id)
    engine = DMSCore(config)
    started = time.perf_counter_ns()
    frame_id = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError("Webcam stopped during enrollment")
            timestamp_ms = (time.perf_counter_ns() - started) // 1_000_000
            output = engine.process(frame, frame_id, timestamp_ms)
            status = guide.status(timestamp_ms)
            if status.step is None:
                break
            guide.observe(output, timestamp_ms)
            status = guide.status(timestamp_ms)
            cv2.imshow(
                "FPTU DMS - Driver Enrollment",
                enrollment_overlay(frame, output, status),
            )
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                raise RuntimeError("Driver enrollment was cancelled")
            if key == ord(" "):
                if guide.advance(timestamp_ms):
                    print(
                        f"Accepted enrollment feature: {status.step.key}"
                    )
                else:
                    print(
                        f"Retrying enrollment feature: {status.step.key} "
                        f"({status.evidence})"
                    )
                    guide.retry_current(timestamp_ms)
            frame_id += 1
    finally:
        engine.close()
        try:
            cv2.destroyWindow("FPTU DMS - Driver Enrollment")
        except cv2.error:
            pass
    threshold = float(
        config["eye"].get(
            "closure_threshold_ratio",
            0.72,
        )
    )
    try:
        profile = guide.build_profile(threshold)
    except ValueError as exc:
        raise RuntimeError(
            "Enrollment finished collecting samples but "
            f"profile validation failed: {exc}. "
            "Please run --enroll again."
        ) from exc
        
    path = store.save(profile)
    print(
        f"Saved driver profile {driver_id} "
        f"(quality={profile.quality_score:.2f}) to {path}"
    )
    print("\nEnrollment diagnostics:")
    diag = guide.diagnostics()
    for k, v in diag.items():
        print(f"  {k:<17}: {v}")
    print()
    return profile


def main():
    parser = argparse.ArgumentParser(description="Real-time laptop-webcam Driver Monitoring System")
    parser.add_argument("--camera", type=int, default=None)
    parser.add_argument(
        "--config",
        type=Path,
        default=AI_ROOT / "configs" / "challenge2.yaml",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Override the Challenge-2 registry production model",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=AI_ROOT / "artifacts" / "webcam_driver_state.jsonl",
    )
    parser.add_argument(
        "--driver-id",
        help="Validated ID used to load/create a non-biometric driver profile",
    )
    parser.add_argument(
        "--profiles-dir",
        type=Path,
        default=AI_ROOT / "artifacts" / "driver_profiles",
    )
    parser.add_argument(
        "--enroll",
        action="store_true",
        help="Force guided enrollment even when this Driver ID exists",
    )
    parser.add_argument("--no-display", action="store_true", help="Process without an OpenCV window")
    parser.add_argument("--max-frames", type=int, default=0, help="0 means unlimited")
    args = parser.parse_args()
    if args.enroll and not args.driver_id:
        parser.error("--enroll requires --driver-id")
    if args.driver_id:
        try:
            validate_driver_id(args.driver_id)
        except ValueError as exc:
            parser.error(str(exc))
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    camera_index = config["camera"]["index"] if args.camera is None else args.camera
    capture = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, config["camera"]["width"])
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config["camera"]["height"])
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open webcam index {camera_index}. Try --camera 1.")
    profile = None
    profile_store = ProfileStore(args.profiles_dir)
    if args.driver_id:
        if args.enroll or not profile_store.exists(args.driver_id):
            if args.enroll:
                if args.no_display:
                    parser.error(
                        "A missing/forced profile requires the enrollment window"
                    )
                profile = enroll_driver(
                    capture, config, args.driver_id, profile_store
                )
            else:
                raise FileNotFoundError(
                    f"Driver profile '{args.driver_id}' not found. Run webcam_driver_demo.py --driver-id {args.driver_id} --enroll first."
                )
        else:
            try:
                profile = profile_store.load(args.driver_id)
            except ValueError as exc:
                if args.no_display:
                    raise RuntimeError(
                        f"Driver profile is invalid: {exc}"
                    ) from exc
                print(f"Profile cannot be reused ({exc}); enrolling again")
                profile = enroll_driver(
                    capture, config, args.driver_id, profile_store
                )
            else:
                print(
                    f"Driver profile: {profile.driver_id} "
                    f"(quality={profile.quality_score:.2f})"
                )
    else:
        print("Driver profile: GLOBAL")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        resolved_model = resolve_driver_model(AI_ROOT, args.model)
    except Exception as exc:
        print(f"Model resolver error: {exc}", file=sys.stderr)
        return 1
    predictor = DriverStatePredictor(resolved_model, args.config, profile)

    active_providers = predictor._engine.face_landmarker.session.get_providers()
    print("\nChallenge 2 model:")
    print(f"  artifact: {resolved_model.name}")
    print(f"  architecture: {predictor.architecture}")
    print("Driver:")
    print(f"  id: {profile.driver_id if profile else 'GLOBAL'}")
    print(f"  personalization: {'ACTIVE' if profile is not None else 'SESSION'}")
    print("Runtime:")
    print(f"  ONNX provider: {active_providers[0] if active_providers else 'None'}")
    print("  RF backend: sklearn CPU\n")
        
    started = time.perf_counter_ns()
    frame_id = 0
    try:
        with args.output.open("w", encoding="utf-8") as stream:
            while True:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Webcam stopped returning frames.")
                timestamp_ms = (time.perf_counter_ns() - started) // 1_000_000
                
                output = predictor.predict_frame(frame_id, timestamp_ms, frame)
                output["driver_id"] = profile.driver_id if profile else None
                output["profile_quality"] = profile.quality_score if profile else None
                    
                stream.write(json.dumps(output, ensure_ascii=False) + "\n")
                stream.flush()
                if not args.no_display:
                    cv2.imshow("FPTU DMS - Laptop Webcam", overlay(frame, output))
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


if __name__ == "__main__":
    main()
