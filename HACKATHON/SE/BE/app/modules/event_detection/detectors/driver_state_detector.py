"""
Driver State Baseline Detector (Challenge 2 Heuristic Detection Engine).
Detects: ALERT, DROWSY, YAWNING, DISTRACTED, MICROSLEEP based on EAR, MAR, and Head Pose.
"""

from typing import Dict, Any, Optional

class DriverStateBaselineDetector:
    """
    Heuristic Driver State Detector based on Eye Aspect Ratio (EAR),
    Mouth Aspect Ratio (MAR), Head Pose, and Frame Sequence.
    """

    def __init__(self):
        self.closed_eye_consecutive_frames = 0

    def detect_driver_state(self, ai_vision: Dict[str, Any], frame_idx: int = 0) -> Dict[str, Any]:
        """
        Detects driver state and returns state enum + alertness score.
        """
        raw_state = str(ai_vision.get("predicted_driver_state", "alert")).lower()
        ear = float(ai_vision.get("ear_value", 0.28))
        mar = float(ai_vision.get("mar_value", 0.08))
        head_yaw = float(ai_vision.get("head_yaw_deg", 0.0))
        head_pitch = float(ai_vision.get("head_pitch_deg", 0.0))

        # Check if AI vision already delivered a high-confidence prediction
        if raw_state in ["drowsy", "yawning", "distracted", "microsleep"]:
            state = raw_state
        # Apply Baseline Heuristic Rules based on facial landmark metrics
        elif ear < 0.14:
            self.closed_eye_consecutive_frames += 1
            if self.closed_eye_consecutive_frames >= 8: # 0.4s @ 20 FPS
                state = "microsleep"
            else:
                state = "drowsy"
        elif mar > 0.42:
            self.closed_eye_consecutive_frames = 0
            state = "yawning"
        elif abs(head_yaw) > 22.0 or abs(head_pitch) > 20.0:
            self.closed_eye_consecutive_frames = 0
            state = "distracted"
        elif ear < 0.22:
            self.closed_eye_consecutive_frames = 0
            state = "drowsy"
        else:
            self.closed_eye_consecutive_frames = 0
            state = "alert"

        # Calculate alertness score (0.0 -> 1.0)
        alertness_map = {
            "alert": 0.95,
            "yawning": 0.70,
            "distracted": 0.50,
            "drowsy": 0.30,
            "microsleep": 0.05
        }
        alertness_score = alertness_map.get(state, 0.95)

        return {
            "detected_driver_state": state.upper(),
            "alertness_score": alertness_score,
            "ear_value": ear,
            "mar_value": mar,
            "closed_eye_frames": self.closed_eye_consecutive_frames
        }

# Singleton instance
driver_state_detector = DriverStateBaselineDetector()
