"""
Challenge 3: Risk Fusion & Reasoning Engine
Fuses Challenge 1 (TTC), Challenge 2 (Driver State) and Telemetry into final_risk_score (0-100).
"""

def calculate_frame_risk(telemetry: dict, driver_state: dict, ttc_val: str) -> dict:
    risk_score = 10.0
    risk_level = "SAFE"
    
    state = driver_state.get("predicted_driver_state", "alert")
    
    # State Risk Penalties
    if state == "microsleep":
        risk_score += 65.0
    elif state == "drowsy":
        risk_score += 40.0
    elif state == "yawning":
        risk_score += 20.0
    elif state == "distracted":
        risk_score += 30.0
        
    # TTC Risk Penalties
    if ttc_val != "inf":
        try:
            val = float(ttc_val)
            if val < 1.5:
                risk_score += 45.0
            elif val < 2.5:
                risk_score += 25.0
        except ValueError:
            pass
            
    final_risk_score = min(100.0, risk_score)
    
    if final_risk_score >= 75.0:
        risk_level = "CRITICAL"
    elif final_risk_score >= 45.0:
        risk_level = "WARNING"
        
    return {
        "final_risk_score": final_risk_score,
        "risk_level": risk_level
    }
