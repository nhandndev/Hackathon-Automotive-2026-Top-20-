from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from app.modules.coaching.llm_service import llm_coaching_service

router = APIRouter(prefix="/coaching", tags=["GenAI Coaching Agent"])

class CoachingRequest(BaseModel):
    trip_id: str
    safe_score: Optional[float] = 85.0
    top_violations: Optional[List[str]] = Field(default_factory=list)

@router.post("/generate")
async def generate_coaching_advice(req: CoachingRequest):
    """Generates streaming/text coaching advisory recommendations for driver training."""
    advice_text = llm_coaching_service.generate_advice(
        trip_id=req.trip_id,
        safe_score=req.safe_score or 85.0,
        violations=req.top_violations or []
    )
    return {
        "trip_id": req.trip_id,
        "safe_score": req.safe_score,
        "advice": advice_text
    }
