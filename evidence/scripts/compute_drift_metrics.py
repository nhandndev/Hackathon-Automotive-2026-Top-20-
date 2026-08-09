"""
E-42: Model drift / domain gap (Tam/Hung).

Quantifies the visual/statistical domain shift between the two Challenge 1
training sources that scripts/prepare_yolo_finetune.py mixes:
  - "practice"   = Practice_Dataset (6 trips) + extra_trips -- CARLA 0.9.15
                   (UE4), the domain the real BTC-scored trips are rendered
                   in. This is what yolov8s_finetuned_carla_v2.pt (the
                   production model, 73.6/72.4 composite) was trained on.
  - "data_train" = Data_train (50 trips) -- CARLA 0.10.0 (UE5). Three
                   separate fine-tune attempts that mixed this source in
                   (v3/v4/v5) all regressed the composite score vs v2; see
                   evidence/05_model_ablation/domain_gap_report.md for the
                   full experiment trail and the concrete failure mechanism
                   found on trip T01 (a v5 false "danger" TTC=0.34s alarm
                   on a correctly-detected but off-path parked truck).

Source images: the original Data_train/ directory was not present on disk
at the time this was run (see domain_gap_report.md for provenance notes),
but scripts/prepare_yolo_finetune.py's output at
datasets/yolo_finetune/images/{train,val}/ retains a physical copy of every
frame it drew from, prefixed by source folder name ("Data_train_...",
"Practice_Dataset_...", "extra_trips_..."), which this script uses instead.

Metrics: Population Stability Index (PSI) and two-sample Kolmogorov-Smirnov
test, computed per feature:
  - mean_luminance   : mean grayscale pixel value per frame (lighting/
                        time-of-day shift)
  - boxes_per_frame  : object count per labeled frame (scene density)
  - box_height_norm  : YOLO-normalized box height across all boxes (object
                        scale/depth distribution)

PSI rule of thumb: <0.1 no significant shift, 0.1-0.25 moderate shift,
>0.25 major shift (standard credit-risk-modeling convention, reused here
since there's no CARLA-specific convention).
"""

import csv
import os
import random
import sys

import cv2
import numpy as np
from scipy.stats import ks_2samp

random.seed(0)

AI_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "HACKATHON", "AI")
IMG_DIR = os.path.join(AI_ROOT, "datasets", "yolo_finetune", "images", "train")
LBL_DIR = os.path.join(AI_ROOT, "datasets", "yolo_finetune", "labels", "train")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "05_model_ablation")
SAMPLE_N = 400  # per domain, for the luminance pass (full population used for box stats)


def domain_of(fname: str) -> str:
    if fname.startswith("Data_train_"):
        return "data_train"
    if fname.startswith("Practice_Dataset_") or fname.startswith("extra_trips_"):
        return "practice"
    return "other"


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """PSI of `actual` vs `expected`, using `expected`'s decile edges."""
    edges = np.quantile(expected, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    edges = np.unique(edges)
    exp_counts, _ = np.histogram(expected, bins=edges)
    act_counts, _ = np.histogram(actual, bins=edges)
    exp_pct = np.clip(exp_counts / max(len(expected), 1), 1e-6, None)
    act_pct = np.clip(act_counts / max(len(actual), 1), 1e-6, None)
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def main():
    if not os.path.isdir(IMG_DIR):
        print(f"FATAL: {IMG_DIR} not found -- run scripts/prepare_yolo_finetune.py first.")
        sys.exit(1)

    all_files = os.listdir(IMG_DIR)
    by_domain = {"practice": [], "data_train": []}
    for f in all_files:
        d = domain_of(f)
        if d in by_domain:
            by_domain[d].append(f)

    print(f"practice frames: {len(by_domain['practice'])}, data_train frames: {len(by_domain['data_train'])}")

    # --- Feature 1: mean luminance (sampled, image decode is the bottleneck) ---
    lum = {"practice": [], "data_train": []}
    for dom in ("practice", "data_train"):
        sample = random.sample(by_domain[dom], min(SAMPLE_N, len(by_domain[dom])))
        for f in sample:
            img = cv2.imread(os.path.join(IMG_DIR, f), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                lum[dom].append(float(img.mean()))

    # --- Feature 2 & 3: boxes/frame and normalized box height (full population, label files are cheap) ---
    density = {"practice": [], "data_train": []}
    box_h = {"practice": [], "data_train": []}
    for dom in ("practice", "data_train"):
        for f in by_domain[dom]:
            lbl_path = os.path.join(LBL_DIR, os.path.splitext(f)[0] + ".txt")
            n = 0
            if os.path.exists(lbl_path):
                with open(lbl_path, "r", encoding="utf-8") as lf:
                    for line in lf:
                        parts = line.split()
                        if len(parts) == 5:
                            n += 1
                            box_h[dom].append(float(parts[4]))  # yolo: cls cx cy w h
            density[dom].append(n)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_csv = os.path.join(OUT_DIR, "psi_ks_metrics.csv")
    rows = []
    for name, (a, b) in {
        "mean_luminance": (lum["practice"], lum["data_train"]),
        "boxes_per_frame": (density["practice"], density["data_train"]),
        "box_height_norm": (box_h["practice"], box_h["data_train"]),
    }.items():
        a_arr, b_arr = np.array(a), np.array(b)
        ks_stat, ks_p = ks_2samp(a_arr, b_arr)
        rows.append({
            "feature": name,
            "practice_n": len(a_arr),
            "practice_mean": round(float(a_arr.mean()), 4),
            "practice_std": round(float(a_arr.std()), 4),
            "data_train_n": len(b_arr),
            "data_train_mean": round(float(b_arr.mean()), 4),
            "data_train_std": round(float(b_arr.std()), 4),
            "psi_data_train_vs_practice": round(psi(a_arr, b_arr), 4),
            "ks_statistic": round(float(ks_stat), 4),
            "ks_pvalue": float(ks_p),
        })
        print(rows[-1])

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {out_csv}")


if __name__ == "__main__":
    main()
