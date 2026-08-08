"""Visual three-camera BTC trip inference for Challenges 1, 2 and 3.

The demo consumes exactly one organizer trip. It uses the same production
predictors as run_inference.py, then renders their diagnostics without feeding
any visualization data back into the predictions.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
import threading
import urllib.request
import urllib.error
import json
import winsound
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

from core.challenge1_road.predict_ttc import (  # noqa: E402
    RoadTTCPredictor,
    format_ttc,
)
from core.challenge2_driver import DriverStatePredictor  # noqa: E402
from core.challenge3_fusion import FleetSafeDrivingScorer  # noqa: E402
from core.btc_trip import TripDataset  # noqa: E402

PANEL_SIZE = (640, 360)
WINDOW_NAME = "FPTU AI - BTC 3 Camera Trip Demo"
CSV_FIELDS = [
    "frame_id",
    "timestamp",
    "predicted_ttc",
    "predicted_driver_state",
    "predicted_risk_score",
]

# ─── Fleet Intervention Overlay ────────────────────────────────────────────
INTERVENTION_ENDPOINT = "http://127.0.0.1:8000/api/v1/alerts/interventions/pending"
INTERVENTION_DISPLAY_SEC = 18.0

_INTERVENTION_ICONS = {
    "alarm": "!! CANH BAO KHAN CAP !!",
    "stop": ">> LENH DUNG XE <<",
    "call": ">> KET NOI CUOC GOI <<",
}
_INTERVENTION_COLORS = {
    "alarm": (30, 30, 210),    # BGR red
    "stop":  (30, 130, 230),   # BGR orange
    "call":  (80, 200, 80),    # BGR green
}

class InterventionOverlayState:
    """Thread-safe container for the active intervention command."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cmd: dict | None = None
        self._expires: float = 0.0
        self._beep_stop = threading.Event()
        self._beep_thread: threading.Thread | None = None

    def set(self, cmd: dict) -> None:
        with self._lock:
            self._cmd = cmd
            self._expires = time.perf_counter() + INTERVENTION_DISPLAY_SEC
        self._start_beep(cmd.get("type", "alarm"))

    def clear(self) -> None:
        with self._lock:
            self._cmd = None
            self._expires = 0.0
        self._beep_stop.set()

    def get_active(self) -> dict | None:
        with self._lock:
            if self._cmd is None:
                return None
            if time.perf_counter() > self._expires:
                self._cmd = None
                self._beep_stop.set()
                return None
            return self._cmd

    def remaining(self) -> float:
        with self._lock:
            if self._cmd is None:
                return 0.0
            return max(0.0, self._expires - time.perf_counter())

    def _start_beep(self, notif_type: str) -> None:
        self._beep_stop.set()
        self._beep_stop = threading.Event()

        def loop() -> None:
            patterns = {
                "alarm": [(1100, 180), (1100, 180), (900, 260)],
                "stop": [(650, 320), (520, 320)],
                "call": [(700, 180), (900, 180), (700, 180), (900, 180)],
            }
            pattern = patterns.get(str(notif_type), patterns["alarm"])
            while not self._beep_stop.is_set():
                for freq, duration in pattern:
                    if self._beep_stop.is_set():
                        return
                    try:
                        winsound.Beep(freq, duration)
                    except Exception:
                        return
                self._beep_stop.wait(0.9)

        self._beep_thread = threading.Thread(target=loop, daemon=True)
        self._beep_thread.start()


def _poll_interventions(
    overlay: InterventionOverlayState,
    trip_id: str,
    stop_event: threading.Event,
    endpoint: str = INTERVENTION_ENDPOINT,
) -> None:
    """Background thread: poll FastAPI for pending intervention commands."""
    url = f"{endpoint}?trip_id={trip_id}"
    while not stop_event.is_set():
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
                data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                overlay.set(item)
        except (urllib.error.URLError, Exception):
            pass  # FastAPI BE not running — silently skip
        stop_event.wait(2.0)


