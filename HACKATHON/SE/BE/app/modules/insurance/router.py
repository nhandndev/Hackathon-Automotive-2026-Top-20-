from fastapi import APIRouter
from app.modules.insurance.insurance_service import insurance_service

router = APIRouter(prefix="/api/trip", tags=["Business & Insurance Report"])

@router.get("/{trip_id}/report")
async def get_insurance_report(trip_id: str):
    """Returns aggregated driver state distribution and SHAP breakdown for insurance report UI."""
    return insurance_service.get_insurance_report(trip_id)
