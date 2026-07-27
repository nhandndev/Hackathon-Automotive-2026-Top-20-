"""
Honest leave-one-trip-out validation of the post-processing knobs
(hold_frames, no_detection_floor, danger_confirm_frames/band, demote_to).

Why this exists: these values were previously chosen by grid-searching
directly on all 6 practice trips (or worse, on a CSV that already had one
fixed confirm-filter baked in -- a circular test). That is exactly the
overfitting risk file 04 warns about: a configuration that looks great on
the 6 practice trips can be worse on the 10 organizer-scored trips, which
are longer (90s vs 30s) and busier.

This replicates predict_ttc.py's post-processing EXACTLY, starting from the
raw per-frame engine output (`fused_ttc` in the feature parquet -- captured
BEFORE hold/floor/confirm), so there is no circularity. For each held-out
trip, the config is chosen using only the other five, then applied to the
sixth and scored. The LOTO average is the honest estimate of what a fresh,
unseen trip (like the organizer's T0Xd) should score.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AI = Path(__file__).resolve().parents[1]
FEAT = AI / "artifacts" / "features" / "all_trips.parquet"


def composite(pred: np.ndarray, gt: np.ndarray) -> float:
    INF = 99.0
    g = np.where(np.isfinite(gt), gt, INF)
    p = np.where(np.isfinite(pred), pred, INF)
    crit = g < 3.0
    mae = np.abs(p[crit] - g[crit]).mean() if crit.any() else float("nan")
    ip = np.where(p > 0.1, 1.0 / np.maximum(p, 0.1), 10.0); ip[~np.isfinite(pred)] = 0.0
    ig = np.where(g > 0.1, 1.0 / np.maximum(g, 0.1), 10.0); ig[~np.isfinite(gt)] = 0.0
    inv = np.abs(ip - ig).mean()
    pd_, gd = p < 2.0, g < 2.0
    tp = int((pd_ & gd).sum()); fp = int((pd_ & ~gd).sum()); fn = int((~pd_ & gd).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    ms = 50.0 if math.isnan(mae) else max(0.0, 100 - 20 * mae)
    return 0.40 * ms + 0.30 * 100 * f1 + 0.30 * max(0.0, 100 - 200 * inv)


def postprocess(raw_ttc, ts, hold_frames, floor, confirm_frames, confirm_band, demote_to):
    """Exact reproduction of predict_ttc.py's _apply_hold -> _smooth_out
    (median window is 1 = no-op in the committed config, omitted here) ->
    floor -> _confirm_danger, run causally frame-by-frame."""
    n = len(raw_ttc)
    out = np.empty(n)
    last_finite_ttc, last_finite_t, gap_count = float("inf"), 0.0, 0
    recent: list = []
    for i in range(n):
        ttc = raw_ttc[i]
        t = ts[i]
        # hold
        if math.isfinite(ttc):
            last_finite_ttc, last_finite_t, gap_count = ttc, t, 0
            held = ttc
        elif gap_count < hold_frames and math.isfinite(last_finite_ttc):
            h = last_finite_ttc - (t - last_finite_t)
            if h > 0.1:
                gap_count += 1
                held = h
            else:
                held = float("inf")
        else:
            held = float("inf")
        # floor
        val = floor if (not math.isfinite(held) and floor > 0) else held
        # confirm
        if confirm_frames > 0 and math.isfinite(val) and val < 2.0:
            if len(recent) < confirm_frames:
                val = demote_to
            elif not all(math.isfinite(v) and v < confirm_band for v in recent[-confirm_frames:]):
                val = demote_to
        recent.append(val)
        out[i] = val
    return out


def main() -> int:
    df = pd.read_parquet(FEAT)
    trips = sorted(df["trip_id"].unique())
    raw = {t: df.loc[df.trip_id == t].sort_values("frame_id") for t in trips}
    for t in raw:
        raw[t] = raw[t].assign(ts=raw[t]["frame_id"] * 0.05)

    committed = dict(hold_frames=6, floor=12.0, confirm_frames=8, confirm_band=3.0, demote_to=2.5)

    def score(cfg, trip):
        d = raw[trip]
        pred = postprocess(d["fused_ttc"].where(d["fused_ttc"] < 90, np.inf).values,
                            d["ts"].values, **cfg)
        return composite(pred, d["gt_ttc"].values)

    print("Sanity -- committed config per trip (should roughly match the live pipeline):")
    committed_scores = [score(committed, t) for t in trips]
    for t, s in zip(trips, committed_scores):
        print(f"  {t:12s} {s:5.1f}")
    print(f"  AVG (all 6, committed config): {np.mean(committed_scores):.1f}\n")

    grid = [
        dict(hold_frames=hf, floor=fl, confirm_frames=cf, confirm_band=cb, demote_to=dt)
        for hf in [4, 6, 10]
        for fl in [10.0, 12.0, 15.0, 20.0]
        for cf in [5, 8, 12]
        for cb in [3.0, 5.0]
        for dt in [2.5, 3.0]
    ]
    print(f"Grid size: {len(grid)} configs x 6 folds\n")

    loto_scores = []
    chosen = []
    for held_out in trips:
        train = [t for t in trips if t != held_out]
        best_cfg, best_avg = None, -1.0
        for cfg in grid:
            avg = np.mean([score(cfg, t) for t in train])
            if avg > best_avg:
                best_avg, best_cfg = avg, cfg
        held_score = score(best_cfg, held_out)
        loto_scores.append(held_score)
        chosen.append(best_cfg)
        print(f"hold-out {held_out:12s} chosen={best_cfg} -> {held_score:.1f}")

    print(f"\nLOTO AVERAGE (honest, unseen-trip estimate): {np.mean(loto_scores):.1f}")
    print(f"Committed-config average on all 6 (in-sample):  {np.mean(committed_scores):.1f}")

    # Best on all six (upper-bound / optimistic, for reference)
    best_all_cfg, best_all = None, -1.0
    for cfg in grid:
        avg = np.mean([score(cfg, t) for t in trips])
        if avg > best_all:
            best_all, best_all_cfg = avg, cfg
    print(f"Best-on-all-6 (optimistic, DO NOT use as the real estimate): {best_all_cfg} -> {best_all:.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
