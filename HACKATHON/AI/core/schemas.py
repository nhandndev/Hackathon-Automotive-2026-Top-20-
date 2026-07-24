# Core AI Feature Vector Schema & Data Contracts
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class FeatureVectorSchema(BaseModel):
    frame_id: int
    timestamp: float
    speed_kmh: float
    longitudinal_accel: float
    lateral_accel: float
    latitude: float
    longitude: float
    heading_deg: float
    ear_score: Optional[float] = None
    mar_score: Optional[float] = None
    head_pose_pitch: Optional[float] = None
    predicted_ttc: str = "inf"
    predicted_driver_state: str = "alert"
    alertness_score: float = 0.95

class EvaluationMetricsSchema(BaseModel):
    critical_region_mae: float
    collision_f1: float
    driver_state_accuracy: float
    macro_f1: float
    recall_microsleep: float
    mae_safe_score: float
    timestamp: str
    git_commit: str
