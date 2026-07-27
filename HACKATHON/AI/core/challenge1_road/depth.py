"""
Depth estimation for Challenge 1.

Two paths, chosen per-detection:
  1. Stereo SGBM disparity → Z = f*B/d   (primary, when both frames given)
  2. Monocular bbox-height triangulation   (fallback when stereo depth in
     the bbox is unreliable, e.g. weak texture / far object)

Depth is sampled as a robust median inside each detection's bbox, not a
single pixel, to survive stereo speckle noise.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import cv2
import numpy as np

from .detection import Detection, REAL_HEIGHT_M

# See file 06 §2.5.4: stereo trustworthy < ~40m at this baseline; beyond
# that ΔZ grows quadratically and we prefer to report "safe".
MAX_TRUST_DEPTH_M = 60.0
MIN_TRUST_DEPTH_M = 1.0
MIN_VALID_DISP = 0.5


class StereoDepth:
    """Stereo SGBM disparity → per-bbox metric depth, with mono fallback.

    Images are optionally upsampled before matching (`upsample`>1). At this
    baseline a vehicle at ~25m spans only ~4px of disparity, so integer-ish
    disparity quantizes depth into flat plateaus — which flattens the
    depth-vs-time slope and makes closing-speed (hence TTC) collapse to inf
    on exactly the critical frames. Upsampling multiplies disparity
    resolution, recovering a usable depth gradient.
    """

    def __init__(
        self,
        fx: float,
        baseline_m: float,
        sgbm_params: Optional[Dict[str, Any]] = None,
        upsample: float = 2.0,
    ) -> None:
        self.fx = float(fx)
        self.baseline = float(baseline_m)
        self.upsample = float(upsample)
        # Overlay any config params ONTO the defaults rather than replacing
        # them wholesale — a config sgbm block that omits P1/P2/mode (the
        # smoothness + 3-way flags) must NOT silently drop them, or SGBM runs
        # with P1=P2=0 and returns badly speckled disparity on every trip.
        params = dict(_DEFAULT_SGBM)
        if sgbm_params:
            params.update(sgbm_params)
        # numDisparities must grow with upsampling to keep near-range coverage.
        params["numDisparities"] = int(params["numDisparities"] * self.upsample)
        self._matcher = cv2.StereoSGBM_create(**params)

    def disparity(self, left_bgr: np.ndarray, right_bgr: np.ndarray) -> np.ndarray:
        if self.upsample != 1.0:
            left_bgr = cv2.resize(left_bgr, None, fx=self.upsample, fy=self.upsample,
                                  interpolation=cv2.INTER_LINEAR)
            right_bgr = cv2.resize(right_bgr, None, fx=self.upsample, fy=self.upsample,
                                   interpolation=cv2.INTER_LINEAR)
        gray_l = cv2.cvtColor(left_bgr, cv2.COLOR_BGR2GRAY)
        gray_r = cv2.cvtColor(right_bgr, cv2.COLOR_BGR2GRAY)
        # SGBM returns fixed-point disparity scaled by 16.
        return self._matcher.compute(gray_l, gray_r).astype(np.float32) / 16.0

    def depth_map(self, disparity: np.ndarray) -> np.ndarray:
        # Disparity is in upsampled pixels, so focal length scales too:
        # Z = (fx*upsample)*B / disp_upsampled → finer depth granularity.
        fx_eff = self.fx * self.upsample
        depth = np.full_like(disparity, np.inf, dtype=np.float32)
        valid = disparity > MIN_VALID_DISP
        depth[valid] = (fx_eff * self.baseline) / disparity[valid]
        depth[depth < MIN_TRUST_DEPTH_M] = np.inf
        depth[depth > MAX_TRUST_DEPTH_M] = np.inf
        # Back to original resolution so bbox coords (original px) index correctly.
        if self.upsample != 1.0:
            depth = cv2.resize(depth, (int(depth.shape[1] / self.upsample),
                                       int(depth.shape[0] / self.upsample)),
                               interpolation=cv2.INTER_NEAREST)
        return depth

    def depth_for_bbox(
        self,
        depth_map: np.ndarray,
        det: Detection,
        shrink: float = 0.6,
    ) -> Optional[float]:
        """Robust median depth inside a shrunk central patch of the bbox.

        Shrinking avoids background bleed at the object edges. Returns None
        when too few valid stereo pixels — caller then uses mono fallback.
        """
        h, w = depth_map.shape
        x1, y1, x2, y2 = det.bbox
        cx, cy = det.cx, det.cy
        bw, bh = det.width_px * shrink, det.height_px * shrink
        px1 = max(0, int(cx - bw / 2))
        px2 = min(w, int(cx + bw / 2))
        py1 = max(0, int(cy - bh / 2))
        py2 = min(h, int(cy + bh / 2))
        if px2 <= px1 or py2 <= py1:
            return None

        patch = depth_map[py1:py2, px1:px2]
        finite = patch[np.isfinite(patch)]
        if finite.size:
            # Nearer percentile, not the median: for thin objects (a
            # motorcycle/pedestrian) the bbox patch is mostly background,
            # which sits FARTHER than the object surface — the median then
            # latches onto that background and over-estimates range (e.g.
            # 12m for a bike truly at 6.5m), corrupting both TTC and the
            # pixel→lateral geometry that gates the collision cone. The 25th
            # percentile tracks the object's own (nearer) surface.
            return float(np.percentile(finite, 25))
        if finite.size < 20:
            return None
        return float(np.median(finite))

    def depth_mono(self, det: Detection) -> Optional[float]:
        """Similar-triangle depth from bbox pixel height (fallback)."""
        real_h = REAL_HEIGHT_M.get(det.target_class)
        if real_h is None or det.height_px < 2:
            return None
        z = self.fx * real_h / det.height_px
        if z < MIN_TRUST_DEPTH_M or z > MAX_TRUST_DEPTH_M:
            return None
        return float(z)

    def estimate(self, depth_map: np.ndarray, det: Detection) -> Optional[float]:
        """Best available depth for a detection: stereo first, mono fallback."""
        z = self.depth_for_bbox(depth_map, det)
        if z is not None:
            return z
        return self.depth_mono(det)


_DEFAULT_SGBM = {
    "minDisparity": 0,
    "numDisparities": 96,   # divisible by 16
    "blockSize": 7,
    "P1": 8 * 3 * 7 ** 2,
    "P2": 32 * 3 * 7 ** 2,
    "disp12MaxDiff": 1,
    "uniquenessRatio": 10,
    "speckleWindowSize": 100,
    "speckleRange": 32,
    "mode": cv2.STEREO_SGBM_MODE_SGBM_3WAY,
}