def draw_intervention_overlay(canvas: np.ndarray, cmd: dict, remaining: float) -> np.ndarray:
    """Draw a full-canvas red alert overlay for a fleet intervention command."""
    h, w = canvas.shape[:2]
    overlay_layer = canvas.copy()
    notif_type = cmd.get("type", "alarm")
    border_color = _INTERVENTION_COLORS.get(notif_type, (30, 30, 210))
    # Red semi-transparent fill
    cv2.rectangle(overlay_layer, (0, 0), (w, h), (20, 20, 180), -1)
    canvas = cv2.addWeighted(overlay_layer, 0.45, canvas, 0.55, 0)
    # Bold pulsing border (thickness based on remaining time)
    thick = 6 if int(remaining * 2) % 2 == 0 else 3
    cv2.rectangle(canvas, (0, 0), (w - 1, h - 1), border_color, thick)
    # Header bar
    cv2.rectangle(canvas, (0, 0), (w, 56), border_color, -1)
    icon_text = _INTERVENTION_ICONS.get(notif_type, "!! LENH CAN THIEP !!")
    cv2.putText(canvas, icon_text, (16, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)
    badge = "FLEET COMMAND"
    badge_w = cv2.getTextSize(badge, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0][0]
    cv2.putText(canvas, badge, (w - badge_w - 14, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 200), 1, cv2.LINE_AA)
    # Message (word-wrap at ~60 chars)
    message = cmd.get("message", "")
    words = message.split()
    lines: list[str] = []
    cur = ""
    for w_tok in words:
        if len(cur) + len(w_tok) + 1 > 58:
            if cur:
                lines.append(cur)
            cur = w_tok
        else:
            cur = (cur + " " + w_tok).strip()
    if cur:
        lines.append(cur)
    y_text = 90
    for line in lines[:4]:
        cv2.putText(canvas, line, (20, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        y_text += 34
    # Countdown bar
    bar_y = h - 20
    bar_x0, bar_x1 = 20, w - 20
    cv2.rectangle(canvas, (bar_x0, bar_y - 6), (bar_x1, bar_y + 6), (60, 60, 60), -1)
    fill_x = int(bar_x0 + (bar_x1 - bar_x0) * (remaining / INTERVENTION_DISPLAY_SEC))
    cv2.rectangle(canvas, (bar_x0, bar_y - 6), (fill_x, bar_y + 6), border_color, -1)
    cv2.putText(canvas, f"{remaining:.0f}s", (bar_x1 + 6, bar_y + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Press C to dismiss fleet command", (20, h - 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (240, 240, 240), 1, cv2.LINE_AA)
    return canvas


def install_starterkit(starterkit_root: Path | None) -> None:
    candidates = [starterkit_root] if starterkit_root else []
    candidates.extend([Path.cwd(), AI_ROOT.parent])
    for candidate in candidates:
        if candidate and (
            candidate.resolve() / "team_kit" / "dataset_loader.py"
        ).is_file():
            sys.path.insert(0, str(candidate.resolve()))
            return
    raise FileNotFoundError(
        "Cannot find team_kit/dataset_loader.py; pass --starterkit-root."
    )


def put_text(
    image: np.ndarray,
    text: str,
    point: tuple[int, int],
    color: tuple[int, int, int] = (240, 240, 240),
    scale: float = 0.55,
    thickness: int = 1,
) -> None:
    cv2.putText(
        image, text, point, cv2.FONT_HERSHEY_SIMPLEX,
        scale, (10, 10, 10), thickness + 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, text, point, cv2.FONT_HERSHEY_SIMPLEX,
        scale, color, thickness, cv2.LINE_AA,
    )


def title_bar(
    image: np.ndarray,
    title: str,
    subtitle: str = "",
) -> None:
    cv2.rectangle(image, (0, 0), (image.shape[1], 34), (18, 22, 28), -1)
    put_text(image, title, (12, 23), (0, 220, 255), 0.58, 2)
    if subtitle:
        title_width = cv2.getTextSize(
            title, cv2.FONT_HERSHEY_SIMPLEX, 0.58, 2
        )[0][0]
        subtitle_width = cv2.getTextSize(
            subtitle, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1
        )[0][0]
        subtitle_x = image.shape[1] - subtitle_width - 12
        if subtitle_x > title_width + 28:
            put_text(
                image, subtitle, (subtitle_x, 23),
                (215, 215, 215), 0.45,
            )


def risk_color(value: float) -> tuple[int, int, int]:
    if value >= 75:
        return (25, 25, 235)
    if value >= 45:
        return (0, 165, 255)
    return (40, 210, 70)


def ttc_color(value: float) -> tuple[int, int, int]:
    if math.isfinite(value) and value < 2:
        return (25, 25, 235)
    if math.isfinite(value) and value < 5:
        return (0, 165, 255)
    return (40, 210, 70)


def draw_road(
    frame: np.ndarray,
    ttc: float,
    debug: dict[str, Any],
    annotations: list[dict[str, Any]],
) -> np.ndarray:
    canvas = cv2.resize(frame, PANEL_SIZE)
    source_h, source_w = frame.shape[:2]
    sx, sy = PANEL_SIZE[0] / source_w, PANEL_SIZE[1] / source_h
    objects = debug.get("objects", [])
    if objects:
        for obj in objects:
            x1, y1, x2, y2 = obj["bbox"]
            box = (
                int(x1 * sx), int(y1 * sy),
                int(x2 * sx), int(y2 * sy),
            )
            value = float(obj.get("ttc", float("inf")))
            color = ttc_color(value)
            cv2.rectangle(canvas, box[:2], box[2:], color, 2)
            depth = obj.get("depth_m")
            label = f"{obj['class']} #{obj['track_id']}"
            if depth is not None:
                label += f" {depth:.1f}m"
            if math.isfinite(value):
                label += f" TTC {value:.1f}s"
            put_text(
                canvas, label,
                (box[0], max(48, box[1] - 5)), color, 0.43, 1,
            )
        box_status = f"AI TRACKS: {len(objects)}"
    elif annotations:
        for item in annotations:
            x1, y1, x2, y2 = item["bbox"]
            box = (
                int(x1 * sx), int(y1 * sy),
                int(x2 * sx), int(y2 * sy),
            )
            color = (255, 190, 30)
            cv2.rectangle(canvas, box[:2], box[2:], color, 1)
            put_text(
                canvas, f"DATASET {item['class']}",
                (box[0], max(48, box[1] - 5)), color, 0.40,
            )
        box_status = (
            f"KITTI LABELS: {len(annotations)} (visual only)"
        )
    else:
        roi = debug.get("roi")
        if roi:
            x1, y1, x2, y2 = roi
            box = (
                int(x1 * sx), int(y1 * sy),
                int(x2 * sx), int(y2 * sy),
            )
            cv2.rectangle(canvas, box[:2], box[2:], (0, 190, 255), 2)
            put_text(
                canvas, "STEREO TTC ROI", (box[0], box[1] - 6),
                (0, 190, 255), 0.45,
            )
        box_status = "NO OBJECT BOX"
    mode = str(debug.get("mode", "unknown"))
    title_bar(canvas, "ROAD LEFT / CHALLENGE 1", box_status)
    ttc_label = format_ttc(ttc)
    put_text(
        canvas, f"TTC: {ttc_label}s", (15, 62),
        ttc_color(ttc), 0.72, 2,
    )
    put_text(
        canvas,
        f"mode: {mode} | depth: {debug.get('depth_source', 'unknown')}",
        (15, 85), (225, 225, 225), 0.43,
    )
    put_text(
        canvas, box_status, (365, 62),
        (190, 205, 215), 0.40,
    )
    return canvas


def draw_right(frame: np.ndarray) -> np.ndarray:
    canvas = cv2.resize(frame, PANEL_SIZE)
    title_bar(
        canvas,
        "ROAD RIGHT / STEREO REFERENCE",
    )
    put_text(
        canvas, "paired with road-left for depth",
        (395, 62), (210, 210, 210), 0.40,
    )
    return canvas


def draw_face(
    frame: np.ndarray,
    result: dict[str, Any],
) -> np.ndarray:
    canvas = cv2.resize(frame, PANEL_SIZE)
    source_h, source_w = frame.shape[:2]
    sx, sy = PANEL_SIZE[0] / source_w, PANEL_SIZE[1] / source_h
    boxes = result.get("visualization", {})
    for key, label, color in (
        ("face_bbox", "FACE", (40, 220, 70)),
        ("left_eye_bbox", "EYE", (255, 190, 30)),
        ("right_eye_bbox", "EYE", (255, 190, 30)),
        ("mouth_bbox", "MOUTH", (0, 170, 255)),
    ):
        box = boxes.get(key)
        if not box:
            continue
        x1, y1, x2, y2 = box
        a = (int(x1 * sx), int(y1 * sy))
        b = (int(x2 * sx), int(y2 * sy))
        cv2.rectangle(canvas, a, b, color, 1 if label != "FACE" else 2)
        put_text(canvas, label, (a[0], max(48, a[1] - 4)), color, 0.38)
    state = str(result["state"])
    state_color = (
        (40, 210, 70) if state == "alert"
        else (0, 165, 255) if state in {"drowsy", "yawning"}
        else (25, 25, 235)
    )
    title_bar(
        canvas, "FACE CAMERA / CHALLENGE 2",
    )
    put_text(
        canvas, f"STATE: {state.upper()}", (15, 62),
        state_color, 0.72, 2,
    )
    features = result.get("features", {})
    put_text(
        canvas,
        (
            f"conf {result['confidence']:.2f} | "
            f"eye {result['eye_state']} | mouth {result['mouth_state']} | "
            f"head {result['head_pose']}"
        ),
        (15, 85), (235, 235, 235), 0.43,
    )
    put_text(
        canvas,
        (
            f"EAR {features.get('ear_robust', 0):.3f}   "
            f"MAR {features.get('mar', 0):.3f}   "
            f"closure {features.get('continuous_eye_closure_ms', 0)}ms   "
            f"yaw {features.get('yaw_deg', 0):.1f}   "
            f"pitch {features.get('pitch_deg', 0):.1f}"
        ),
        (15, 108), (235, 235, 235), 0.43,
    )
    put_text(
        canvas,
        f"source: {result.get('prediction_source', 'ML model')}",
        (15, 131), (235, 235, 235), 0.43,
    )
    put_text(
        canvas, f"quality: {result['quality_status']}",
        (465, 62), (210, 210, 210), 0.40,
    )
    return canvas


def draw_dashboard(
    trip_id: str,
    frame: Any,
    ttc: float,
    driver: dict[str, Any],
    risk: float,
    speed: float,
    paused: bool,
) -> np.ndarray:
    canvas = np.full((PANEL_SIZE[1], PANEL_SIZE[0], 3), 22, np.uint8)
    title_bar(canvas, "FPTU AI FUSION / CHALLENGE 3")
    put_text(canvas, trip_id, (505, 62), (210, 210, 210), 0.42)
    rows = [
        ("FRAME", f"{frame.frame_id}  |  {frame.timestamp:.3f}s"),
        ("EGO", f"{frame.speed_kmh:.1f} km/h  accel {frame.longitudinal_accel:+.2f} m/s2"),
        ("TTC", f"{format_ttc(ttc)} s"),
        ("DRIVER", f"{driver['state']}  conf {driver['confidence']:.2f}"),
        ("ALERTNESS", f"{driver['alertness_score']:.2f}"),
        ("BTC RISK", f"{risk:.1f} / 100"),
        ("SAFE SCORE", f"{100.0 - risk:.1f} / 100"),
    ]
    y = 62
    for key, value in rows:
        put_text(canvas, key, (24, y), (145, 155, 165), 0.48, 1)
        color = (
            risk_color(risk) if key == "BTC RISK"
            else ttc_color(ttc) if key == "TTC"
            else (240, 240, 240)
        )
        put_text(canvas, value, (190, y), color, 0.58, 2)
        y += 34
    cv2.rectangle(canvas, (20, 302), (620, 306), (70, 75, 80), -1)
    status = "PAUSED" if paused else f"PLAYING {speed:g}x"
    put_text(canvas, status, (24, 333), (0, 220, 255), 0.52, 2)
    put_text(
        canvas, "SPACE pause | N next | +/- speed | Q quit",
        (185, 333), (205, 205, 205), 0.43,
    )
    return canvas


def project_kitti_labels(
    dataset: Any,
    frame_id: int,
    image_shape: tuple[int, ...],
) -> list[dict[str, Any]]:
    """Project optional KITTI 3-D labels for a clearly marked visual fallback."""
    label_path = dataset.label_dir / f"{frame_id:06d}.txt"
    if not label_path.is_file() or label_path.stat().st_size == 0:
        return []
    try:
        projection = dataset.load_frame_calibration(frame_id)["P2"]
    except (FileNotFoundError, KeyError):
        return []
    height_px, width_px = image_shape[:2]
    output: list[dict[str, Any]] = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) < 15:
            continue
        kind = fields[0]
        left, top, right, bottom = map(float, fields[4:8])
        if right > left and bottom > top:
            bbox = [left, top, right, bottom]
        else:
            h, w, length = map(float, fields[8:11])
            x, y, z = map(float, fields[11:14])
            yaw = float(fields[14])
            corners = np.array([
                [length / 2, 0, w / 2],
                [length / 2, 0, -w / 2],
                [-length / 2, 0, -w / 2],
                [-length / 2, 0, w / 2],
                [length / 2, -h, w / 2],
                [length / 2, -h, -w / 2],
                [-length / 2, -h, -w / 2],
                [-length / 2, -h, w / 2],
            ]).T
            rotation = np.array([
                [math.cos(yaw), 0, math.sin(yaw)],
                [0, 1, 0],
                [-math.sin(yaw), 0, math.cos(yaw)],
            ])
            camera = rotation @ corners + np.array([[x], [y], [z]])
            if np.any(camera[2] <= 0.1):
                continue
            homogeneous = np.vstack([camera, np.ones((1, 8))])
            pixels = projection @ homogeneous
            pixels = pixels[:2] / pixels[2:3]
            bbox = [
                float(pixels[0].min()), float(pixels[1].min()),
                float(pixels[0].max()), float(pixels[1].max()),
            ]
        x1 = max(0, min(width_px - 1, int(bbox[0])))
        y1 = max(0, min(height_px - 1, int(bbox[1])))
        x2 = max(0, min(width_px - 1, int(bbox[2])))
        y2 = max(0, min(height_px - 1, int(bbox[3])))
        if x2 > x1 and y2 > y1:
            output.append({"class": kind, "bbox": [x1, y1, x2, y2]})
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Display synchronized 2-road + 1-face BTC inference"
    )
    parser.add_argument("--trip-dir", type=Path, required=True)
    parser.add_argument("--starterkit-root", type=Path)
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
        default=None,
    )
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument(
        "--max-frames", type=int, default=0,
        help="0 processes until the trip ends",
    )
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument(
        "--speed-limit-kmh",
        type=float,
        help=(
            "Override metadata.speed_limit_kmh for a derived demo trip"
        ),
    )
    parser.add_argument(
        "--no-label-fallback", action="store_true",
        help="Do not draw explicitly marked KITTI labels when YOLO is absent",
    )
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument("--output-video", type=Path)
    parser.add_argument("--output-csv", type=Path)
    args = parser.parse_args()
    if args.start_frame < 0 or args.max_frames < 0 or args.speed <= 0:
        parser.error("start/max frames and speed must be non-negative")

    dataset = TripDataset(args.trip_dir.resolve())
    road_cfg = yaml.safe_load(
        args.road_config.read_text(encoding="utf-8")
    ) or {}
    road = RoadTTCPredictor(dataset.load_calibration(), road_cfg)
    road.set_trip_dir(dataset.trip_dir)
    road.reset()
    from core.runtime.model_registry import resolve_driver_model
    try:
        driver_model_path = resolve_driver_model(AI_ROOT, args.driver_model)
    except Exception as e:
        print(f"Model resolver error: {e}", file=sys.stderr)
        return 1
        
    driver = DriverStatePredictor(driver_model_path, args.driver_config)
    try:
        speed_limit_kmh = (
            float(args.speed_limit_kmh)
            if args.speed_limit_kmh is not None
            else float(dataset.metadata["speed_limit_kmh"])
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"{dataset.trip_id}: metadata.speed_limit_kmh is required "
            "for BTC Challenge 3"
        ) from exc
    fleet = FleetSafeDrivingScorer(speed_limit_kmh)
    fps = float(dataset.metadata.get("fps", 20.0) or 20.0)
    writer = None
    rows: list[dict[str, object]] = []
    paused = False
    step_once = False
    processed = 0
    started = time.perf_counter()

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
        for frame in dataset.iter_frames():
            if frame.frame_id < args.start_frame:
                # Stateful time-series predictors must still see earlier data.
                left = dataset.load_left(frame.frame_id)
                right = dataset.load_right(frame.frame_id)
                cabin = dataset.load_driver(frame.frame_id)
                warm_ttc = road.predict_frame(
                    frame.frame_id, frame.timestamp, left, right,
                    frame.speed_kmh,
                )
                driver.predict_frame(
                    frame.frame_id, round(frame.timestamp * 1000), cabin,
                )
                fleet.update(
                    warm_ttc,
                    frame.speed_kmh,
                    frame.longitudinal_accel,
                    frame.lateral_accel,
                )
                continue
            left = dataset.load_left(frame.frame_id)
            right = dataset.load_right(frame.frame_id)
            cabin = dataset.load_driver(frame.frame_id)
            ttc = road.predict_frame(
                frame.frame_id, frame.timestamp, left, right,
                frame.speed_kmh,
            )
            driver_result = driver.predict_frame(
                frame.frame_id, round(frame.timestamp * 1000), cabin,
            )
            fleet_score = fleet.update(
                ttc,
                frame.speed_kmh,
                frame.longitudinal_accel,
                frame.lateral_accel,
            )
            risk = fleet_score.risk_score
            annotations: list[dict[str, Any]] = []
            if (
                not road.last_debug.get("objects")
                and not args.no_label_fallback
            ):
                annotations = project_kitti_labels(
                    dataset, frame.frame_id, left.shape
                )
            top = np.hstack([
                draw_road(left, ttc, road.last_debug, annotations),
                draw_right(right),
            ])
            bottom = np.hstack([
                draw_face(cabin, driver_result),
                draw_dashboard(
                    dataset.trip_id, frame, ttc, driver_result,
                    risk, args.speed, paused,
                ),
            ])
            canvas = np.vstack([top, bottom])
            # ── Intervention overlay (drawn on full canvas before display) ─────
            active_cmd = intervention_overlay.get_active()
            if active_cmd is not None:
                canvas = draw_intervention_overlay(
                    canvas, active_cmd, intervention_overlay.remaining()
                )
            rows.append({
                "frame_id": frame.frame_id,
                "timestamp": f"{frame.timestamp:.3f}",
                "predicted_ttc": format_ttc(ttc),
                "predicted_driver_state": driver_result["state"],
                "predicted_risk_score": risk,
            })
            if args.output_video:
                if writer is None:
                    args.output_video.parent.mkdir(
                        parents=True, exist_ok=True
                    )
                    writer = cv2.VideoWriter(
                        str(args.output_video),
                        cv2.VideoWriter_fourcc(*"mp4v"),
                        fps, (canvas.shape[1], canvas.shape[0]),
                    )
                    if not writer.isOpened():
                        raise RuntimeError(
                            f"Cannot open video writer: {args.output_video}"
                        )
                writer.write(canvas)
            processed += 1
            if not args.no_display:
                cv2.imshow(WINDOW_NAME, canvas)
                while True:
                    delay = (
                        0 if paused and not step_once
                        else max(1, round(1000 / (fps * args.speed)))
                    )
                    key = cv2.waitKey(delay) & 0xFF
                    step_once = False
                    if key in (ord("q"), 27):
                        raise KeyboardInterrupt
                    if key == ord(" "):
                        paused = not paused
                        break
                    if key in (ord("n"), 83) and paused:
                        step_once = True
                        break
                    if key in (ord("+"), ord("=")):
                        args.speed = min(8.0, args.speed * 2)
                        break
                    if key in (ord("-"), ord("_")):
                        args.speed = max(0.25, args.speed / 2)
                        break
                    if not paused:
                        break
            if args.max_frames and processed >= args.max_frames:
                break
    except KeyboardInterrupt:
        pass
    finally:
        _stop_poll.set()
        driver.close()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()


    if args.output_csv:
        from core.runtime.paths import resolve_csv_output
        output_csv = resolve_csv_output(args.output_csv, dataset.trip_id)
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            csv_writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
            csv_writer.writeheader()
            csv_writer.writerows(rows)
    elapsed = max(1e-6, time.perf_counter() - started)
    print(
        f"{dataset.trip_id}: {processed} frames, "
        f"{processed / elapsed:.2f} processing FPS"
    )
    final_score = fleet.snapshot()
    print(
        "Challenge 3 BTC: "
        f"safe={final_score.safe_driving_score:.1f}, "
        f"risk={final_score.risk_score:.1f}, "
        f"near_miss={final_score.near_miss_count}, "
        "harsh="
        f"{final_score.harsh_brake_count}/"
        f"{final_score.harsh_accel_count}/"
        f"{final_score.harsh_corner_count}, "
        f"speeding={final_score.speeding_pct_time:.1f}%"
    )
    if not road.use_detector:
        print(
            "Challenge 1 detector unavailable; TTC used stereo ROI fallback. "
            f"Reason: {road.detector.load_error}"
        )
        if not args.no_label_fallback:
            print(
                "Road boxes, when present, are explicitly marked KITTI "
                "dataset labels and are visual-only."
            )
    if args.output_video:
        print(f"Video: {args.output_video.resolve()}")
    if args.output_csv:
        print(f"CSV: {args.output_csv.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
