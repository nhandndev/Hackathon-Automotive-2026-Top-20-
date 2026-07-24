from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.modules.streaming.ws_manager import ws_manager
from app.modules.streaming.replay_service import replay_service

router = APIRouter(tags=["20 FPS Stream Replay"])

@router.websocket("/ws/replay/{trip_id}")
async def websocket_replay_endpoint(websocket: WebSocket, trip_id: str):
    await ws_manager.connect(websocket, trip_id)
    try:
        await replay_service.stream_replay(websocket, trip_id)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, trip_id)
    except Exception:
        ws_manager.disconnect(websocket, trip_id)
