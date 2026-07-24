from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class RiskFusionSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    predicted_risk_score: float = 5.0  # Frame-by-frame risk score (0.0 to 100.0)
    predicted_safe_score: Optional[float] = 95.0  # Cumulative trip safe score (0.0 to 100.0)
    is_compound_critical: bool = False
    active_events: List[str] = []
