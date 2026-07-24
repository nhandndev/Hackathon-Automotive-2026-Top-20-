from typing import Dict, Any, Optional
from app.domain.interfaces.base_detector import BaseDetector

class SpeedingDetector(BaseDetector):
    @property
    def event_code(self) -> str:
        return "SPEEDING"

    def detect(self, telemetry: Dict[str, Any], ai_vision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        speed = telemetry.get("speed_kmh", 0.0)
        speed_limit = telemetry.get("speed_limit_kmh", 80.0)
        if speed > speed_limit:
            return {
                "event_type": "SPEEDING",
                "severity": "MEDIUM",
                "description": f"Chạy quá tốc độ: {speed} km/h (giới hạn {speed_limit} km/h)",
                "value": speed
            }
        return None
