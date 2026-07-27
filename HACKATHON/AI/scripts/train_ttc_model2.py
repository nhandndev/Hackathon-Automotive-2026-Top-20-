"""
Learned TTC head, second attempt -- on the post-fix pipeline.

The first attempt (train_ttc_model.py) lost to the heuristic, but it ran on
features produced before the GT-depth wiring and the tracker fix, when the
inputs themselves were badly corrupted. It is worth re-running now for a
specific reason: every hand-written threshold tried since has failed to
separate genuine threats from "phantoms" (roadside/oncoming vehicles we are
merely approaching), because both share the same noisy geometry. That is a
decision boundary a model can learn and a single threshold cannot.

Two changes over attempt one:
  * TEMPORAL CONTEXT. What actually distinguishes a real approach from a
    phantom is how the evidence evolves -- a real threat's range collapses
    monotonically while a phantom's does not. Per-frame features cannot see
    that, so lags and deltas of the key signals are added here.
  * Blending against the heuristic is swept, and everything is scored
    leave-one-trip-out, so the reported number is not fitted to the trip it
    is measured on.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

AI = Path(__file__).resolve().parents[1]
FEAT = AI / "artifacts" / "features" / "all_trips.parquet"
PRED_DIR = AI / "predictions" / "FPTU_DMS_Vision"
MODEL_OUT = AI / "artifacts" / "ttc_model2.json"


def load_submitted_ttc(trip_id: str) -> dict:
    """The actual per-frame value in the submitted CSV -- i.e. AFTER the
    no-detection floor, temporal hold and danger-confirmation filter. This
    is the correct 'w=0 heuristic' baseline; the raw engine fused_ttc
    feature is NOT, since it is captured before that post-processing."""
    out = {}
    with open(PRED_DIR / f"{trip_id}.csv") as f:
        for row in csv.DictReader(f):
            v = row["predicted_ttc"].strip().lower()
            out[int(row["frame_id"])] = float("inf") if v in ("inf", "") else float(v)
    return out

BASE_COLS = [
    "ego_speed_kmh", "ego_long_accel", "ego_lat_accel",
    "n_obs", "n_in_cone", "min_z_cone", "min_z_any",
    "min_stereo_ttc", "min_looming_ttc", "fused_ttc",
    "cand_ttc", "cand_z", "cand_xlat_abs", "cand_h", "cand_closing",
    "cand_in_cone", "cand_looming",
]
LAG_COLS = ["fused_ttc", "cand_z", "cand_closing", "cand_h", "n_in_cone", "cand_xlat_abs"]
LAGS = [1, 2, 4, 8]

XGB_PARAMS = dict(
    objective="reg:squarederror",
    max_depth=4, eta=0.05, subsample=0.8, colsample_bytree=0.8,
    min_child_weight=5, seed=0,
)
NUM_ROUNDS = 400


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


def u_to_ttc(u: np.ndarray) -> np.ndarray:
    u = np.clip(u, 0.0, None)
    return np.where(u > 1e-3, 1.0 / np.maximum(u, 1e-3), np.inf)


def build(df: pd.DataFrame) -> pd.DataFrame:
    """Add per-trip temporal context (lags + deltas)."""
    out = []
    for trip, g in df.groupby("trip_id", sort=True):
        g = g.sort_values("frame_id").copy()
        for c in LAG_COLS:
            for L in LAGS:
                g[f"{c}_lag{L}"] = g[c].shift(L).fillna(g[c].iloc[0] if len(g) else 0.0)
                g[f"{c}_d{L}"] = g[c] - g[f"{c}_lag{L}"]
        out.append(g)
    return pd.concat(out, ignore_index=True)


def main() -> int:
    df = build(pd.read_parquet(FEAT))
    cols = BASE_COLS + [c for c in df.columns if any(
        c.startswith(f"{b}_lag") or c.startswith(f"{b}_d") for b in LAG_COLS)]
    X = df[cols].astype(float).values
    y = df["gt_inv_ttc"].astype(float).values
    trips = df["trip_id"].values
    uniq = sorted(set(trips))

    # Correct heuristic baseline: the actually-submitted per-frame TTC (post
    # floor/hold/confirm), not the pre-post-processing engine snapshot.
    submitted_ttc = np.empty(len(df))
    for tid in uniq:
        m = (trips == tid)
        sub = load_submitted_ttc(tid)
        submitted_ttc[m] = [sub.get(int(fid), float("inf")) for fid in df.loc[m, "frame_id"]]
    u_heur = 1.0 / np.clip(submitted_ttc, 0.1, None)
    u_heur[~np.isfinite(submitted_ttc)] = 0.0

    sanity = np.mean([
        composite(u_to_ttc(u_heur[trips == tid]), df.loc[trips == tid, "gt_ttc"].values)
        for tid in uniq
    ])
    print(f"sanity check -- submitted-CSV composite reproduced here: {sanity:.1f} (should be ~65.4)")

    print(f"{len(df)} frames, {len(cols)} features (incl. temporal context)")
    weights = [0.0, 0.2, 0.35, 0.5, 0.7, 1.0]
    per_w = {w: [] for w in weights}
    for te_trip in uniq:
        te = trips == te_trip
        bst = xgb.train(XGB_PARAMS, xgb.DMatrix(X[~te], label=y[~te]), NUM_ROUNDS)
        um = np.clip(bst.predict(xgb.DMatrix(X[te])), 0.0, None)
        gt = df.loc[te, "gt_ttc"].values
        line = [f"  {te_trip[:11]:11s}"]
        for w in weights:
            c = composite(u_to_ttc(w * um + (1 - w) * u_heur[te]), gt)
            per_w[w].append(c)
            line.append(f"w{w}={c:5.1f}")
        print(" ".join(line), flush=True)

    print("\nLOTO average by model weight:")
    best_w, best_avg = 0.0, -1.0
    for w in weights:
        a = float(np.mean(per_w[w]))
        tag = "  <- heuristic only" if w == 0.0 else ("  <- model only" if w == 1.0 else "")
        print(f"  w={w}: {a:5.1f}{tag}")
        if a > best_avg:
            best_avg, best_w = a, w
    print(f"\nBEST: w={best_w} -> LOTO {best_avg:.1f}")

    final = xgb.train(XGB_PARAMS, xgb.DMatrix(X, label=y), NUM_ROUNDS)
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    final.save_model(str(MODEL_OUT))
    imp = sorted(final.get_score(importance_type="gain").items(), key=lambda kv: -kv[1])[:10]
    print("Top features:", ", ".join(f"{k}={v:.0f}" for k, v in imp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
