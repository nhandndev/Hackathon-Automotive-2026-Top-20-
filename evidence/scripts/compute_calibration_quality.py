"""
E-37: Calibration quality (Tam, supporting: Dan).

Parses the real per-trip calibration manifests (`kitti/calibration_info.txt`
+ per-frame `kitti/calib/*.txt`, KITTI format) shipped with every Challenge 1
trip, computes the baseline distribution across trips AND across every frame
within each trip (not just spot-checked), and renders an epipolar-line
montage over one representative frame per trip so misalignment (bad
rectification) would be visible by eye: a corresponding real-world point
must land on the same horizontal scanline in both the left and right image.

Ran via a repo read-only scan first (see domain_gap_report.md siblings for
that context) which reported no manifest/generation script found -- that
scan did not look inside Practice_Dataset/*/kitti/, where the manifests
actually live. This script fixes that: it reads the real, per-frame
calibration files that scripts/eval_practice.py already depends on via
TripDataset.load_calibration(), so this IS the same calibration data driving
the production Challenge 1 composite score (73.6/100), not a separate/mocked
source.

Usage: run with cwd = repo root.
"""

import glob
import json
import os

import cv2
import numpy as np

AI_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "HACKATHON", "AI")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "06_calibration_quality")

TRIP_GLOBS = [
    os.path.join(AI_ROOT, "Practice_Dataset", "Practice_Dataset", "*-Sample"),
    os.path.join(AI_ROOT, "extra_trips", "*-Sample*"),
]


def find_trips():
    trips = []
    for pattern in TRIP_GLOBS:
        for d in sorted(glob.glob(pattern)):
            if os.path.isdir(os.path.join(d, "kitti")):
                trips.append(d)
    return trips


def parse_kitti_calib(path):
    """Return dict of matrix-name -> flat float list, KITTI calib format."""
    out = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, vals = line.split(":", 1)
            out[key.strip()] = [float(v) for v in vals.split()]
    return out


def baseline_from_kitti(calib):
    """baseline_m = -Tx(P3) / fx(P2), the standard KITTI stereo convention."""
    p2, p3 = calib["P2"], calib["P3"]
    fx = p2[0]
    tx3 = p3[3]
    return -tx3 / fx if fx else float("nan")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    trips = find_trips()
    if not trips:
        print("FATAL: no trips found under Practice_Dataset/extra_trips.")
        return

    # --- 1. Baseline distribution: manifest-level (1 value/trip) + per-frame (every calib/*.txt) ---
    manifest_rows = []
    per_frame_baselines = []
    for trip_dir in trips:
        trip_id = os.path.basename(trip_dir)
        info_path = os.path.join(trip_dir, "kitti", "calibration_info.txt")
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        manifest_rows.append({
            "trip_id": trip_id,
            "baseline_m": info["baseline_m"],
            "fov_deg": info["fov_deg"],
            "image_width": info["image_width"],
            "image_height": info["image_height"],
        })

        calib_files = sorted(glob.glob(os.path.join(trip_dir, "kitti", "calib", "*.txt")))
        for cf in calib_files:
            calib = parse_kitti_calib(cf)
            if "P2" in calib and "P3" in calib:
                b = baseline_from_kitti(calib)
                per_frame_baselines.append((trip_id, os.path.basename(cf), b))

    per_frame_arr = np.array([b for _, _, b in per_frame_baselines])
    print(f"Manifests: {len(manifest_rows)} trips. Per-frame calib files parsed: {len(per_frame_baselines)}")
    print(f"Per-frame baseline_m: mean={per_frame_arr.mean():.6f} std={per_frame_arr.std():.6f} "
          f"min={per_frame_arr.min():.6f} max={per_frame_arr.max():.6f}")

    import csv
    dist_csv = os.path.join(OUT_DIR, "baseline_distribution.csv")
    with open(dist_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["trip_id", "baseline_m", "fov_deg", "image_width", "image_height"])
        w.writeheader()
        w.writerows(manifest_rows)
    print(f"Wrote {dist_csv}")

    per_frame_csv = os.path.join(OUT_DIR, "baseline_per_frame.csv")
    with open(per_frame_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trip_id", "frame_file", "baseline_m_computed"])
        w.writerows(per_frame_baselines)
    print(f"Wrote {per_frame_csv} ({len(per_frame_baselines)} rows)")

    summary_txt = os.path.join(OUT_DIR, "baseline_summary.txt")
    with open(summary_txt, "w", encoding="utf-8") as f:
        f.write(f"Trips covered: {len(manifest_rows)}\n")
        f.write(f"Per-frame calib files parsed: {len(per_frame_baselines)}\n")
        f.write(f"Per-frame baseline_m: mean={per_frame_arr.mean():.6f} "
                f"std={per_frame_arr.std():.6f} min={per_frame_arr.min():.6f} "
                f"max={per_frame_arr.max():.6f}\n")
        f.write("Manifest-level baseline_m per trip:\n")
        for r in manifest_rows:
            f.write(f"  {r['trip_id']}: {r['baseline_m']} m (fov={r['fov_deg']} deg, "
                     f"{r['image_width']}x{r['image_height']})\n")
    print(f"Wrote {summary_txt}")

    # --- 2. Epipolar montage: one representative frame per trip, horizontal reference lines ---
    FRAME_ID = 50  # arbitrary mid-trip frame present in every trip
    LINE_EVERY = 40  # px
    tiles = []
    for trip_dir in trips:
        trip_id = os.path.basename(trip_dir)
        left_path = os.path.join(trip_dir, "kitti", "image_2", f"{FRAME_ID:06d}.jpg")
        right_path = os.path.join(trip_dir, "kitti", "image_3", f"{FRAME_ID:06d}.jpg")
        if not (os.path.exists(left_path) and os.path.exists(right_path)):
            continue
        left = cv2.imread(left_path)
        right = cv2.imread(right_path)
        if left is None or right is None:
            continue
        pair = np.hstack([left, right])
        h, w = pair.shape[:2]
        for y in range(0, h, LINE_EVERY):
            cv2.line(pair, (0, y), (w, y), (0, 255, 0), 1)
        cv2.line(pair, (left.shape[1], 0), (left.shape[1], h), (0, 0, 255), 2)  # left/right divider
        cv2.putText(pair, f"{trip_id} frame={FRAME_ID} (L | R)", (8, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        tiles.append(pair)

    if tiles:
        # normalize widths (all trips share 640x360 per manifest, but guard anyway)
        max_w = max(t.shape[1] for t in tiles)
        tiles = [cv2.copyMakeBorder(t, 0, 0, 0, max_w - t.shape[1], cv2.BORDER_CONSTANT, value=(0, 0, 0))
                 for t in tiles]
        montage = np.vstack(tiles)
        montage_path = os.path.join(OUT_DIR, "epipolar_montage.png")
        cv2.imwrite(montage_path, montage)
        print(f"Wrote {montage_path} ({len(tiles)} trip pairs, green lines every {LINE_EVERY}px)")
    else:
        print("WARNING: no trip had frame 000050 in both image_2/image_3 -- montage not generated.")


if __name__ == "__main__":
    main()
