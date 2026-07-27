from fastapi import APIRouter, Query
from typing import Optional
from app.adapters.csv_file_adapter import CSVFileAdapter
from app.modules.event_detection.detector_registry import detector_registry

router = APIRouter(prefix="/trip", tags=["Risk Event Detection"])
adapter = CSVFileAdapter()

@router.get("/{trip_id}/events")
async def get_trip_events(trip_id: str, type: Optional[str] = Query(None)):
    """Returns historical list of detected risk events for timeline UI."""
    frames = adapter.load_trip_data(trip_id)
    all_events = []
    
    for frame in frames:
        telemetry = frame["telemetry"]
        ai_vision = frame["ai_vision"]
        timestamp = frame["timestamp"]
        
        detected = detector_registry.run_detectors(telemetry, ai_vision)
        for ev in detected:
            if type is None or ev["event_type"] == type.upper():
                all_events.append({
                    "event_id": len(all_events) + 1,
                    "frame_id": frame["frame_id"],
                    "timestamp": timestamp,
                    "event_type": ev["event_type"],
                    "severity": ev["severity"],
                    "description": ev["description"],
                    "value": ev["value"]
                })
                
    return {
        "trip_id": trip_id,
        "total_events": len(all_events),
        "events": all_events
    }
