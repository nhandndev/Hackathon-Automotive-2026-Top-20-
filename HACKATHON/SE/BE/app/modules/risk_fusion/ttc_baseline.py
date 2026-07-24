"""
BTC TTC (Time-to-Collision) Baseline Implementation.
Formula: TTC = Distance / Closing_Speed
Rules:
1. If Closing_Speed <= 0 (target moving away or equal speed) -> TTC = "inf"
2. If Distance <= 0 -> TTC = 0.0
3. Otherwise TTC = min(10.0, max(0.1, round(Distance / Closing_Speed, 2)))
"""

from typing import Union

def calculate_btc_ttc_baseline(
    distance_m: float,
    closing_speed_ms: float
) -> Union[float, str]:
    """
    Computes BTC Time-to-Collision (TTC) baseline value.
    
    :param distance_m: Distance to target object ahead in meters
    :param closing_speed_ms: Relative approach speed in meters per second (v_ego - v_target)
    :return: TTC in seconds as float or "inf" string if no collision risk
    """
    if distance_m is None or distance_m < 0:
        return "inf"
        
    if closing_speed_ms is None or closing_speed_ms <= 0.1:
        # Target moving away or stationary distance increasing -> Infinite TTC
        return "inf"
        
    # Calculate TTC
    raw_ttc = distance_m / closing_speed_ms
    
    if raw_ttc > 10.0:
        return "inf"
    elif raw_ttc < 0.1:
        return 0.1
    else:
        return round(raw_ttc, 2)
