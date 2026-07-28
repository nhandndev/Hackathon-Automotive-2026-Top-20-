"""Timestamp-based Driver Monitoring System core.

The processing frame is never mirrored. Mirroring is only applied by the UI.
Feature distances use pixel coordinates as required by the v2 specification.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import hypot
from typing import Any

import cv2
import mediapipe as mp
import numpy as np

EYE_A = (33, 160, 158, 133, 153, 144)
EYE_B = (362, 385, 387, 263, 373, 380)
MOUTH_VERTICAL = ((13, 14), (82, 312), (87, 317))
MOUTH_CORNERS = (78, 308)
POSE_LANDMARKS = (1, 152, 33, 263, 61, 291)
POSE_MODEL = np.array(
    [(0, 0, 0), (0, -63.6, -12.5), (-43.3, 32.7, -26),
     (43.3, 32.7, -26), (-28.9, -28.9, -24.1), (28.9, -28.9, -24.1)],
    dtype=np.float64,
)


def _distance(a: np.ndarray, b: np.ndarray) -> float:
    return hypot(float(a[0] - b[0]), float(a[1] - b[1]))


def eye_aspect_ratio(points: np.ndarray) -> float | None:
    horizontal = _distance(points[0], points[3])
    if horizontal < 1e-6:
        return None
    return (_distance(points[1], points[5]) + _distance(points[2], points[4])) / (2 * horizontal)


def mouth_aspect_ratio(points: np.ndarray) -> float | None:
    width = _distance(points[MOUTH_CORNERS[0]], points[MOUTH_CORNERS[1]])
    if width < 1e-6:
        return None
    return sum(_distance(points[a], points[b]) for a, b in MOUTH_VERTICAL) / (3 * width)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def angle_delta(angle: float, reference: float) -> float:
    """Return the shortest signed angular difference in degrees."""
    return (float(angle) - float(reference) + 180.0) % 360.0 - 180.0


@dataclass
class _Sample:
    timestamp_ms: int
    valid: bool
    closed: bool
    off_road: bool


class DMSCore:
    """MediaPipe feature extraction plus deterministic temporal state engine."""

    def __init__(self, config: dict[str, Any]):
        self.cfg = config
        face = config["face"]
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=float(face["min_detection_confidence"]),
            min_tracking_confidence=float(face["min_tracking_confidence"]),
        )
        self.started_ms: int | None = None
        self.last_face_ms: int | None = None
        self.eye_closed_since: int | None = None
        self.mouth_open_since: int | None = None
        self.off_road_since: int | None = None
        self.eye_closed_latched = False
        self.open_ears: list[float] = []
        self.closed_mars: list[float] = []
        self.neutral_poses: list[np.ndarray] = []
        self.history: deque[_Sample] = deque()
        self.ear_filter: deque[float] = deque(maxlen=int(config["smoothing"]["primitive_median_window_frames"]))
        self.mar_filter: deque[float] = deque(maxlen=int(config["smoothing"]["primitive_median_window_frames"]))

    def close(self) -> None:
        self.mesh.close()

    def _pose(self, pts: np.ndarray, width: int, height: int) -> tuple[np.ndarray, bool]:
        image_points = pts[list(POSE_LANDMARKS)].astype(np.float64)
        focal = float(width)
        camera = np.array([[focal, 0, width / 2], [0, focal, height / 2], [0, 0, 1]], dtype=np.float64)
        ok, rotation, _ = cv2.solvePnP(POSE_MODEL, image_points, camera, np.zeros((4, 1)), flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            return np.zeros(3), False
        matrix, _ = cv2.Rodrigues(rotation)
        angles, *_ = cv2.RQDecomp3x3(matrix)
        return np.asarray(angles, dtype=float), True  # pitch, yaw, roll

    def _window_stats(self, now: int) -> tuple[float, float, float]:
        while self.history and now - self.history[0].timestamp_ms > 30_000:
            self.history.popleft()
        if len(self.history) < 2:
            return 0.0, 0.0, 0.0
        valid_ms = closed_ms = off_road_ms = 0
        for previous, current in zip(self.history, list(self.history)[1:]):
            dt = max(0, current.timestamp_ms - previous.timestamp_ms)
            if previous.valid:
                valid_ms += dt
                closed_ms += dt if previous.closed else 0
                off_road_ms += dt if previous.off_road else 0
        span = max(1, self.history[-1].timestamp_ms - self.history[0].timestamp_ms)
        return closed_ms / max(1, valid_ms), valid_ms / span, float(off_road_ms)

    def _missing(self, frame_id: int, timestamp_ms: int) -> dict[str, Any]:
        missing = timestamp_ms - (self.last_face_ms if self.last_face_ms is not None else timestamp_ms)
        return {
            "frame_id": frame_id, "timestamp_ms": timestamp_ms,
            "driver_state": "unknown", "state_confidence": 0.0, "alertness_score": 0.0,
            "attention_state": "unknown", "fatigue_level": "unknown",
            "eye_state": "unknown", "eye_event": "none", "mouth_state": "unknown",
            "mouth_event": "none", "head_state": "unknown", "features": {},
            "observation": {"face_detected": False, "face_confidence": 0.0,
                "left_eye_valid": False, "right_eye_valid": False, "mouth_valid": False,
                "head_pose_valid": False, "coverage_30s": 0.0,
                "quality_status": "face_missing", "missing_duration_ms": max(0, missing),
                "monitoring_available": False},
        }

    def process(self, frame: np.ndarray, frame_id: int, timestamp_ms: int) -> dict[str, Any]:
        if self.started_ms is None:
            self.started_ms = timestamp_ms
        height, width = frame.shape[:2]
        result = self.mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not result.multi_face_landmarks:
            self.history.append(_Sample(timestamp_ms, False, False, False))
            return self._missing(frame_id, timestamp_ms)

        self.last_face_ms = timestamp_ms
        raw = result.multi_face_landmarks[0].landmark
        pts = np.array([(p.x * width, p.y * height) for p in raw], dtype=np.float64)
        ear_left = eye_aspect_ratio(pts[list(EYE_A)])
        ear_right = eye_aspect_ratio(pts[list(EYE_B)])
        ear = float(np.median([x for x in (ear_left, ear_right) if x is not None]))
        mar = mouth_aspect_ratio(pts)
        assert mar is not None
        self.ear_filter.append(ear)
        self.mar_filter.append(mar)
        ear = float(np.median(self.ear_filter))
        mar = float(np.median(self.mar_filter))
        pose, pose_valid = self._pose(pts, width, height)

        calibrating = timestamp_ms - self.started_ms < int(self.cfg["eye"]["calibration_seconds"] * 1000)
        if calibrating:
            self.open_ears.append(ear)
            self.closed_mars.append(mar)
            if pose_valid:
                self.neutral_poses.append(pose)
        ear_open = float(np.median(self.open_ears)) if self.open_ears else max(ear, 0.25)
        ear_closed = max(0.05, ear_open * 0.45)
        closure = _clamp((ear_open - ear) / max(1e-6, ear_open - ear_closed))
        mar_base = float(np.median(self.closed_mars)) if self.closed_mars else mar
        mar_mad = float(np.median(np.abs(np.asarray(self.closed_mars) - mar_base))) if self.closed_mars else 0.0
        mar_threshold = max(mar_base + 3 * 1.4826 * mar_mad, mar_base * 1.45)
        neutral = np.median(self.neutral_poses, axis=0) if self.neutral_poses else np.zeros(3)
        pitch, yaw, roll = (
            angle_delta(pose[0], neutral[0]),
            angle_delta(pose[1], neutral[1]),
            angle_delta(pose[2], neutral[2]),
        )

        # Hysteresis prevents one noisy frame around the threshold from
        # splitting a prolonged eye closure into several short blinks.
        if self.eye_closed_latched:
            closed = closure > float(self.cfg["eye"]["closure_ratio_exit"])
        else:
            closed = closure >= float(self.cfg["eye"]["closure_ratio_enter"])
        self.eye_closed_latched = closed
        if closed and self.eye_closed_since is None:
            self.eye_closed_since = timestamp_ms
        if not closed:
            self.eye_closed_since = None
        closure_ms = timestamp_ms - self.eye_closed_since if self.eye_closed_since is not None else 0
        mouth_open = mar >= mar_threshold
        if mouth_open and self.mouth_open_since is None:
            self.mouth_open_since = timestamp_ms
        if not mouth_open:
            self.mouth_open_since = None
        mouth_ms = timestamp_ms - self.mouth_open_since if self.mouth_open_since is not None else 0
        off_road = abs(yaw) >= self.cfg["attention"]["candidate_yaw_deg"] or abs(pitch) >= self.cfg["attention"]["candidate_pitch_deg"]
        if off_road and self.off_road_since is None:
            self.off_road_since = timestamp_ms
        if not off_road:
            self.off_road_since = None
        off_road_ms = timestamp_ms - self.off_road_since if self.off_road_since is not None else 0

        self.history.append(_Sample(timestamp_ms, True, closed, off_road))
        perclos, coverage, vats_ms = self._window_stats(timestamp_ms)
        microsleep = self.cfg["eye"]["microsleep_min_ms"] <= closure_ms < self.cfg["eye"]["microsleep_max_ms"]
        sleep_candidate = closure_ms >= self.cfg["eye"]["sleep_min_ms"]
        yawn = mouth_ms >= self.cfg["mouth"]["yawn_min_ms"]
        distracted = off_road_ms >= self.cfg["attention"]["long_glance_ms"] or vats_ms >= self.cfg["attention"]["vats_trigger_ms"]
        fatigue = _clamp(0.65 * perclos + 0.20 * min(1, closure_ms / 1000) + 0.15 * float(yawn))
        if microsleep or sleep_candidate:
            state = "microsleep"
        elif yawn:
            state = "yawning"
        elif distracted:
            state = "distracted"
        elif fatigue >= 0.60:
            state = "drowsy"
        else:
            state = "alert"
        confidence = _clamp(0.55 + 0.4 * coverage) if not calibrating else 0.45
        head_state = "right" if yaw > 20 else "left" if yaw < -20 else "down" if pitch > 15 else "normal"
        eye_event = "sleep_candidate" if sleep_candidate else "microsleep" if microsleep else "prolonged_closure" if closure_ms >= 500 else "none"
        return {
            "frame_id": frame_id, "timestamp_ms": timestamp_ms, "driver_state": state,
            "state_confidence": round(confidence, 3), "alertness_score": round(1 - fatigue, 3),
            "attention_state": "off_road" if off_road else "on_road",
            "fatigue_level": "severe" if fatigue >= .75 else "moderate" if fatigue >= .6 else "mild" if fatigue >= .3 else "none",
            "eye_state": "closed" if closed else "open", "eye_event": eye_event,
            "mouth_state": "yawning" if yawn else "open" if mouth_open else "normal",
            "mouth_event": "yawn" if yawn else "none", "head_state": head_state,
            "features": {
                "ear_left": round(float(ear_left), 3), "ear_right": round(float(ear_right), 3),
                "ear_robust": round(ear, 3), "closure_ratio": round(closure, 3),
                "perclos_30s": round(perclos, 3), "mar": round(mar, 3),
                "yaw_deg": round(float(yaw), 2), "pitch_deg": round(float(pitch), 2),
                "roll_deg": round(float(roll), 2), "off_road_duration_ms": off_road_ms,
            },
            "observation": {
                "face_detected": True, "face_confidence": 1.0, "left_eye_valid": ear_left is not None,
                "right_eye_valid": ear_right is not None, "mouth_valid": True,
                "head_pose_valid": pose_valid, "coverage_30s": round(coverage, 3),
                "quality_status": "calibrating" if calibrating else "valid",
                "monitoring_available": True,
            },
        }
