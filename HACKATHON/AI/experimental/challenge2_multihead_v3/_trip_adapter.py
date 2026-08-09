from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import cv2
import yaml


def hackathon_root() -> Path:
    # .../HACKATHON/AI/experimental/challenge2_multihead_v3/_trip_adapter.py
    return Path(__file__).resolve().parents[3]


def ensure_import_path() -> None:
    root = hackathon_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_trip_json(trip_dir: str | Path) -> dict[str, Any]:
    trip_dir = Path(trip_dir)
    candidates = [trip_dir / f"{trip_dir.name}.json", *trip_dir.glob("*.json")]
    for candidate in candidates:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as handle:
                return json.load(handle)
    raise FileNotFoundError(f"No trip JSON found in {trip_dir}")


def discover_trip_dirs(data_dir: str | Path, samples_only: bool = False) -> list[Path]:
    data_dir = Path(data_dir)
    if (data_dir / f"{data_dir.name}.json").exists():
        return [data_dir]
    trips = []
    for child in sorted(data_dir.iterdir()):
        if not child.is_dir():
            continue
        if samples_only and "-Sample" not in child.name:
            continue
        if (child / f"{child.name}.json").exists() or any(child.glob("*.json")):
            trips.append(child)
    if not trips:
        raise FileNotFoundError(f"No trip folders found in {data_dir}")
    return trips


def driver_image_path(trip_dir: str | Path, frame_id: int) -> Path:
    trip_dir = Path(trip_dir)
    candidates = [
        trip_dir / "driver" / f"frame_{frame_id:06d}.jpg",
        trip_dir / "driver" / f"frame_{frame_id:06d}.png",
        trip_dir / "driver" / f"{frame_id:06d}.jpg",
        trip_dir / "driver" / f"{frame_id}.jpg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No driver image for frame {frame_id} in {trip_dir / 'driver'}")


def iter_trip_frames(trip_json: Mapping[str, Any], max_frames: int | None = None) -> Iterable[dict[str, Any]]:
    frames = list(trip_json.get("frames", []))
    if max_frames is not None:
        frames = frames[: max(0, int(max_frames))]
    return frames


def frame_label(frame: Mapping[str, Any]) -> str | None:
    driver = frame.get("driver", {})
    if not isinstance(driver, Mapping):
        return None
    state = driver.get("state")
    if state is None:
        return None
    return str(state).strip().lower()


def frame_timestamp_ms(frame: Mapping[str, Any], fallback_frame_id: int, fps: float = 20.0) -> int:
    timestamp = frame.get("timestamp")
    if timestamp is None:
        timestamp = fallback_frame_id / max(1e-6, fps)
    return int(round(float(timestamp) * 1000.0))


def primitive_to_raw_features(
    primitive: Mapping[str, Any],
    frame: Mapping[str, Any],
) -> dict[str, Any]:
    features = primitive.get("features", {})
    observation = primitive.get("observation", {})
    ego = frame.get("ego", {}) if isinstance(frame.get("ego"), Mapping) else {}

    return {
        "frame_id": int(frame.get("frame_id", primitive.get("frame_id", 0))),
        "timestamp_sec": float(frame.get("timestamp", primitive.get("timestamp_ms", 0) / 1000.0)),
        "ear": _maybe_float(features.get("ear_robust")),
        "mar": _maybe_float(features.get("mar")),
        "yaw_deg": _maybe_float(features.get("yaw_deg")),
        "pitch_deg": _maybe_float(features.get("pitch_deg")),
        "roll_deg": _maybe_float(features.get("roll_deg")),
        "eye_quality": 1.0 if observation.get("left_eye_valid") or observation.get("right_eye_valid") else 0.0,
        "mouth_quality": 1.0 if observation.get("mouth_valid", False) else 0.0,
        "head_quality": 1.0 if observation.get("head_pose_valid", False) else 0.0,
        "hand_visible": bool(float(features.get("hand_visible", 0.0) or 0.0) > 0.0),
        "hand_quality": 1.0,
        "phone_detected": bool(float(features.get("phone_detected", 0.0) or 0.0) > 0.0),
        "speed_kmh": float(ego.get("speed_kmh", 0.0) or 0.0),
        "longitudinal_accel": float(ego.get("longitudinal_accel", 0.0) or 0.0),
        "lateral_accel": float(ego.get("lateral_accel", 0.0) or 0.0),
    }


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def make_dms_core(config_path: str | Path):
    ensure_import_path()
    from AI.core.challenge2_driver.dms_core import DMSCore

    return DMSCore(load_yaml(config_path))


def process_driver_frame(dms_core: Any, trip_dir: str | Path, frame: Mapping[str, Any], fps: float = 20.0) -> dict[str, Any]:
    frame_id = int(frame.get("frame_id", 0))
    image_path = driver_image_path(trip_dir, frame_id)
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Could not read driver image: {image_path}")
    return dms_core.process(image, frame_id, frame_timestamp_ms(frame, frame_id, fps=fps))
