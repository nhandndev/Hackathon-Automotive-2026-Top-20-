from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseDetector(ABC):
    """Abstract base class for all behavioral & kinematics detectors (Plugin Pattern)."""
    
    @property
    @abstractmethod
    def event_code(self) -> str:
        """Returns unique string code for event (e.g. HARSH_BRAKE, MICROSLEEP)."""
        pass
        
    @abstractmethod
    def detect(self, telemetry: Dict[str, Any], ai_vision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluates frame data and returns an event dict if detected, else None.
        Returns:
            Dict containing event_type, severity, timestamp, description or None.
        """
        pass
