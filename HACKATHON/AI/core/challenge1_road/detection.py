"""
Object Detection + Tracking for Challenge 1 (Road / TTC).

Wraps YOLOv8 (ultralytics) with its built-in ByteTrack tracker so each
detection carries a stable track_id across frames -- required to estimate
closing_speed (Δdistance / Δt) for a *single* object over time.

Graceful degradation: if ultralytics/torch is unavailable, `is_available()`
returns False and the caller falls back to the stereo-ROI baseline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# COCO class ids we care about, mapped to the dataset's target_class vocab.
# (ultralytics YOLOv8 is COCO-pretrained: 2=car, 3=motorcycle, 5=bus,
#  7=truck, 0=person, 1=bicycle)
_COCO_TO_TARGET = {
    2: "vehicle",
    5: "vehicle",
    7: "vehicle",
    3: "motorcycle",
    0: "pedestrian",
    1: "motorcycle",  # cyclist treated as a two-wheeler VRU
}


@dataclass
class Detection:
    track_id: int
    target_class: str          # vehicle | motorcycle | pedestrian
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 (pixels, left image)
    confidence: float

    @property
    def cx(self) -> float:
        return 0.5 * (self.bbox[0] + self.bbox[2])

    @property
    def cy(self) -> float:
        return 0.5 * (self.bbox[1] + self.bbox[3])

    @property
    def height_px(self) -> float:
        return self.bbox[3] - self.bbox[1]

    @property
    def width_px(self) -> float:
        return self.bbox[2] - self.bbox[0]


# Average real-world heights (m) per class -- monocular depth fallback.
REAL_HEIGHT_M = {"vehicle": 1.5, "motorcycle": 1.3, "pedestrian": 1.7}


class _CentroidTracker:
    """Minimal greedy centroid tracker used instead of ByteTrack.

    ByteTrack only emits a track once a detection is matched on two
    consecutive frames. The faint VRU detections here are intermittent --
    on T02's cut-in the rider is found on frames 311,312,314,316,317,319..
    but not 313,315,318 -- so every nascent track died before it was ever
    confirmed and `track()` returned nothing for the rider at all, even for
    a 0.50-confidence box. Tuning ByteTrack's thresholds cannot fix that:
    the requirement is structural.

    This keeps a track alive across those gaps (`max_age` frames) and
    matches on centroid distance scaled by box size, which is all the TTC
    engine needs -- a stable id per object so depth history is continuous.
    """

    def __init__(self, max_age: int = 12, max_dist_px: float = 60.0) -> None:
        self.max_age = max_age
        self.max_dist = max_dist_px
        self._tracks: Dict[int, Dict[str, float]] = {}
        self._next_id = 1
        self._frame = 0

    def reset(self) -> None:
        self._tracks.clear()
        self._next_id = 1
        self._frame = 0

    def assign(self, boxes: List[Tuple[float, float, float, float]]) -> List[int]:
        self._frame += 1
        ids: List[int] = [-1] * len(boxes)
        used: set = set()
        for i, (cx, cy, w, h) in enumerate(boxes):
            best_id, best_d = None, 1e18
            for tid, tr in self._tracks.items():
                if tid in used or self._frame - tr["seen"] > self.max_age:
                    continue
                d = math.hypot(cx - tr["cx"], cy - tr["cy"])
                # allow more drift for bigger/closer boxes
                lim = self.max_dist + 0.5 * max(w, h)
                if d < lim and d < best_d:
                    best_id, best_d = tid, d
            if best_id is None:
                best_id = self._next_id
                self._next_id += 1
            ids[i] = best_id
            used.add(best_id)
            self._tracks[best_id] = {"cx": cx, "cy": cy, "seen": self._frame}
        for tid in [t for t, v in self._tracks.items() if self._frame - v["seen"] > self.max_age]:
            del self._tracks[tid]
        return ids


class ObjectDetector:
    """YOLOv8 detector + ByteTrack tracker (ultralytics)."""

    def __init__(
        self,
        weights: str = "yolov8n.pt",
        conf: float = 0.25,
        iou: float = 0.5,
        device: Optional[str] = None,
        imgsz: int = 640,
        tracker: str = "bytetrack.yaml",
    ) -> None:
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device
        # Tracker config path. This matters as much as `conf`: ByteTrack
        # applies its OWN new_track_thresh (0.25 by default) on top of the
        # detector threshold, so faint-but-real VRU detections never become
        # tracks and are invisible downstream. See configs/bytetrack_vru.yaml.
        self.tracker = tracker
        # "simple" -> our own centroid tracker over raw predict() output.
        self._simple = _CentroidTracker() if tracker == "simple" else None
        self._model = None
        self._load_error: Optional[str] = None
        try:
            from ultralytics import YOLO  # noqa: WPS433 (lazy import by design)
            weight_path = Path(weights)
            if not weight_path.is_absolute() and not weight_path.exists():
                ai_relative = Path(__file__).resolve().parents[2] / weight_path
                if ai_relative.exists():
                    weight_path = ai_relative
            weights = str(weight_path)
            self._model = YOLO(weights)
        except Exception as e:  # ultralytics/torch missing or weights unfetchable
            self._load_error = str(e)

    def is_available(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def track(self, left_bgr: np.ndarray) -> List[Detection]:
        """Run detection+tracking on one left frame. Persists tracker state
        across calls, so call once per frame in temporal order (and call
        `reset()` between trips)."""
        if self._model is None:
            return []

        if self._simple is not None:
            results = self._model.predict(
                left_bgr,
                conf=self.conf,
                iou=self.iou,
                imgsz=self.imgsz,
                device=self.device,
                classes=list(_COCO_TO_TARGET.keys()),
                verbose=False,
            )
        else:
            results = self._model.track(
                left_bgr,
                persist=True,
                conf=self.conf,
                iou=self.iou,
                imgsz=self.imgsz,
                device=self.device,
                tracker=self.tracker,
                classes=list(_COCO_TO_TARGET.keys()),
                verbose=False,
            )
        if not results:
            return []

        res = results[0]
        boxes = getattr(res, "boxes", None)
        if boxes is None:
            return []

        xyxy = boxes.xyxy.cpu().numpy()
        cls = boxes.cls.cpu().numpy().astype(int)
        conf = boxes.conf.cpu().numpy()
        if self._simple is not None:
            centres = [
                ((x1 + x2) / 2.0, (y1 + y2) / 2.0, x2 - x1, y2 - y1)
                for x1, y1, x2, y2 in xyxy
            ]
            ids = np.array(self._simple.assign(centres), dtype=int)
        else:
            if boxes.id is None:
                return []
            ids = boxes.id.cpu().numpy().astype(int)

        dets: List[Detection] = []
        for i in range(len(xyxy)):
            target_class = _COCO_TO_TARGET.get(int(cls[i]))
            if target_class is None:
                continue
            x1, y1, x2, y2 = (float(v) for v in xyxy[i])
            dets.append(
                Detection(
                    track_id=int(ids[i]),
                    target_class=target_class,
                    bbox=(x1, y1, x2, y2),
                    confidence=float(conf[i]),
                )
            )
        return dets

    def reset(self) -> None:
        """Clear tracker state between trips."""
        if self._simple is not None:
            self._simple.reset()
        if self._model is not None and hasattr(self._model, "predictor"):
            predictor = self._model.predictor
            if predictor is not None and getattr(predictor, "trackers", None):
                for tr in predictor.trackers:
                    if hasattr(tr, "reset"):
                        tr.reset()
