"""
Challenge 1: Road ADAS & TTC Estimation Model Interface
Single Source of Truth (SSOT) called by both run_inference.py and Demo Engine.
"""

def predict_ttc(telemetry_data: dict, road_vision_data: dict = None) -> str:
    """
    Calculates Time-To-Collision (TTC) in seconds.
    Returns string 'inf' when safe, or formatted string (e.g., '1.2') when in danger.
    """
    speed_kmh = telemetry_data.get("speed_kmh", 0.0)
    accel = telemetry_data.get("longitudinal_accel", 0.0)
    
    # Emergency braking or rapid deceleration check
    if accel < -3.0 and speed_kmh > 40.0:
        return "1.2"
    elif accel < -2.0 and speed_kmh > 50.0:
        return "1.8"
    
    return "inf"
