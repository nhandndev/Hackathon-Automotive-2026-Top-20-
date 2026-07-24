from fastapi import APIRouter, Query
from app.modules.fleet.fleet_service import fleet_service

router = APIRouter(tags=["Live Fleet Manager & GPS Trajectory"])

@router.get("/api/fleet/summary")
async def get_fleet_summary(limit: int = Query(10, ge=1, le=50)):
    """Returns list of all fleet drivers ranked by safe score for Leaderboard."""
    return fleet_service.get_fleet_summary(limit)

@router.get("/api/trip/{trip_id}/trajectory")
async def get_trip_trajectory(trip_id: str):
    """Returns GPS trajectory polyline array for Leaflet map."""
    return fleet_service.get_trip_trajectory(trip_id)
