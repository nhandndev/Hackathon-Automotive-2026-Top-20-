"""
Object Detection + Tracking for Challenge 1 (Road / TTC).

Wraps YOLOv8 (ultralytics) with its built-in ByteTrack tracker so each
detection carries a stable track_id across frames -- required to estimate
closing_speed (Δdistance / Δt) for a *single* object over time.

Graceful degradation: if ultralytics/torch is unavailable, `is_available()`
returns False and the caller falls back to the stereo-ROI baseline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

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


class ObjectDetector:
    """YOLOv8 detector + ByteTrack tracker (ultralytics)."""

    def __init__(
        self,
        weights: str = "yolov8n.pt",
        conf: float = 0.25,
        iou: float = 0.5,
        device: Optional[str] = None,
        imgsz: int = 640,
    ) -> None:
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device
        self._model = None
        self._load_error: Optional[str] = None
        try:
            from ultralytics import YOLO  # noqa: WPS433 (lazy import by design)
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

        results = self._model.track(
            left_bgr,
            persist=True,
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            device=self.device,
            tracker="bytetrack.yaml",
            classes=list(_COCO_TO_TARGET.keys()),
            verbose=False,
        )
        if not results:
            return []

        res = results[0]
        boxes = getattr(res, "boxes", None)
        if boxes is None or boxes.id is None:
            return []

        dets: List[Detection] = []
        xyxy = boxes.xyxy.cpu().numpy()
        cls = boxes.cls.cpu().numpy().astype(int)
        conf = boxes.conf.cpu().numpy()
        ids = boxes.id.cpu().numpy().astype(int)
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
        if self._model is not None and hasattr(self._model, "predictor"):
            predictor = self._model.predictor
            if predictor is not None and getattr(predictor, "trackers", None):
                for tr in predictor.trackers:
                    if hasattr(tr, "reset"):
                        tr.reset()
