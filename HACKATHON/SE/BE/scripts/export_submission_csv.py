import os
import sys
import pandas as pd

# Add parent directory to sys.path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.adapters.csv_file_adapter import CSVFileAdapter
from app.modules.risk_fusion.algorithms.nhtsa_v1 import NHTSARiskModelV1
from app.modules.event_detection.detector_registry import detector_registry

def export_all_submissions(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    adapter = CSVFileAdapter()
    risk_model = NHTSARiskModelV1()

    trip_ids = [f"T{i:02d}d" for i in range(1, 11)]

    for trip_id in trip_ids:
        frames = adapter.load_trip_data(trip_id)
        rows = []

        for frame in frames:
            frame_id = frame["frame_id"]
            timestamp = frame["timestamp"]
            telemetry = frame["telemetry"]
            ai_vision = frame["ai_vision"]

            predicted_ttc = ai_vision["predicted_ttc"]
            predicted_driver_state = ai_vision["predicted_driver_state"]

            # Calculate risk score
            ttc_val = 999.0 if predicted_ttc == "inf" else float(predicted_ttc)
            detected = detector_registry.run_detectors(telemetry, ai_vision)
            active_events = [ev["event_type"] for ev in detected]

            predicted_risk_score = risk_model.calculate_frame_risk(
                predicted_ttc=ttc_val,
                driver_state=predicted_driver_state,
                active_events=active_events,
                telemetry=telemetry
            )

            rows.append({
                "frame_id": frame_id,
                "timestamp": timestamp,
                "predicted_ttc": predicted_ttc,
                "predicted_driver_state": predicted_driver_state,
                "predicted_risk_score": round(predicted_risk_score, 1)
            })

        df = pd.DataFrame(rows)
        # Ensure exact 5 columns order
        df = df[["frame_id", "timestamp", "predicted_ttc", "predicted_driver_state", "predicted_risk_score"]]
        
        csv_filename = os.path.join(output_dir, f"{trip_id}.csv")
        df.to_csv(csv_filename, index=False)
        print(f"Exported Submission CSV: {csv_filename} ({len(df)} rows x {len(df.columns)} cols)")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "submissions")
    export_all_submissions(out_dir)
