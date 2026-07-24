from pydantic import BaseModel, ConfigDict
from typing import Union

class SubmissionFrameRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    frame_id: int
    timestamp: float
    predicted_ttc: Union[float, str]  # Float or "inf"
    predicted_driver_state: str        # alert, drowsy, yawning, distracted, microsleep
    predicted_risk_score: float        # 0.0 to 100.0
