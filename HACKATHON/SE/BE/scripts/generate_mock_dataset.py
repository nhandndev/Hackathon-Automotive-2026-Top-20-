import os
import json
import math

def generate_mock_dataset(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    trip_ids = [f"T{i:02d}d" for i in range(1, 11)]

    for trip_id in trip_ids:
        frames = []
        for idx in range(1800):  # 90s @ 20 FPS
            t = round(idx * 0.05, 3)
            
            # Inject hazard episode at t=22.5s for T01d
            if trip_id == "T01d" and 430 <= idx <= 470:
                ttc = round(max(0.5, 4.0 - (idx - 430) * 0.15), 2)
                driver_state = "microsleep" if idx > 445 else "drowsy"
                accel_x = -3.8
                accel_y = 0.8
                speed = max(10.0, 65.0 - (idx - 430) * 1.2)
            else:
                ttc = "inf"
                driver_state = "alert"
                accel_x = -0.2
                accel_y = 0.1
                speed = 65.0 + math.sin(idx * 0.05) * 4.0

            frames.append({
                "frame_id": idx,
                "timestamp": t,
                "telemetry": {
                    "speed_kmh": round(speed, 2),
                    "longitudinal_accel": round(accel_x, 2),
                    "lateral_accel": round(accel_y, 2),
                    "latitude": round(10.762622 + idx * 0.00001, 6),
                    "longitude": round(106.660172 + idx * 0.00001, 6),
                    "heading_deg": round((idx * 0.5) % 360, 1)
                },
                "ai_vision": {
                    "predicted_ttc": ttc,
                    "predicted_driver_state": driver_state,
                    "alertness_score": 0.15 if driver_state in ["drowsy", "microsleep"] else 0.95
                }
            })

        out_path = os.path.join(output_dir, f"{trip_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"trip_id": trip_id, "total_frames": 1800, "frames": frames}, f, indent=2)
        print(f"Generated mock dataset: {out_path} (1800 frames)")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..")
    generate_mock_dataset(out_dir)
