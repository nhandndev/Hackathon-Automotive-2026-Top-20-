from pathlib import Path
from typing import Any

import pytest

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def sample_ai_payload() -> dict[str, Any]:
    return {
        "trip_id": "T01d",
        "metadata": {
            "trip_id": "T01d",
            "description": "DEBUG highway evening",
            "duration_sec": 90,
            "fps": 20,
            "map": "Town01",
            "driver_profile": "normal",
            "carla_version": "0.9.15",
            "random_seed": 1001,
            "speed_limit_kmh": 80,
            "metadata_extra": {"weather": "clear"},
        },
        "frames": [
            {
                "frame_id": 0,
                "timestamp": 0.0,
                "ego": {
                    "speed_kmh": 0.0,
                    "longitudinal_accel": 0.0,
                    "lateral_accel": 0.0,
                    "geolocation": {"lat": -0.00123, "lon": -0.000485, "alt": 0.16},
                    "world_frame": 123,
                },
                "driver": {
                    "state": "distracted",
                    "alertness_score": 0.45,
                    "eye_state": "open",
                    "head_pose": "side",
                    "mouth_state": "normal",
                    "nthu_subject_id": "14",
                },
                "min_ttc": "Infinity",
                "headway_sec": "inf",
                "behavior_flags": {
                    "harsh_brake": False,
                    "harsh_accel": False,
                    "harsh_corner": False,
                    "speeding": False,
                    "tailgating": False,
                },
                "risk": {
                    "base_risk": 0.0,
                    "driver_factor": 2.2,
                    "final_risk_score": 0.0,
                },
                "targets": [{"id": "motorcycle-1"}],
                "events_active": [],
            }
        ],
        "trip_extra": "preserved",
    }


def make_settings(dataset_dir: Path, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "APP_ENV": "test",
        "DATASET_DIR": dataset_dir,
        "OUTPUT_SUBMISSION_DIR": dataset_dir / "submissions",
        "AI_SOURCE_MODE": "file",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def app_factory(tmp_path: Path):
    def factory(**overrides: Any):
        return create_app(make_settings(tmp_path, **overrides))

    return factory
