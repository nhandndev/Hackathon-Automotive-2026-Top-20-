from typing import Dict, Any, Optional
from app.domain.interfaces.base_detector import BaseDetector

class HarshBrakeDetector(BaseDetector):
    @property
    def event_code(self) -> str:
        return "HARSH_BRAKE"

    def detect(self, telemetry: Dict[str, Any], ai_vision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        accel_x = telemetry.get("longitudinal_accel", 0.0)
        if accel_x < -3.0:
            return {
                "event_type": "HARSH_BRAKE",
                "severity": "CRITICAL" if accel_x < -4.5 else "HIGH",
                "description": f"Phanh gấp nguy hiểm: gia tốc dọc {accel_x} m/s²",
                "value": accel_x
            }
        return None
