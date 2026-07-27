"""
Output-calibration search with honest leave-one-trip-out validation.

All three scoring terms are functions of the single number we emit, so the
mapping from the pipeline's internal TTC to the submitted value is itself a
tunable. This searches a 3-parameter monotone transform:

    scale  -- multiply sub-3s readings (moves the F1 decision boundary and
              the inverse-TTC magnitude where GT is smallest)
    demote -- value substituted for an unconfirmed danger reading
    floor  -- value substituted for "nothing tracked"

Fitting these on all six trips would just be overfitting the practice set,
so every configuration is scored leave-one-trip-out: parameters are chosen
on five trips and applied to the sixth. The LOTO average is what gets
reported; the all-trips number is printed only to show the gap.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np

AI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI / "Dataset/Dataset/Package_starterkit/package_starterkit"))
from team_kit.dataset_loader import TripDataset  # noqa: E402

DEMOTE_SENTINEL = 2.5
FLOOR_SENTINEL = 12.0


def composite(pred: np.ndarray, gt: np.ndarray) -> float:
    INF = 99.0
    g = np.where(np.isfinite(gt), gt, INF)
    p = np.where(np.isfinite(pred), pred, INF)
    crit = g < 3.0
    mae = np.abs(p[crit] - g[crit]).mean() if crit.any() else float("nan")
    ip = np.where(p > 0.1, 1.0 / np.maximum(p, 0.1), 10.0)
    ip[~np.isfinite(pred)] = 0.0
    ig = np.where(g > 0.1, 1.0 / np.maximum(g, 0.1), 10.0)
    ig[~np.isfinite(gt)] = 0.0
    inv = np.abs(ip - ig).mean()
    pd_, gd = p < 2.0, g < 2.0
    tp = int((pd_ & gd).sum()); fp = int((pd_ & ~gd).sum()); fn = int((~pd_ & gd).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    ms = 50.0 if math.isnan(mae) else max(0.0, 100 - 20 * mae)
    return 0.40 * ms + 0.30 * 100 * f1 + 0.30 * max(0.0, 100 - 200 * inv)


def apply_map(p: np.ndarray, scale: float, demote: float, floor: float) -> np.ndarray:
    q = p.copy()
    is_dem = np.isclose(q, DEMOTE_SENTINEL)
    is_flo = np.isclose(q, FLOOR_SENTINEL)
    real = np.isfinite(q) & ~is_dem & ~is_flo
    small = real & (q < 3.0)
    q[small] = q[small] * scale
    q[is_dem] = demote
    q[is_flo] = floor
    return q


def load():
    base = AI / "Dataset/Dataset/Practice_Dataset 2"
    data = []
    for t in sorted(base.iterdir()):
        if not t.is_dir():
            continue
        c = AI / "predictions/FPTU_DMS_Vision" / f"{t.name}.csv"
        if not c.exists():
            continue
        pr = {}
        for r in csv.DictReader(open(c)):
            v = r["predicted_ttc"].strip().lower()
            pr[int(r["frame_id"])] = float("inf") if v in ("inf", "") else float(v)
        ds = TripDataset(t)
        ids = [f.frame_id for f in ds.iter_frames()]
        data.append((
            t.name,
            np.array([pr.get(i, float("inf")) for i in ids]),
            np.array([f.min_ttc for f in ds.iter_frames()]),
        ))
    return data


def main() -> int:
    data = load()
    grid = [
        (s, d, f)
        for s in [0.7, 0.85, 1.0, 1.2, 1.5]
        for d in [2.1, 2.5, 3.0, 4.0]
        for f in [8.0, 12.0, 16.0, 22.0]
    ]

    base_avg = np.mean([composite(p, g) for _, p, g in data])
    print(f"baseline (scale=1, demote=2.5, floor=12): {base_avg:.1f}")

    # --- leave-one-trip-out ---
    loto = []
    for i, (name, p_te, g_te) in enumerate(data):
        train = [d for j, d in enumerate(data) if j != i]
        best, best_s = None, -1.0
        for cfg in grid:
            s = np.mean([composite(apply_map(p, *cfg), g) for _, p, g in train])
            if s > best_s:
                best_s, best = s, cfg
        held = composite(apply_map(p_te, *best), g_te)
        loto.append(held)
        print(f"  hold-out {name[:11]:11s} chose scale={best[0]} demote={best[1]} "
              f"floor={best[2]} -> {held:.1f}")
    print(f"\nLOTO AVERAGE: {np.mean(loto):.1f}   (baseline {base_avg:.1f})")

    # --- best on all six, for reference only (optimistic) ---
    best, best_s = None, -1.0
    for cfg in grid:
        s = np.mean([composite(apply_map(p, *cfg), g) for _, p, g in data])
        if s > best_s:
            best_s, best = s, cfg
    print(f"best-on-all (optimistic): scale={best[0]} demote={best[1]} floor={best[2]} -> {best_s:.1f}")
    per = [composite(apply_map(p, *best), g) for _, p, g in data]
    print("   " + "  ".join(f"{n[:3]}={x:.1f}" for (n, _, _), x in zip(data, per)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
