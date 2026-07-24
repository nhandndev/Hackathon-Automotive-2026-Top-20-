from typing import Dict, Any
from app.adapters.csv_file_adapter import CSVFileAdapter
from app.modules.risk_fusion.algorithms.nhtsa_v1 import NHTSARiskModelV1
from app.modules.event_detection.detector_registry import detector_registry

class RiskService:
    def __init__(self):
        self.adapter = CSVFileAdapter()
        self.model = NHTSARiskModelV1()

    def process_trip_risk(self, trip_id: str) -> Dict[str, Any]:
        frames = self.adapter.load_trip_data(trip_id)
        frame_risks = []
        all_events = []

        for frame in frames:
            telemetry = frame["telemetry"]
            ai_vision = frame["ai_vision"]
            ttc_val = 999.0 if ai_vision["predicted_ttc"] == "inf" else float(ai_vision["predicted_ttc"])
            
            detected = detector_registry.run_detectors(telemetry, ai_vision)
            active_events = [ev["event_type"] for ev in detected]
            all_events.extend(detected)

            r_score = self.model.calculate_frame_risk(
                predicted_ttc=ttc_val,
                driver_state=ai_vision["predicted_driver_state"],
                active_events=active_events,
                telemetry=telemetry
            )
            frame_risks.append(r_score)

        safe_score = self.model.calculate_trip_safe_score(frame_risks, all_events)
        
        return {
            "trip_id": trip_id,
            "total_frames": len(frames),
            "predicted_safe_score": safe_score,
            "max_risk_score": max(frame_risks) if frame_risks else 0.0,
            "avg_risk_score": round(sum(frame_risks)/len(frame_risks), 1) if frame_risks else 0.0,
            "total_violations": len(all_events)
        }

risk_service = RiskService()
