from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseRiskModel(ABC):
    """Abstract base class for Risk Fusion Scoring Engine (Strategy Pattern)."""
    
    @abstractmethod
    def calculate_frame_risk(
        self,
        predicted_ttc: float,
        driver_state: str,
        active_events: List[str],
        telemetry: Dict[str, Any]
    ) -> float:
        """Calculates per-frame risk score bounded between 0.0 and 100.0."""
        pass
        
    @abstractmethod
    def calculate_trip_safe_score(self, frame_risk_scores: List[float], total_events: List[Dict[str, Any]]) -> float:
        """Calculates overall trip safe driving score (0.0 to 100.0)."""
        pass
