"""
Challenge 2: Driver Monitoring System (DMS) State Estimation Model Interface
Extracts EAR, MAR, Head Pose and predicts driver state: alert, drowsy, yawning, microsleep, distracted.
"""

def predict_driver_state(cabin_frame_data: dict) -> dict:
    """
    Predicts driver state and returns dictionary with predicted_driver_state and alertness_score.
    """
    ear_score = cabin_frame_data.get("ear_score", 0.35)
    mar_score = cabin_frame_data.get("mar_score", 0.15)
    
    state = "alert"
    score = 0.95
    
    if ear_score < 0.18:
        state = "microsleep"
        score = 0.15
    elif ear_score < 0.22:
        state = "drowsy"
        score = 0.40
    elif mar_score > 0.65:
        state = "yawning"
        score = 0.60
        
    return {
        "predicted_driver_state": state,
        "alertness_score": score,
        "ear_score": ear_score,
        "mar_score": mar_score
    }
