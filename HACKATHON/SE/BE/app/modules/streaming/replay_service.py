import asyncio
import json
from typing import Dict, Any, List
from app.adapters.csv_file_adapter import CSVFileAdapter
from app.modules.event_detection.detector_registry import detector_registry
from app.modules.risk_fusion.algorithms.nhtsa_v1 import NHTSARiskModelV1
from app.core.config import settings
from app.core.logger import logger

class ReplayService:
    """Service executing 20 FPS stream replay timer loop (dt = 50ms)."""

    def __init__(self):
        self.adapter = CSVFileAdapter()
        self.risk_model = NHTSARiskModelV1()

    async def stream_replay(self, websocket, trip_id: str):
        frames = self.adapter.load_trip_data(trip_id)
        if not frames:
            await websocket.send_json({"error": f"No data found for trip {trip_id}"})
            return

        current_index = 0
        is_playing = True
        speed = 1.0

        try:
            while True:
                # Listen for incoming control messages without blocking stream loop
                try:
                    # Non-blocking receive check if client sent control command
                    raw_msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
                    ctrl = json.loads(raw_msg)
                    action = ctrl.get("action")
                    if action == "pause":
                        is_playing = False
                    elif action == "play":
                        is_playing = True
                    elif action == "seek":
                        target_frame = ctrl.get("frame", 0)
                        current_index = max(0, min(target_frame, len(frames) - 1))
                    elif action == "speed":
                        speed = max(0.25, min(float(ctrl.get("speed", 1.0)), 4.0))
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    pass

                if is_playing and current_index < len(frames):
                    frame_data = frames[current_index]
                    telemetry = frame_data["telemetry"]
                    ai_vision = frame_data["ai_vision"]

                    # 1. Run Event Detectors
                    detected_events = detector_registry.run_detectors(telemetry, ai_vision)
                    active_events = [ev["event_type"] for ev in detected_events]

                    # 2. Run Risk Fusion Engine
                    predicted_ttc = ai_vision["predicted_ttc"]
                    ttc_val = 999.0 if predicted_ttc == "inf" else float(predicted_ttc)
                    driver_state = ai_vision["predicted_driver_state"]
                    
                    risk_score = self.risk_model.calculate_frame_risk(
                        predicted_ttc=ttc_val,
                        driver_state=driver_state,
                        active_events=active_events,
                        telemetry=telemetry
                    )

                    payload = {
                        "frame_id": frame_data["frame_id"],
                        "timestamp": frame_data["timestamp"],
                        "telemetry": telemetry,
                        "ai_vision": ai_vision,
                        "risk_fusion": {
                            "predicted_risk_score": round(risk_score, 1),
                            "is_compound_critical": risk_score > 60.0 or ttc_val <= 1.5 or driver_state == "microsleep",
                            "active_events": active_events
                        }
                    }

                    await websocket.send_json(payload)
                    current_index += 1

                    if current_index >= len(frames):
                        current_index = 0  # Loop stream

                await asyncio.sleep(settings.FRAME_INTERVAL_SEC / speed)
        except Exception as e:
            logger.info(f"Replay stream ended for trip {trip_id}: {e}")

replay_service = ReplayService()
