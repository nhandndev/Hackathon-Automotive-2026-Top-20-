"""
Challenge 1: Road ADAS & TTC Estimation — Single Source of Truth (SSOT).

Two entry points, same core:
  * `RoadTTCPredictor` — stateful, full stereo-vision pipeline
    (YOLOv8+ByteTrack detection → stereo/mono depth → TTC engine). Call
    `predict_frame()` once per frame in temporal order; `reset()` between
    trips. This is what `scripts/run_inference.py` and the Demo Engine use.
  * `predict_ttc()` — thin stateless helper kept for the SE interface
    contract (telemetry-only guess when no vision pipeline is wired up).

If ultralytics/torch or the YOLO weights aren't available, the predictor
degrades to a stereo-ROI baseline so a valid CSV is always produced.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from .detection import ObjectDetector
from .depth import StereoDepth
from .ttc_engine import TTCEngine


def format_ttc(ttc: float) -> str:
    """Serialize a TTC value for the submission CSV."""
    if ttc is None or not math.isfinite(ttc):
        return "inf"
    return f"{max(0.0, ttc):.3f}"


class RoadTTCPredictor:
    """Full stereo-vision TTC pipeline with temporal tracking state."""

    def __init__(
        self,
        calibration: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        cfg = config or {}
        if not calibration:
            raise ValueError("calibration required (need K_left/fx + baseline_m)")

        self.fx = float(calibration["K_left"][0][0])
        self.baseline = float(calibration["baseline_m"])
        self.image_width = int(calibration.get("image_width", 640))

        det_cfg = cfg.get("detector", {})
        self.detector = ObjectDetector(
            weights=det_cfg.get("weights", "yolov8n.pt"),
            conf=det_cfg.get("conf", 0.25),
            iou=det_cfg.get("iou", 0.5),
            device=det_cfg.get("device"),
            imgsz=det_cfg.get("imgsz", 640),
        )
        self.depth = StereoDepth(self.fx, self.baseline, cfg.get("sgbm"))
        self.engine = TTCEngine(self.fx, self.image_width)

        self.use_detector = self.detector.is_available()
        # Baseline-fallback state (used only when detector unavailable).
        self._roi_cfg = cfg.get("roi", _DEFAULT_ROI)
        self._depth_hist: List[Tuple[float, float]] = []

        # Output temporal hold: a lead vehicle can't vanish for a few frames,
        # but detection/stereo occasionally drops it, punching brief inf gaps
        # into an otherwise-finite critical sequence — each gap frame is
        # scored against a small GT TTC and costs ~penalty_cap. Hold the last
        # finite TTC across short gaps, counting it down by elapsed time.
        ttc_cfg = cfg.get("ttc", {})
        self._hold_frames = int(ttc_cfg.get("hold_frames", 6))
        self._last_finite_ttc: float = float("inf")
        self._last_finite_t: float = 0.0
        self._gap_count: int = 0

        # Output median smoothing: the fused per-frame TTC still jitters
        # frame-to-frame, and because the score's inverse-TTC term is highly
        # nonlinear at small TTC, that jitter inflates error. A short median
        # rejects single-frame spikes without lagging a genuine trend.
        # Median window of 1 = identity (off). A wider median rejects spikes
        # but lags a genuine approaching trend, which hurt the steady-lead
        # trips more than the jitter it removed — kept configurable, off by
        # default. Set ttc.smooth_out>1 in config only if a trip is jitter-
        # dominated rather than lag-sensitive.
        self._smooth_window = int(ttc_cfg.get("smooth_out", 1))
        self._ttc_out_hist: deque = deque(maxlen=self._smooth_window)

    # ------------------------------------------------------------------ #
    def predict_frame(
        self,
        frame_id: int,
        timestamp: float,
        left_bgr: np.ndarray,
        right_bgr: np.ndarray,
        ego_speed_kmh: float = 0.0,
    ) -> float:
        """Return predicted min_ttc (seconds; inf if safe) for one frame."""
        disparity = self.depth.disparity(left_bgr, right_bgr)
        depth_map = self.depth.depth_map(disparity)

        if not self.use_detector:
            return self._baseline_ttc(timestamp, depth_map, ego_speed_kmh)

        detections = self.detector.track(left_bgr)
        observations: List[Tuple[int, float, float, float]] = []
        for det in detections:
            z = self.depth.estimate(depth_map, det)
            if z is None:
                continue
            observations.append((det.track_id, z, det.cx, det.height_px))

        ttc = self.engine.update_and_compute(timestamp, observations, ego_speed_kmh)
        ttc = self._apply_hold(timestamp, ttc)
        return self._smooth_out(ttc)

    def _smooth_out(self, ttc: float) -> float:
        """Short median over recent outputs (inf mapped to a large sentinel)
        to reject single-frame spikes; result mapped back to inf."""
        SENT = 99.0
        self._ttc_out_hist.append(ttc if math.isfinite(ttc) else SENT)
        med = float(np.median(self._ttc_out_hist))
        return float("inf") if med >= SENT else med

    def _apply_hold(self, timestamp: float, ttc: float) -> float:
        """Bridge brief inf gaps by counting down the last finite TTC."""
        if math.isfinite(ttc):
            self._last_finite_ttc = ttc
            self._last_finite_t = timestamp
            self._gap_count = 0
            return ttc
        # ttc is inf — try to hold across a short gap
        if self._gap_count < self._hold_frames and math.isfinite(self._last_finite_ttc):
            elapsed = timestamp - self._last_finite_t
            held = self._last_finite_ttc - elapsed  # TTC counts down in real time
            if held > 0.1:
                self._gap_count += 1
                return held
        return float("inf")

    def reset(self) -> None:
        self.engine.reset()
        self._depth_hist.clear()
        self._last_finite_ttc = float("inf")
        self._last_finite_t = 0.0
        self._gap_count = 0
        self._ttc_out_hist.clear()
        if self.use_detector:
            self.detector.reset()

    # ------------------------------------------------------------------ #
    # Baseline fallback (no detector): stereo ROI median depth + closing speed
    # ------------------------------------------------------------------ #
    def _baseline_ttc(self, t: float, depth_map: np.ndarray, ego_speed_kmh: float) -> float:
        if ego_speed_kmh < 5.0:
            return float("inf")
        h, w = depth_map.shape
        x0 = int(w * self._roi_cfg["x_start_frac"])
        x1 = int(w * self._roi_cfg["x_end_frac"])
        y0 = int(h * self._roi_cfg["y_start_frac"])
        y1 = int(h * self._roi_cfg["y_end_frac"])
        roi = depth_map[y0:y1, x0:x1]
        finite = roi[np.isfinite(roi)]
        if finite.size < 100:
            return float("inf")
        depth = float(np.median(finite))

        self._depth_hist.append((t, depth))
        if len(self._depth_hist) > 5:
            self._depth_hist.pop(0)
        if len(self._depth_hist) < 2:
            return float("inf")
        ts = np.array([a for a, _ in self._depth_hist])
        ds = np.array([b for _, b in self._depth_hist])
        if ts.max() - ts.min() < 1e-3:
            return float("inf")
        A = np.vstack([ts, np.ones_like(ts)]).T
        slope, _ = np.linalg.lstsq(A, ds, rcond=None)[0]
        closing = -float(slope)
        if closing <= 0.5:
            return float("inf")
        return depth / closing


_DEFAULT_ROI = {
    "x_start_frac": 0.35,
    "x_end_frac": 0.65,
    "y_start_frac": 0.50,
    "y_end_frac": 0.85,
}


# ---------------------------------------------------------------------- #
# Thin stateless SSOT helper (SE interface contract) — telemetry-only.
# ---------------------------------------------------------------------- #
def predict_ttc(telemetry_data: dict, road_vision_data: dict = None) -> str:
    """Telemetry-only TTC guess for callers without the vision pipeline.

    Returns 'inf' when safe or a formatted seconds string when a hard
    deceleration at speed suggests an imminent conflict. This is a coarse
    fallback — real scoring uses `RoadTTCPredictor.predict_frame()`.
    """
    speed_kmh = telemetry_data.get("speed_kmh", 0.0)
    accel = telemetry_data.get("longitudinal_accel", 0.0)

    if accel < -3.0 and speed_kmh > 40.0:
        return "1.2"
    if accel < -2.0 and speed_kmh > 50.0:
        return "1.8"
    return "inf"
