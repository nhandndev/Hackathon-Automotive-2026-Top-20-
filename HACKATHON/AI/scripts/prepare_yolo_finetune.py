"""
Fine-tuning step 1/2: convert kitti/label_2 (KITTI format) labels from the
6 practice trips into a YOLO-format dataset, ready for `yolo detect train`.

Why fine-tune at all: throughout Challenge 1 development, the dominant
remaining error (T01/T02) traced back to the stock COCO-pretrained YOLOv8s
under-detecting/mis-detecting VRUs specific to this CARLA-rendered domain --
e.g. a real cyclist scoring only 0.12-0.42 confidence, sometimes labelled
"person" instead of a two-wheeler. COCO was never trained on this render
style, camera angle, or resolution. A short domain-adaptation fine-tune on
real in-domain labels (kitti/label_2, present and accurate on all 6 practice
trips) directly targets that gap.

Class mapping kept identical to core/challenge1_road/detection.py's
_COCO_TO_TARGET, so the fine-tuned weights drop in with ZERO code changes:
    KITTI "Car"        -> COCO class 2 (car)
    KITTI "Pedestrian"  -> COCO class 0 (person)
    KITTI "Cyclist"     -> COCO class 1 (bicycle)  (this dataset's
                            motorcycle_cut_in scenario is exported as
                            "Cyclist" in label_2 -- confirmed against T02's
                            ground truth during earlier debugging)
Training keeps the full 80-class COCO head (not collapsed to 3 classes) so
the model doesn't forget/repurpose unrelated classes -- only images/labels
for these 3 classes are supplied, which is standard partial-supervision
fine-tuning.

A 90/10 frame-level split (not trip-level) is used for train/val: with only
134 pedestrian and 459 cyclist boxes total, holding out a whole trip would
starve val (or train) of an entire class in some trips (T03/T04 have zero
pedestrians, T01 has zero cars/cyclists). Final Challenge-1 quality is
judged later by the existing LOTO pipeline eval, not by this val split --
this split only exists to watch for training-time overfitting.

Usage:
    py -3.13 scripts/prepare_yolo_finetune.py
"""

from __future__ import annotations

import random
import shutil
import sys
from pathlib import Path

import numpy as np

AI_ROOT = Path(__file__).resolve().parents[1]
KIT = AI_ROOT / "Package_starterkit" / "Package_starterkit" / "package_starterkit"
DATA = AI_ROOT / "Practice_Dataset" / "Practice_Dataset"
OUT = AI_ROOT / "datasets" / "yolo_finetune"
sys.path.insert(0, str(KIT))
from team_kit.dataset_loader import TripDataset  # noqa: E402

KITTI_TO_COCO = {"Car": 2, "Pedestrian": 0, "Cyclist": 1}
VAL_FRACTION = 0.10
SEED = 0

# Standard COCO class names, in COCO id order -- keeps the fine-tuned head
# COCO-shaped so ObjectDetector's classes=[...] filter and _COCO_TO_TARGET
# mapping need no changes.
COCO_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
    "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
    "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
    "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush",
]

IMG_W, IMG_H = 640, 360  # release resolution (see README)
MIN_BOX_PX = 3  # reject degenerate/near-zero-area projected boxes


def project_3d_to_2d_bbox(
    h: float, w: float, l: float,
    x: float, y: float, z: float, ry: float,
    P2: np.ndarray,
) -> tuple[float, float, float, float] | None:
    """KITTI 3D box -> axis-aligned 2D bbox via the camera projection matrix.

    location (x,y,z) is the BOTTOM-CENTER of the box in camera coordinates
    (KITTI convention), dimensions are (height, width, length), rotation_y
    is yaw about the camera's Y axis. Returns None if the box is behind the
    camera or projects outside the image entirely.
    """
    x_c = np.array([l / 2, l / 2, -l / 2, -l / 2, l / 2, l / 2, -l / 2, -l / 2])
    y_c = np.array([0, 0, 0, 0, -h, -h, -h, -h])
    z_c = np.array([w / 2, -w / 2, -w / 2, w / 2, w / 2, -w / 2, -w / 2, w / 2])
    corners = np.vstack([x_c, y_c, z_c])  # 3x8, object frame

    cos_r, sin_r = np.cos(ry), np.sin(ry)
    R = np.array([[cos_r, 0, sin_r], [0, 1, 0], [-sin_r, 0, cos_r]])
    corners = R @ corners
    corners[0, :] += x
    corners[1, :] += y
    corners[2, :] += z

    in_front = corners[2, :] > 0.1
    if not in_front.any():
        return None  # entire box behind the camera

    corners_hom = np.vstack([corners, np.ones((1, 8))])
    proj = P2 @ corners_hom  # 3x8
    px = proj[0, in_front] / proj[2, in_front]
    py = proj[1, in_front] / proj[2, in_front]

    x1, y1 = max(0.0, float(px.min())), max(0.0, float(py.min()))
    x2, y2 = min(float(IMG_W), float(px.max())), min(float(IMG_H), float(py.max()))
    if x2 - x1 < MIN_BOX_PX or y2 - y1 < MIN_BOX_PX:
        return None
    return x1, y1, x2, y2


