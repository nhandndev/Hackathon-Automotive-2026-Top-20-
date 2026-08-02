"""Validated, non-biometric driver profile and persistent storage."""
from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROFILE_SCHEMA_VERSION = 3
PROFILE_LANDMARK_BACKEND = "onnx-yunet-facemesh468"
DRIVER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,64}$")


def validate_driver_id(driver_id: str) -> str:
    """Return a safe ID or raise before it can become part of a file path."""
    if not DRIVER_ID_PATTERN.fullmatch(driver_id):
        raise ValueError(
            "Driver ID must contain 3-64 letters, numbers, '_' or '-'"
        )
    return driver_id


def _finite(name: str, value: Any, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return number


@dataclass(frozen=True)
class DriverProfile:
    """Small calibration profile; deliberately contains no image or identity."""

    driver_id: str
    ear_open: float
    ear_closed: float
    mar_neutral: float
    mar_yawn: float
    neutral_yaw_deg: float
    neutral_pitch_deg: float
    neutral_roll_deg: float
    eye_closure_threshold: float
    quality_score: float
    created_at: str
    landmark_backend: str = PROFILE_LANDMARK_BACKEND
    schema_version: int = PROFILE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_driver_id(self.driver_id)
        if self.schema_version != PROFILE_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported profile schema {self.schema_version}; "
                f"expected {PROFILE_SCHEMA_VERSION}"
            )
        if self.landmark_backend != PROFILE_LANDMARK_BACKEND:
            raise ValueError(
                f"Unsupported profile landmark backend "
                f"'{self.landmark_backend}'; expected "
                f"'{PROFILE_LANDMARK_BACKEND}'"
            )
        open_ear = _finite("ear_open", self.ear_open, 0.05, 0.8)
        closed_ear = _finite("ear_closed", self.ear_closed, 0.01, 0.7)
        if closed_ear >= open_ear:
            raise ValueError("ear_closed must be lower than ear_open")
        neutral_mar = _finite("mar_neutral", self.mar_neutral, 0.01, 2.0)
        yawn_mar = _finite("mar_yawn", self.mar_yawn, 0.01, 3.0)
        if yawn_mar <= neutral_mar:
            raise ValueError("mar_yawn must be higher than mar_neutral")
        for name in (
            "neutral_yaw_deg",
            "neutral_pitch_deg",
            "neutral_roll_deg",
        ):
            _finite(name, getattr(self, name), -180.0, 180.0)
        _finite(
            "eye_closure_threshold", self.eye_closure_threshold, 0.5, 0.95
        )
        _finite("quality_score", self.quality_score, 0.0, 1.0)
        if not isinstance(self.created_at, str) or not self.created_at:
            raise ValueError("created_at must be a non-empty ISO timestamp")

    @classmethod
    def create(cls, driver_id: str, **values: Any) -> "DriverProfile":
        return cls(
            driver_id=validate_driver_id(driver_id),
            created_at=datetime.now(timezone.utc).isoformat(),
            **values,
        )

    @classmethod
    def from_dict(cls, document: dict[str, Any]) -> "DriverProfile":
        allowed = set(cls.__dataclass_fields__)
        unknown = sorted(set(document) - allowed)
        if unknown:
            raise ValueError(f"Unknown profile fields: {unknown}")
        try:
            return cls(**document)
        except TypeError as exc:
            raise ValueError(f"Invalid profile document: {exc}") from exc

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProfileStore:
    """Load and atomically save profiles below one controlled directory."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def path_for(self, driver_id: str) -> Path:
        return self.root / f"{validate_driver_id(driver_id)}.json"

    def exists(self, driver_id: str) -> bool:
        return self.path_for(driver_id).is_file()

    def load(self, driver_id: str) -> DriverProfile:
        path = self.path_for(driver_id)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot read driver profile {path}: {exc}") from exc
        if not isinstance(document, dict):
            raise ValueError(f"{path}: profile must be a JSON object")
        profile = DriverProfile.from_dict(document)
        if profile.driver_id != driver_id:
            raise ValueError(f"{path}: driver_id does not match file name")
        return profile

    def save(self, profile: DriverProfile) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        destination = self.path_for(profile.driver_id)
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(profile.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)
        return destination
