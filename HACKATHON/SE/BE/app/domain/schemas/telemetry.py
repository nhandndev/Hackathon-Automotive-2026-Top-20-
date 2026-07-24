from pydantic import BaseModel, ConfigDict
from typing import Optional

class TelemetrySchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    speed_kmh: float = 0.0
    longitudinal_accel: float = 0.0
    lateral_accel: float = 0.0
    is_harsh_brake: bool = False
    is_harsh_accel: bool = False
    is_harsh_corner: bool = False
    is_speeding: bool = False
    latitude: Optional[float] = 10.762622
    longitude: Optional[float] = 106.660172
    heading_deg: Optional[float] = 0.0
