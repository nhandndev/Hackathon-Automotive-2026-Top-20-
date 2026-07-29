"""Small dependency-free loader for the BTC trip inference contract."""
from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import cv2
import numpy as np


@dataclass(frozen=True)
class FrameRecord:
    frame_id: int
    timestamp: float
    speed_kmh: float
    longitudinal_accel: float
    lateral_accel: float


class TripDataset:
    """Load only the organizer fields required by production inference."""

    def __init__(self, trip_dir: str | Path) -> None:
        self.trip_dir = Path(trip_dir).resolve()
        if not self.trip_dir.is_dir():
            raise FileNotFoundError(f"Trip directory not found: {trip_dir}")
        self.trip_id = self.trip_dir.name
        self._document = self._load_document()
        self.metadata: dict[str, Any] = self._document.get("metadata", {})
        self._records = [
            self._parse_frame(item)
            for item in self._document.get("frames", [])
        ]
        if not self._records:
            raise ValueError(f"{self.trip_id}: trip contains no frames")
        kitti = self.trip_dir / "kitti"
        self.image_left_dir = kitti / "image_2"
        self.image_right_dir = kitti / "image_3"
        self.depth_dir = kitti / "depth"
        self.calib_dir = kitti / "calib"
        self.label_dir = kitti / "label_2"
        self.driver_dir = self.trip_dir / "driver"

    def __len__(self) -> int:
        return len(self._records)

    def iter_frames(self) -> Iterator[FrameRecord]:
        return iter(self._records)

    def load_left(self, frame_id: int) -> np.ndarray:
        return self._load_image(self.image_left_dir, f"{frame_id:06d}")

    def load_right(self, frame_id: int) -> np.ndarray:
        return self._load_image(self.image_right_dir, f"{frame_id:06d}")

    def load_driver(self, frame_id: int) -> np.ndarray:
        return self._load_image(
            self.driver_dir, f"frame_{frame_id:06d}"
        )

    def load_calibration(self) -> dict[str, Any]:
        path = self.trip_dir / "kitti" / "calibration_info.txt"
        if not path.is_file():
            raise FileNotFoundError(f"Missing trip calibration: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def load_frame_calibration(
        self, frame_id: int
    ) -> dict[str, np.ndarray]:
        path = self.calib_dir / f"{frame_id:06d}.txt"
        if not path.is_file():
            raise FileNotFoundError(f"Missing frame calibration: {path}")
        output: dict[str, np.ndarray] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, values = line.split(":", 1)
            numbers = np.fromstring(values, sep=" ", dtype=float)
            if key.startswith("P") and numbers.size == 12:
                output[key] = numbers.reshape(3, 4)
            elif key == "R0_rect" and numbers.size == 9:
                output[key] = numbers.reshape(3, 3)
            elif numbers.size == 12:
                output[key] = numbers.reshape(3, 4)
            else:
                output[key] = numbers
        return output

    def _load_document(self) -> dict[str, Any]:
        compressed = self.trip_dir / f"{self.trip_id}.json.gz"
        plain = self.trip_dir / f"{self.trip_id}.json"
        if compressed.is_file():
            with gzip.open(compressed, "rt", encoding="utf-8") as stream:
                return json.load(stream)
        if plain.is_file():
            return json.loads(plain.read_text(encoding="utf-8"))
        raise FileNotFoundError(
            f"Missing {self.trip_id}.json or {self.trip_id}.json.gz"
        )

    @staticmethod
    def _parse_frame(raw: dict[str, Any]) -> FrameRecord:
        ego = raw.get("ego", {})
        return FrameRecord(
            frame_id=int(raw["frame_id"]),
            timestamp=float(raw["timestamp"]),
            speed_kmh=float(ego.get("speed_kmh", 0.0)),
            longitudinal_accel=float(
                ego.get("longitudinal_accel", 0.0)
            ),
            lateral_accel=float(ego.get("lateral_accel", 0.0)),
        )

    @staticmethod
    def _load_image(directory: Path, stem: str) -> np.ndarray:
        for suffix in (".jpg", ".png", ".jpeg"):
            path = directory / f"{stem}{suffix}"
            if path.is_file():
                image = cv2.imread(str(path), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError(f"Cannot decode image: {path}")
                return image
        raise FileNotFoundError(f"Image not found: {directory / stem}")
