from typing import Dict, Any, List

class EdgeCaseTemporalFilter:
    """
    Edge Case & Temporal Filtering Module.
    Filters out false alarms (blinks, glare squints, low-speed parking brakes, talking vs yawning)
    and handles compound critical risk boosts.
    """

    def __init__(self):
        self.closed_frame_counter = 0
        self.yawn_frame_counter = 0
        self.speeding_frame_counter = 0

    def filter_driver_state(self, raw_state: str, ear: float = 0.28, mar: float = 0.05, speed_kmh: float = 60.0, head_yaw: float = 0.0) -> str:
        # EC-15 & EC-13: Parking / Idle Relax Mode (v < 2.0 km/h) -> No false drowsiness
        if speed_kmh < 2.0:
            return "alert"

        # EC-01: Normal Blink vs Microsleep
        # Blink (<0.4s / 8 frames) is IGNORED -> alert. Microsleep (>=0.5s / 10 frames) -> microsleep.
        if ear < 0.22 or raw_state in ["microsleep", "drowsy"]:
            self.closed_frame_counter += 1
        else:
            self.closed_frame_counter = 0

        if self.closed_frame_counter >= 10:
            return "microsleep"
        elif 0 < self.closed_frame_counter < 8 and raw_state == "microsleep":
            return "alert"  # Ignore transient short eye closures

        # EC-02: Glare Squinting vs Drowsiness
        # If head is straight ahead (|yaw| < 10 deg) and speed > 30 km/h, prevent false drowsy
        if raw_state == "drowsy" and abs(head_yaw) < 10.0 and self.closed_frame_counter < 10:
            return "alert"

        # EC-03: Yawning vs Talking
        if mar > 0.55 or raw_state == "yawning":
            self.yawn_frame_counter += 1
        else:
            self.yawn_frame_counter = 0

        if self.yawn_frame_counter >= 60:  # Continuous 3s
            return "yawning"
        elif raw_state == "yawning" and self.yawn_frame_counter < 60:
            return "alert"

        return raw_state

    def filter_kinematics_event(self, event_type: str, speed_kmh: float, accel_val: float) -> bool:
        # EC-04: Low-speed parking / stop-and-go braking (v < 20 km/h) -> Ignore harsh brake penalty
        if event_type == "HARSH_BRAKE" and speed_kmh < 20.0:
            return False
        return True

    def calculate_compound_risk_boost(self, ttc: float, driver_state: str) -> float:
        # EC-06: Compound Critical Risk (TTC <= 1.5s AND driver is microsleep or distracted)
        if ttc <= 1.5 and driver_state in ["microsleep", "distracted"]:
            return 40.0
        return 0.0

temporal_filter = EdgeCaseTemporalFilter()
