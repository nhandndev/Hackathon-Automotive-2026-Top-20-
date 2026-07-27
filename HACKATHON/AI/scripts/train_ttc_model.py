"""
Direction A — learned TTC model, step 2: train + honest evaluation.

Trains an XGBoost regressor on the pipeline features (extract_features.py)
to predict inverse-TTC (u = 1/ttc, with no-target → 0). Inverse-TTC is the
right target: it is bounded, handles the inf case cleanly, and matches the
scoring's own inverse-TTC term while emphasising small (dangerous) TTC.

Reports leave-one-trip-out cross-validation — for each trip, train on the
other five and score the held-out trip with the organizer's composite
formula. This is the anti-overfit check (file 04): a trip is never in its
own training set, so the average LOTO composite is an honest estimate of
what the model will do on the redacted scored trips. A final model trained
on all six trips is then saved for deployment.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

AI_ROOT = Path(__file__).resolve().parents[1]
FEAT = AI_ROOT / "artifacts" / "features" / "all_trips.parquet"
MODEL_OUT = AI_ROOT / "artifacts" / "ttc_model.json"

FEATURE_COLS = [
    "ego_speed_kmh", "ego_long_accel", "ego_lat_accel",
    "n_obs", "n_in_cone", "min_z_cone", "min_z_any",
    "min_stereo_ttc", "min_looming_ttc", "fused_ttc",
    "cand_ttc", "cand_z", "cand_xlat_abs", "cand_h", "cand_closing",
    "cand_in_cone", "cand_looming",
]

XGB_PARAMS = dict(
    objective="reg:squarederror",
    max_depth=4,            # shallow → resist overfit on 6 trips
    eta=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    seed=0,
)
NUM_ROUNDS = 400


# ---- organizer composite (mirrors team_kit/evaluation.py) -----------------
def composite(pred_ttc: np.ndarray, gt_ttc: np.ndarray) -> dict:
    INF = 99.0
    gt = np.where(np.isfinite(gt_ttc), gt_ttc, INF)
    pr = np.where(np.isfinite(pred_ttc), pred_ttc, INF)

    crit = gt < 3.0
    if crit.any():
        mae_crit = float(np.abs(np.clip(pr[crit], 0, INF) - gt[crit]).mean())
    else:
        mae_crit = float("nan")

    inv_p = np.where(pr > 0.1, 1.0 / pr, 1.0 / 0.1); inv_p[pr >= INF] = 0.0
    inv_g = np.where(gt > 0.1, 1.0 / gt, 1.0 / 0.1); inv_g[gt >= INF] = 0.0
    inv_mae = float(np.abs(inv_p - inv_g).mean())

    pd_ = pr < 2.0; gd = gt < 2.0
    tp = int((pd_ & gd).sum()); fp = int((pd_ & ~gd).sum()); fn = int((~pd_ & gd).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0

    mae_score = 50.0 if math.isnan(mae_crit) else max(0.0, 100 - 20 * mae_crit)
    comp = 0.40 * mae_score + 0.30 * (100 * f1) + 0.30 * max(0.0, 100 - 200 * inv_mae)
    return {"mae_crit": mae_crit, "f1": f1, "inv": inv_mae, "composite": comp}


def u_to_ttc(u: np.ndarray) -> np.ndarray:
    u = np.clip(u, 0.0, None)
    ttc = np.where(u > 1e-3, 1.0 / np.maximum(u, 1e-3), np.inf)
    return ttc


def main() -> int:
    df = pd.read_parquet(FEAT)
    X = df[FEATURE_COLS].astype(float).values
    y = df["gt_inv_ttc"].astype(float).values
    trips = df["trip_id"].values
    uniq = sorted(set(trips))

    print("=== Leave-one-trip-out CV ===")
    # Heuristic inverse-TTC per frame = 1 / fused_ttc (fused_ttc==99 -> ~0).
    u_heur_all = 1.0 / np.clip(df["fused_ttc"].astype(float).values, 0.1, None)

    weights = [0.0, 0.25, 0.5, 0.75, 1.0]  # weight on the MODEL in the inv-TTC blend
    print("=== Leave-one-trip-out CV (heuristic w=0 .. model w=1) ===")
    per_w = {w: [] for w in weights}
    for test_trip in uniq:
        te = trips == test_trip
        tr = ~te
        booster = xgb.train(XGB_PARAMS, xgb.DMatrix(X[tr], label=y[tr]), NUM_ROUNDS)
        u_model = np.clip(booster.predict(xgb.DMatrix(X[te])), 0.0, None)
        u_heur = u_heur_all[te]
        gt_ttc = df.loc[te, "gt_ttc"].values
        line = [f"  {test_trip}:"]
        for w in weights:
            m = composite(u_to_ttc(w * u_model + (1 - w) * u_heur), gt_ttc)
            per_w[w].append(m["composite"])
            line.append(f"w{w}={m['composite']:.1f}")
        print(" ".join(line), flush=True)

    print("\n=== Average composite by ensemble weight ===")
    best_w, best_avg = 0.0, -1.0
    for w in weights:
        avg = float(np.mean(per_w[w]))
        note = "  (w0=heuristic-only, w1=model-only)" if w in (0.0, 1.0) else ""
        print(f"  w_model={w}: AVG = {avg:.1f}{note}")
        if avg > best_avg:
            best_avg, best_w = avg, w
    print(f"\nBEST ensemble weight w_model={best_w}  ->  AVG composite {best_avg:.1f} / 100")

    # Final model on all trips for deployment on the redacted scored trips.
    final = xgb.train(XGB_PARAMS, xgb.DMatrix(X, label=y), NUM_ROUNDS)
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    final.save_model(str(MODEL_OUT))
    print(f"\nSaved model -> {MODEL_OUT.name} (deploy with ensemble w_model={best_w})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
