"""Timestamp-based Driver Monitoring System core.

The processing frame is never mirrored. Mirroring is only applied by the UI.
Feature distances use pixel coordinates as required by the v2 specification.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import hypot
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .face_landmarker import OnnxFaceLandmarker
from .hand_landmarker import OnnxHandLandmarker

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


def landmark_bbox(
    points: np.ndarray,
    width: int,
    height: int,
    padding: int = 4,
) -> list[int]:
    """Return a clipped pixel bounding box [x1, y1, x2, y2]."""
    x1 = max(0, int(np.floor(points[:, 0].min())) - padding)
    y1 = max(0, int(np.floor(points[:, 1].min())) - padding)
    x2 = min(width - 1, int(np.ceil(points[:, 0].max())) + padding)
    y2 = min(height - 1, int(np.ceil(points[:, 1].max())) + padding)
    return [x1, y1, x2, y2]


@dataclass
class _Sample:
    timestamp_ms: int
    valid: bool
    closed: bool
    off_road: bool


class DMSCore:
    """ONNX feature extraction plus deterministic temporal state engine."""

    def __init__(
        self,
        config: dict[str, Any],
        driver_profile: Any | None = None,
    ):
        self.cfg = config
        self.driver_profile = driver_profile
        face = config["face"]
        self.face_landmarker = OnnxFaceLandmarker(
            face,
            default_model_dir=Path(__file__).resolve().parents[2] / "models",
        )
        self.hand_landmarker = OnnxHandLandmarker(
            config.get("hand", {}),
            default_model_dir=Path(__file__).resolve().parents[2] / "models",
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
        
        self._last_hand_frame_id = -9999
        self._last_hand_results = []
        self._last_hand_x_rel = 0.0
        self._last_hand_y_rel = 0.0
        self._last_hand_ms: int | None = None

    def close(self) -> None:
        self.face_landmarker.close()
        self.hand_landmarker.close()

    def reset_temporal(self) -> None:
        """Reset sequence state without discarding subject calibration."""
        self.last_face_ms = None
        self.eye_closed_since = None
        self.mouth_open_since = None
        self.off_road_since = None
        self.eye_closed_latched = False
        self.history.clear()
        self.ear_filter.clear()
        self.mar_filter.clear()
        self._last_hand_frame_id = -9999
        self._last_hand_results = []
        self._last_hand_ms = None

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
            "mouth_event": "none", "head_state": "unknown", 
            "features": {
                "hand_visible": 0.0, "hand_x_rel_face": 0.0, "hand_y_rel_face": 0.0,
                "hand_to_face_distance": 2.0, "hand_motion": 0.0, "hand_active": 0.0,
                "head_side_and_hand_active": 0.0, "head_down_and_hand_active": 0.0,
                "head_hand_interaction": 0.0,
            },
            "observation": {"face_detected": False, "face_confidence": 0.0,
                "left_eye_valid": False, "right_eye_valid": False, "mouth_valid": False,
            "head_pose_valid": False, "coverage_30s": 0.0,
                "quality_status": "face_missing", "missing_duration_ms": max(0, missing),
                "monitoring_available": False},
            "visualization": {},
        }

    def process(self, frame: np.ndarray, frame_id: int, timestamp_ms: int) -> dict[str, Any]:
        if self.started_ms is None:
            self.started_ms = timestamp_ms
        height, width = frame.shape[:2]
        result = self.face_landmarker.detect(frame, timestamp_ms)
        if result is None:
            self.history.append(_Sample(timestamp_ms, False, False, False))
            return self._missing(frame_id, timestamp_ms)

        self.last_face_ms = timestamp_ms
        pts = np.asarray(result.landmarks[:, :2], dtype=np.float64).copy()
        pts[:, 0] *= width
        pts[:, 1] *= height
        mouth_indices = sorted(
            set(MOUTH_CORNERS).union(
                point for pair in MOUTH_VERTICAL for point in pair
            )
        )
        visualization = {
            "face_bbox": landmark_bbox(pts, width, height, padding=8),
            "left_eye_bbox": landmark_bbox(
                pts[list(EYE_A)], width, height, padding=8
            ),
            "right_eye_bbox": landmark_bbox(
                pts[list(EYE_B)], width, height, padding=8
            ),
            "mouth_bbox": landmark_bbox(
                pts[mouth_indices], width, height, padding=10
            ),
        }
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

        calibrating = (
            self.driver_profile is None
            and timestamp_ms - self.started_ms
            < int(self.cfg["eye"]["calibration_seconds"] * 1000)
        )
        if calibrating:
            self.open_ears.append(ear)
            self.closed_mars.append(mar)
            if pose_valid:
                self.neutral_poses.append(pose)
        if self.driver_profile is None:
            ear_open = (
                float(np.median(self.open_ears))
                if self.open_ears
                else max(ear, 0.25)
            )
            ear_closed = max(0.05, ear_open * 0.45)
        else:
            ear_open = float(self.driver_profile.ear_open)
            ear_closed = float(self.driver_profile.ear_closed)
        closure = _clamp((ear_open - ear) / max(1e-6, ear_open - ear_closed))
        if self.driver_profile is None:
            mar_base = (
                float(np.median(self.closed_mars))
                if self.closed_mars
                else mar
            )
            mar_mad = (
                float(
                    np.median(
                        np.abs(np.asarray(self.closed_mars) - mar_base)
                    )
                )
                if self.closed_mars
                else 0.0
            )
            mar_threshold = max(
                mar_base + 3 * 1.4826 * mar_mad, mar_base * 1.45
            )
            neutral = (
                np.median(self.neutral_poses, axis=0)
                if self.neutral_poses
                else np.zeros(3)
            )
            closure_enter = float(self.cfg["eye"]["closure_ratio_enter"])
            closure_exit = float(self.cfg["eye"]["closure_ratio_exit"])
        else:
            mar_threshold = float(self.driver_profile.mar_yawn)
            neutral = np.asarray(
                [
                    self.driver_profile.neutral_pitch_deg,
                    self.driver_profile.neutral_yaw_deg,
                    self.driver_profile.neutral_roll_deg,
                ],
                dtype=float,
            )
            closure_enter = float(
                self.driver_profile.eye_closure_threshold
            )
            closure_exit = min(
                float(self.cfg["eye"]["closure_ratio_exit"]),
                closure_enter - 0.10,
            )
        pitch, yaw, roll = (
            angle_delta(pose[0], neutral[0]),
            angle_delta(pose[1], neutral[1]),
            angle_delta(pose[2], neutral[2]),
        )

        # Hysteresis prevents one noisy frame around the threshold from
        # splitting a prolonged eye closure into several short blinks.
        if self.eye_closed_latched:
            closed = closure > closure_exit
        else:
            closed = closure >= closure_enter
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
        
        # Hand processing
        hand_cfg = self.cfg.get("hand", {})
        if hand_cfg.get("enabled", True):
            if frame_id - self._last_hand_frame_id >= hand_cfg.get("inference_interval_frames", 3):
                self._last_hand_results = self.hand_landmarker.detect(frame, frame_id)
                self._last_hand_frame_id = frame_id
            if frame_id - self._last_hand_frame_id > hand_cfg.get("max_stale_frames", 6):
                self._last_hand_results = []
                self._last_hand_ms = None
        else:
            self._last_hand_results = []
            
        hand_visible = float(len(self._last_hand_results) > 0)
        hand_count = float(len(self._last_hand_results))
        hand_x_rel_face = 0.0
        hand_y_rel_face = 0.0
        missing_dist = float(hand_cfg.get("missing_distance_value", 2.0))
        hand_to_face_distance = missing_dist
        hand_motion = 0.0
        hand_active = 0.0
        
        # Architect-v2 distance anchors
        min_hand_to_mouth_norm = missing_dist
        min_hand_to_ear_side_norm = missing_dist
        min_hand_to_eye_norm = missing_dist
        min_hand_to_face_center_norm = missing_dist
        min_hand_to_left_ear_side_norm = missing_dist
        min_hand_to_right_ear_side_norm = missing_dist
        hand_motion_norm = 0.0
        
        face_x1, face_y1, face_x2, face_y2 = visualization["face_bbox"]
        face_w = max(face_x2 - face_x1, 1)
        face_h = max(face_y2 - face_y1, 1)
        face_cx = (face_x1 + face_x2) / 2
        face_cy = (face_y1 + face_y2) / 2
        face_diag = hypot(face_w, face_h)
        
        # Face anchors
        mouth_center = np.mean(pts[[13, 14, 78, 308]], axis=0)
        left_eye_center = np.mean(pts[list(EYE_A)], axis=0)
        right_eye_center = np.mean(pts[list(EYE_B)], axis=0)
        # Left ear-side anchor (outermost left face contour point e.g. 234)
        # Right ear-side anchor (outermost right face contour point e.g. 454)
        left_ear_side = pts[234]
        right_ear_side = pts[454]
        
        if hand_visible:
            PALM_INDICES = (0, 5, 9, 13, 17)
            palm_centers = []
            for hand_res in self._last_hand_results:
                if hasattr(hand_res, "landmarks") and len(hand_res.landmarks) > max(PALM_INDICES):
                    p_x = float(np.mean([hand_res.landmarks[i][0] * width for i in PALM_INDICES]))
                    p_y = float(np.mean([hand_res.landmarks[i][1] * height for i in PALM_INDICES]))
                    palm_centers.append(np.array([p_x, p_y]))
                    
            if palm_centers:
                # Use first hand for legacy fields
                palm_x_px, palm_y_px = palm_centers[0][0], palm_centers[0][1]
                hand_x_rel_face = (palm_x_px - face_cx) / face_w
                hand_y_rel_face = (palm_y_px - face_cy) / face_h
                hand_to_face_distance = hypot(palm_x_px - face_cx, palm_y_px - face_cy) / max(face_diag, 1e-6)
                
                if self._last_hand_ms is not None:
                    dx = hand_x_rel_face - self._last_hand_x_rel
                    dy = hand_y_rel_face - self._last_hand_y_rel
                    dt = (timestamp_ms - self._last_hand_ms) / 1000.0
                    hand_motion = hypot(dx, dy) / max(dt, 1e-6)
                    hand_motion_norm = hand_motion
                    
                self._last_hand_x_rel = hand_x_rel_face
                self._last_hand_y_rel = hand_y_rel_face
                self._last_hand_ms = timestamp_ms
                
                hand_active_threshold = float(hand_cfg.get("motion_active_threshold", 0.15))
                hand_active = float(hand_motion >= hand_active_threshold)
                
                # Minimum norm distances over all palm centers
                mouth_dists = [hypot(p[0] - mouth_center[0], p[1] - mouth_center[1]) / max(face_diag, 1e-6) for p in palm_centers]
                left_ear_dists = [hypot(p[0] - left_ear_side[0], p[1] - left_ear_side[1]) / max(face_diag, 1e-6) for p in palm_centers]
                right_ear_dists = [hypot(p[0] - right_ear_side[0], p[1] - right_ear_side[1]) / max(face_diag, 1e-6) for p in palm_centers]
                eye_dists = [
                    min(hypot(p[0] - left_eye_center[0], p[1] - left_eye_center[1]),
                        hypot(p[0] - right_eye_center[0], p[1] - right_eye_center[1])) / max(face_diag, 1e-6)
                    for p in palm_centers
                ]
                face_center_dists = [hypot(p[0] - face_cx, p[1] - face_cy) / max(face_diag, 1e-6) for p in palm_centers]
                
                min_hand_to_mouth_norm = float(min(mouth_dists))
                min_hand_to_left_ear_side_norm = float(min(left_ear_dists))
                min_hand_to_right_ear_side_norm = float(min(right_ear_dists))
                min_hand_to_ear_side_norm = float(min(min_hand_to_left_ear_side_norm, min_hand_to_right_ear_side_norm))
                min_hand_to_eye_norm = float(min(eye_dists))
                min_hand_to_face_center_norm = float(min(face_center_dists))
            else:
                self._last_hand_ms = None
        else:
            self._last_hand_ms = None
            
        head_side = float(abs(yaw) >= self.cfg["attention"]["candidate_yaw_deg"])
        head_down = float(pitch >= self.cfg["attention"]["candidate_pitch_deg"])
        head_side_and_hand_active = head_side * hand_active
        head_down_and_hand_active = head_down * hand_active
        head_hand_interaction = max(head_side_and_hand_active, head_down_and_hand_active)
        
        # Hand near thresholds
        near_mouth_thresh = float(hand_cfg.get("near_mouth_norm_threshold", 0.45))
        near_ear_thresh = float(hand_cfg.get("near_ear_norm_threshold", 0.45))
        near_face_thresh = float(hand_cfg.get("near_face_norm_threshold", 0.70))
        
        hand_near_mouth = float(min_hand_to_mouth_norm < near_mouth_thresh)
        hand_near_ear = float(min_hand_to_ear_side_norm < near_ear_thresh)
        hand_near_face = float(min_hand_to_face_center_norm < near_face_thresh)
        
        offroad_and_hand_visible = float(off_road > 0 and hand_visible > 0)
        offroad_and_hand_active = float(off_road > 0 and hand_active > 0)
        
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
                "roll_deg": round(float(roll), 2),
                "raw_yaw_deg": round(float(pose[1]), 2),
                "raw_pitch_deg": round(float(pose[0]), 2),
                "raw_roll_deg": round(float(pose[2]), 2),
                "continuous_eye_closure_ms": closure_ms,
                "mouth_open_duration_ms": mouth_ms,
                "off_road_duration_ms": off_road_ms,
                "hand_visible": hand_visible,
                "hand_x_rel_face": round(hand_x_rel_face, 3),
                "hand_y_rel_face": round(hand_y_rel_face, 3),
                "hand_to_face_distance": round(hand_to_face_distance, 3),
                "hand_motion": round(hand_motion, 3),
                "hand_active": hand_active,
                "head_side_and_hand_active": head_side_and_hand_active,
                "head_down_and_hand_active": head_down_and_hand_active,
                "head_hand_interaction": head_hand_interaction,
                # Architect-v2 features
                "hand_count": hand_count,
                "min_hand_to_mouth_norm": round(min_hand_to_mouth_norm, 3),
                "min_hand_to_ear_side_norm": round(min_hand_to_ear_side_norm, 3),
                "min_hand_to_eye_norm": round(min_hand_to_eye_norm, 3),
                "min_hand_to_face_center_norm": round(min_hand_to_face_center_norm, 3),
                "min_hand_to_left_ear_side_norm": round(min_hand_to_left_ear_side_norm, 3),
                "min_hand_to_right_ear_side_norm": round(min_hand_to_right_ear_side_norm, 3),
                "hand_motion_norm": round(hand_motion_norm, 3),
                "hand_near_mouth": hand_near_mouth,
                "hand_near_ear": hand_near_ear,
                "hand_near_face": hand_near_face,
                "offroad_and_hand_visible": offroad_and_hand_visible,
                "offroad_and_hand_active": offroad_and_hand_active,
            },
            "observation": {
                "face_detected": True, "face_confidence": round(result.confidence, 3), "left_eye_valid": ear_left is not None,
                "right_eye_valid": ear_right is not None, "mouth_valid": True,
                "head_pose_valid": pose_valid, "coverage_30s": round(coverage, 3),
                "quality_status": (
                    "calibrating"
                    if calibrating
                    else "valid_profile"
                    if self.driver_profile is not None
                    else "valid"
                ),
                "monitoring_available": True,
            },
            "visualization": visualization,
        }