def convert_label_file(label_path: Path, P2: np.ndarray) -> list[str]:
    """One KITTI line -> one YOLO line (class cx cy w h, normalized).

    The dataset's own bbox_left/top/right/bottom fields are always 0.00
    (never populated by the CARLA export) -- confirmed by scanning many
    label files, so the 2D box must be derived from the real 3D
    dimensions+location+rotation_y fields via projection instead.
    """
    out_lines = []
    for line in label_path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        cls_name = parts[0]
        coco_id = KITTI_TO_COCO.get(cls_name)
        if coco_id is None:
            continue  # DontCare / Van / Truck / Tram / Misc -- skip
        h, w, l = (float(v) for v in parts[8:11])
        x, y, z = (float(v) for v in parts[11:14])
        ry = float(parts[14])
        if h <= 0 or w <= 0 or l <= 0:
            continue  # degenerate/placeholder entry
        bbox = project_3d_to_2d_bbox(h, w, l, x, y, z, ry, P2)
        if bbox is None:
            continue
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0 / IMG_W
        cy = (y1 + y2) / 2.0 / IMG_H
        bw = (x2 - x1) / IMG_W
        bh = (y2 - y1) / IMG_H
        out_lines.append(f"{coco_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    return out_lines


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    for split in ("train", "val"):
        (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)
    n_by_split = {"train": 0, "val": 0}
    n_boxes_by_split = {"train": 0, "val": 0}

    trips = sorted(p for p in DATA.iterdir() if p.is_dir() and p.name.endswith("-Sample"))
    n_skipped_no_calib = 0
    for trip in trips:
        label_dir = trip / "kitti" / "label_2"
        image_dir = trip / "kitti" / "image_2"
        if not label_dir.is_dir():
            continue
        ds = TripDataset(trip)  # only used here for load_frame_calibration()
        for label_path in sorted(label_dir.glob("*.txt")):
            frame_id_str = label_path.stem
            try:
                calib = ds.load_frame_calibration(int(frame_id_str))
                P2 = calib["P2"]
            except (FileNotFoundError, KeyError):
                n_skipped_no_calib += 1
                continue
            yolo_lines = convert_label_file(label_path, P2)
            if not yolo_lines:
                continue  # only keep frames that actually have a labeled object
            img_path = image_dir / f"{frame_id_str}.jpg"
            if not img_path.is_file():
                img_path = image_dir / f"{frame_id_str}.png"
            if not img_path.is_file():
                continue

            split = "val" if rng.random() < VAL_FRACTION else "train"
            stem = f"{trip.name}_{frame_id_str}"
            shutil.copy(img_path, OUT / "images" / split / f"{stem}{img_path.suffix}")
            (OUT / "labels" / split / f"{stem}.txt").write_text("\n".join(yolo_lines) + "\n")
            n_by_split[split] += 1
            n_boxes_by_split[split] += len(yolo_lines)
        print(f"  {trip.name}: done", flush=True)
    if n_skipped_no_calib:
        print(f"(skipped {n_skipped_no_calib} frames with no per-frame calib file)")

    yaml_path = OUT / "dataset.yaml"
    names_block = "\n".join(f"  {i}: {name}" for i, name in enumerate(COCO_NAMES))
    yaml_path.write_text(
        f"path: {OUT.resolve()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"names:\n{names_block}\n"
    )

    print(f"Train: {n_by_split['train']} images, {n_boxes_by_split['train']} boxes")
    print(f"Val:   {n_by_split['val']} images, {n_boxes_by_split['val']} boxes")
    print(f"Wrote dataset config -> {yaml_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
