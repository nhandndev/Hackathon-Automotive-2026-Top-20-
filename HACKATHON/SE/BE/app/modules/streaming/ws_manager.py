from fastapi import WebSocket
from typing import List, Dict
from app.core.logger import logger

class ConnectionManager:
    """Manages active WebSockets connections per trip session."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, trip_id: str):
        await websocket.accept()
        if trip_id not in self.active_connections:
            self.active_connections[trip_id] = []
        self.active_connections[trip_id].append(websocket)
        logger.info(f"WebSocket Client connected to trip '{trip_id}'. Active clients: {len(self.active_connections[trip_id])}")

    def disconnect(self, websocket: WebSocket, trip_id: str):
        if trip_id in self.active_connections:
            if websocket in self.active_connections[trip_id]:
                self.active_connections[trip_id].remove(websocket)
            if not self.active_connections[trip_id]:
                del self.active_connections[trip_id]
        logger.info(f"WebSocket Client disconnected from trip '{trip_id}'.")

    async def broadcast_to_trip(self, trip_id: str, message: dict):
        if trip_id in self.active_connections:
            for connection in self.active_connections[trip_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")

ws_manager = ConnectionManager()
