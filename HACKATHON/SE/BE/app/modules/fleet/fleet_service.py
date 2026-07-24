from typing import List, Dict, Any
from app.adapters.csv_file_adapter import CSVFileAdapter
from app.modules.risk_fusion.risk_service import risk_service

class FleetService:
    def __init__(self):
        self.adapter = CSVFileAdapter()

    def get_fleet_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        # Trips T01d through T10d
        trip_ids = [f"T{i:02d}d" for i in range(1, 11)]
        drivers = ["Nguyen Van A", "Tran Van B", "Le Van C", "Pham Van D", "Hoang Van E",
                   "Vu Van F", "Dang Van G", "Bui Van H", "Dinh Van I", "Do Van K"]

        summary_list = []
        for idx, t_id in enumerate(trip_ids[:limit]):
            res = risk_service.process_trip_risk(t_id)
            safe_score = res["predicted_safe_score"]
            
            summary_list.append({
                "trip_id": t_id,
                "driver_name": drivers[idx % len(drivers)],
                "vehicle_id": f"29A-{12345 + idx}",
                "predicted_safe_score": safe_score,
                "avg_risk_score": res["avg_risk_score"],
                "total_violations": res["total_violations"],
                "status": "SAFE" if safe_score >= 80.0 else ("WARNING" if safe_score >= 60.0 else "DANGER")
            })

        # Sort descending by safe score for Leaderboard (Top 1-2-3)
        summary_list.sort(key=lambda x: x["predicted_safe_score"], reverse=True)
        return summary_list

    def get_trip_trajectory(self, trip_id: str) -> List[Dict[str, Any]]:
        frames = self.adapter.load_trip_data(trip_id)
        trajectory = []
        for frame in frames:
            tel = frame["telemetry"]
            trajectory.append({
                "frame_id": frame["frame_id"],
                "timestamp": frame["timestamp"],
                "lat": tel.get("latitude", 10.762622),
                "lon": tel.get("longitude", 106.660172),
                "speed_kmh": tel.get("speed_kmh", 0.0),
                "heading": tel.get("heading_deg", 0.0)
            })
        return trajectory

fleet_service = FleetService()
