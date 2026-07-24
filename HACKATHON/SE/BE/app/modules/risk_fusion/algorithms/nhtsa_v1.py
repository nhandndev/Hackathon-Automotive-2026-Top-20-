from typing import Dict, Any, List
from app.domain.interfaces.base_risk_model import BaseRiskModel

class NHTSARiskModelV1(BaseRiskModel):
    """
    Risk Fusion Scoring Algorithm based on NHTSA guidelines.
    Formula: R(t) = min(100, BaseRisk(TTC) * DriverFactor(State) + KinematicsPenalty)
    """

    def calculate_frame_risk(
        self,
        predicted_ttc: float,
        driver_state: str,
        active_events: List[str],
        telemetry: Dict[str, Any]
    ) -> float:
        # 1. Base Risk from TTC (Challenge 1)
        if predicted_ttc == "inf" or predicted_ttc > 10.0:
            base_risk = 5.0
        elif predicted_ttc <= 1.0:
            base_risk = 85.0
        elif predicted_ttc <= 1.5:
            base_risk = 70.0
        elif predicted_ttc <= 3.0:
            base_risk = 40.0
        else:
            base_risk = 15.0

        # 2. Driver Risk Factor (Challenge 2)
        state_factors = {
            "alert": 1.0,
            "yawning": 1.2,
            "distracted": 1.5,
            "drowsy": 1.8,
            "microsleep": 2.5
        }
        driver_factor = state_factors.get(driver_state.lower(), 1.0)

        # 3. Kinematics Penalty
        kinematics_penalty = 0.0
        if "HARSH_BRAKE" in active_events:
            kinematics_penalty += 15.0
        if "HARSH_CORNER" in active_events:
            kinematics_penalty += 10.0
        if "SPEEDING" in active_events:
            kinematics_penalty += 8.0

        raw_risk = (base_risk * driver_factor) + kinematics_penalty
        return max(0.0, min(100.0, round(raw_risk, 1)))

    def calculate_trip_safe_score(self, frame_risk_scores: List[float], total_events: List[Dict[str, Any]]) -> float:
        if not frame_risk_scores:
            return 100.0
            
        avg_risk = sum(frame_risk_scores) / len(frame_risk_scores)
        critical_count = sum(1 for r in frame_risk_scores if r >= 60.0)
        
        # Safe score starts at 100 and subtracts risk penalties
        penalty = (avg_risk * 0.4) + (critical_count * 1.5)
        safe_score = max(0.0, min(100.0, 100.0 - penalty))
        return round(safe_score, 1)
