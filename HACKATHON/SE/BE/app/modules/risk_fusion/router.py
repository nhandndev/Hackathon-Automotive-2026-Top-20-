from fastapi import APIRouter
from app.modules.risk_fusion.risk_service import risk_service

router = APIRouter(prefix="/api/risk", tags=["Risk Fusion Scoring Engine"])

@router.get("/{trip_id}")
async def get_trip_risk_summary(trip_id: str):
    """Returns trip safe score and risk summary statistics."""
    return risk_service.process_trip_risk(trip_id)
