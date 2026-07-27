"""
Standalone prototype -- depth-based moving-obstacle detector (Phase: new
attack angle, see conversation). Does NOT touch the main pipeline; this is
a throwaway validation script to answer one question cheaply before any
real integration work: can clustering+tracking raw depth (no YOLO) catch
the T02 motorcycle earlier than frame 319 (where YOLO first locks on)?

Method:
  1. Reproject each corridor pixel to metric (X, Z) using pinhole geometry.
  2. Histogram-bin Z within the corridor. A discrete object (fence post,
     bike) is roughly constant-depth -> forms a narrow, tall histogram
     spike. The road surface spans a continuous depth range -> spreads
     thinly across many bins. This cheaply separates "compact object" from
     "ground plane" without a full 3D ground-plane fit.
  3. Frame-to-frame nearest-neighbour association (poor man's tracker) on
     (Z, X), keeping a short history per track.
  4. Keep only tracks whose Z is DECREASING (approaching) -- this is what
     rejects the static fence blob we found stuck at ~3.0m earlier.

Run: py -3.13 scripts/proto_geo_detector.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

AI_ROOT = Path(__file__).resolve().parents[1]
KIT = AI_ROOT / "Dataset" / "Dataset" / "Package_starterkit" / "package_starterkit"
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(AI_ROOT))

from team_kit.dataset_loader import TripDataset  # noqa: E402
from core.challenge1_road.depth import StereoDepth  # noqa: E402

FX = 320.0
CX = 320.0
HALF_W = 2.6
Z_MIN, Z_MAX = 1.0, 40.0
BIN_SIZE = 0.3
MIN_PIXELS = 30
TRACK_MATCH_Z = 2.5   # metres
TRACK_MATCH_X = 1.2   # metres
HIST_WINDOW = 8
MIN_APPROACH_SPEED = 0.5  # m/s
# A regression slope can look like "approaching" from noise alone over a
# short/sparse window (this is exactly what happened at T02 f325-340: a
# real object sitting at near-zero true closing speed still produced a
# small positive slope). Require the depth to have dropped by a minimum
# ABSOLUTE amount across the window, not just a noisy slope sign, before
# trusting the closing-speed estimate.
MIN_TOTAL_DROP_M = 1.2
HOLD_FRAMES = 6


def find_depth_blobs(depth_map: np.ndarray):
    h, w = depth_map.shape
    v, u = np.mgrid[0:h, 0:w]
    Z = depth_map
    valid = np.isfinite(Z) & (Z > Z_MIN) & (Z < Z_MAX)
    X = (u - CX) * Z / FX
    corridor = valid & (np.abs(X) < HALF_W)
    if not corridor.any():
        return []
    zs, us, vs, xs = Z[corridor], u[corridor], v[corridor], X[corridor]
    bins = np.round(zs / BIN_SIZE).astype(int)
    blobs = []
    for b in np.unique(bins):
        m = bins == b
        if m.sum() < MIN_PIXELS:
            continue
        blobs.append({
            "z": float(np.median(zs[m])), "x": float(np.median(xs[m])),
            "cx": float(np.median(us[m])), "cy": float(np.median(vs[m])),
            "size": int(m.sum()),
        })
    return blobs


class GeoTrack:
    def __init__(self, z, x, t):
        self.hist = [(t, z, x)]

    def update(self, z, x, t):
        self.hist.append((t, z, x))
        if len(self.hist) > HIST_WINDOW:
            self.hist.pop(0)

    def closing_speed(self):
        if len(self.hist) < 3:
            return None
        ts = np.array([p[0] for p in self.hist])
        zs = np.array([p[1] for p in self.hist])
        if ts.max() - ts.min() < 1e-3:
            return None
        if zs.max() - zs.min() < MIN_TOTAL_DROP_M:
            return None  # noise floor -- not a confidently-approaching trend
        A = np.vstack([ts, np.ones_like(ts)]).T
        slope, _ = np.linalg.lstsq(A, zs, rcond=None)[0]
        return -float(slope)

    @property
    def last(self):
        return self.hist[-1]


def run_region(trip_dir: Path, f_lo: int, f_hi: int, verbose=True):
    """Full geo-detector eval WITH stereo fallback on non-keyframes and
    output-level temporal hold, for a fair apples-to-apples comparison
    against the main pipeline's region numbers."""
    ds = TripDataset(trip_dir)
    depth_dir = trip_dir / "kitti" / "depth"
    calib = ds.load_calibration()
    stereo = StereoDepth(float(calib["K_left"][0][0]), float(calib["baseline_m"]))

    tracks: list[GeoTrack] = []
    last_finite_ttc, last_finite_t, gap_count = float("inf"), 0.0, 0
    errs, tp, fp, fn = [], 0, 0, 0

    for fr in ds.iter_frames():
        if fr.frame_id < f_lo or fr.frame_id > f_hi:
            continue
        p = depth_dir / f"{fr.frame_id:06d}.npy"
        if p.exists():
            depth = np.load(p).astype(np.float32)
            depth[depth >= 60.0] = np.inf
        else:
            left, right = ds.load_left(fr.frame_id), ds.load_right(fr.frame_id)
            depth = stereo.depth_map(stereo.disparity(left, right))

        blobs = find_depth_blobs(depth)
        used = set()
        for tr in tracks:
            lz, lx = tr.last[1], tr.last[2]
            best_i, best_d = None, 1e9
            for i, b in enumerate(blobs):
                if i in used:
                    continue
                d = abs(b["z"] - lz) / TRACK_MATCH_Z + abs(b["x"] - lx) / TRACK_MATCH_X
                if d < best_d and abs(b["z"] - lz) < TRACK_MATCH_Z and abs(b["x"] - lx) < TRACK_MATCH_X:
                    best_d, best_i = d, i
            if best_i is not None:
                tr.update(blobs[best_i]["z"], blobs[best_i]["x"], fr.timestamp)
                used.add(best_i)
        for i, b in enumerate(blobs):
            if i not in used:
                tracks.append(GeoTrack(b["z"], b["x"], fr.timestamp))
        tracks[:] = [tr for tr in tracks if fr.timestamp - tr.last[0] < 0.3]

        raw_ttc = float("inf")
        for tr in tracks:
            if tr.last[0] != fr.timestamp:
                continue
            speed = tr.closing_speed()
            if speed is None or speed < MIN_APPROACH_SPEED:
                continue
            ttc = tr.last[1] / speed
            raw_ttc = min(raw_ttc, ttc)

        # output-level temporal hold (same policy as main pipeline)
        if math.isfinite(raw_ttc):
            last_finite_ttc, last_finite_t, gap_count = raw_ttc, fr.timestamp, 0
            pred = raw_ttc
        elif gap_count < HOLD_FRAMES and math.isfinite(last_finite_ttc):
            held = last_finite_ttc - (fr.timestamp - last_finite_t)
            pred = held if held > 0.1 else float("inf")
            if held > 0.1:
                gap_count += 1
        else:
            pred = float("inf")

        gt = fr.min_ttc
        if math.isfinite(gt) and gt < 3.0:
            errs.append(abs((pred if math.isfinite(pred) else 99.0) - gt))
        pd_, gd = (math.isfinite(pred) and pred < 2.0), (math.isfinite(gt) and gt < 2.0)
        if pd_ and gd:
            tp += 1
        elif pd_ and not gd:
            fp += 1
        elif gd and not pd_:
            fn += 1

    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0.0
    mae = sum(errs) / len(errs) if errs else float("nan")
    if verbose:
        print(f"{trip_dir.name} [{f_lo}-{f_hi}]: MAE-crit={mae:.2f} n={len(errs)} "
              f"F1={f1:.2f} (tp{tp} fp{fp} fn{fn})")
    return mae, f1


if __name__ == "__main__":
    base = AI_ROOT / "Dataset" / "Dataset" / "Practice_Dataset 2"
    run_region(base / "T02-Sample", 280, 340)
