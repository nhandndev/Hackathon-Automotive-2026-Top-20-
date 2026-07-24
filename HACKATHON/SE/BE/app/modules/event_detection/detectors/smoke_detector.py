from typing import Dict, Any, Optional
from app.domain.interfaces.base_detector import BaseDetector

class SmokeDetector(BaseDetector):
    """Extensible plugin example for detecting driver smoking / cabin hazard."""
    @property
    def event_code(self) -> str:
        return "SMOKING_IN_CABIN"

    def detect(self, telemetry: Dict[str, Any], ai_vision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Checked via AI vision extra flags if present
        is_smoking = ai_vision.get("is_smoking", False)
        if is_smoking:
            return {
                "event_type": "SMOKING_IN_CABIN",
                "severity": "LOW",
                "description": "Phát hiện tài xế hút thuốc trong cabin",
                "value": 1.0
            }
        return None
