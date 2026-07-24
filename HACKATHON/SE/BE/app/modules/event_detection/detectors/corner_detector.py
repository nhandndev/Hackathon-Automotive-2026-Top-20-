from typing import Dict, Any, Optional
from app.domain.interfaces.base_detector import BaseDetector

class HarshCornerDetector(BaseDetector):
    @property
    def event_code(self) -> str:
        return "HARSH_CORNER"

    def detect(self, telemetry: Dict[str, Any], ai_vision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        accel_y = abs(telemetry.get("lateral_accel", 0.0))
        if accel_y > 3.5:
            return {
                "event_type": "HARSH_CORNER",
                "severity": "HIGH",
                "description": f"Cua gắt nguy hiểm: gia tốc ngang {accel_y} m/s²",
                "value": accel_y
            }
        return None
