import os
import hashlib
import json
import zipfile
from datetime import datetime, timezone

def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def bundle_evaluator():
    print("Bundle Evaluator Started...")

    target_dir = os.path.join(os.path.dirname(__file__), "..", "01_reproducibility")
    os.makedirs(target_dir, exist_ok=True)

    bundle_name = os.path.join(target_dir, "evaluation_bundle.zip")
    manifest_name = os.path.join(target_dir, "manifest.json")

    # Challenge 1 (Road/TTC) reproducibility set, provided by Hung/Tam.
    # Run this script with cwd = repo root.
    files_to_bundle = [
        "HACKATHON/AI/configs/challenge1.yaml",
        "HACKATHON/AI/yolov8s_finetuned_carla_v2.pt",
        "HACKATHON/AI/scripts/eval_practice.py",
        "HACKATHON/AI/core/challenge1_road/predict_ttc.py",
        "HACKATHON/AI/core/challenge1_road/ttc_engine.py",
    ]

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "challenge": "C1 (Road / TTC)",
        "owner": "Hung/Tam",
        "reproduce_command": "cd HACKATHON/AI && python scripts/eval_practice.py",
        "reported_composite_score": {
            "in_sample_6_practice_trips": 73.6,
            "loto_cross_validated": 72.4,
            "note": "in-sample = evaluated on the same 6 Practice trips the "
                    "detector's val split is drawn from; LOTO = leave-one-"
                    "trip-out cross-validation over configs/challenge1.yaml "
                    "thresholds (scripts/loto_postprocess.py), the more "
                    "honest generalization estimate.",
        },
        "files": {}
    }

    with zipfile.ZipFile(bundle_name, 'w') as zf:
        for f in files_to_bundle:
            if os.path.exists(f):
                zf.write(f, f)
                manifest["files"][f] = hash_file(f)
            else:
                print(f"File missing: {f}")

    with open(manifest_name, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2)

    print(f"Bundle created at: {bundle_name}")
    print(f"Manifest created at: {manifest_name}")

if __name__ == "__main__":
    bundle_evaluator()
