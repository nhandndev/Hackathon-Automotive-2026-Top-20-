from typing import List, Dict, Any
from app.domain.interfaces.base_detector import BaseDetector
from app.modules.event_detection.detectors.brake_detector import HarshBrakeDetector
from app.modules.event_detection.detectors.corner_detector import HarshCornerDetector
from app.modules.event_detection.detectors.speed_detector import SpeedingDetector
from app.modules.event_detection.detectors.smoke_detector import SmokeDetector
from app.core.logger import logger

class DetectorRegistry:
    """Registry maintaining active event detector plugins."""

    def __init__(self):
        self.detectors: List[BaseDetector] = []
        self._register_default_detectors()

    def register(self, detector: BaseDetector):
        self.detectors.append(detector)
        logger.info(f"Registered Detector Plugin: {detector.event_code}")

    def _register_default_detectors(self):
        self.register(HarshBrakeDetector())
        self.register(HarshCornerDetector())
        self.register(SpeedingDetector())
        self.register(SmokeDetector())

    def run_detectors(self, telemetry: Dict[str, Any], ai_vision: Dict[str, Any]) -> List[Dict[str, Any]]:
        active_events = []
        for detector in self.detectors:
            event = detector.detect(telemetry, ai_vision)
            if event:
                active_events.append(event)
        return active_events

detector_registry = DetectorRegistry()
