from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, Union

class DriverStateEnum(str, Enum):
    ALERT = "alert"
    DROWSY = "drowsy"
    YAWNING = "yawning"
    DISTRACTED = "distracted"
    MICROSLEEP = "microsleep"

class AIVisionSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    predicted_ttc: Union[float, str] = "inf"  # float value or "inf" string
    predicted_driver_state: DriverStateEnum = DriverStateEnum.ALERT
    alertness_score: float = 1.0
    ear_value: Optional[float] = 0.28
    mar_value: Optional[float] = 0.05
    perclos_60s: Optional[float] = 0.05
