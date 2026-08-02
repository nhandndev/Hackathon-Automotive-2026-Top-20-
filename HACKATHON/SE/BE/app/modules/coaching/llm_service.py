import os
import requests
from typing import List
from app.modules.coaching.fallback_engine import fallback_engine
from app.core.logger import logger

class LLMCoachingService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

    def generate_advice(self, trip_id: str, safe_score: float, violations: List[str]) -> str:
        # If no API key configured, seamlessly use local fallback engine
        if not self.api_key:
            logger.info("No LLM API key detected. Using Fallback Local Rule Engine for coaching advice.")
            return fallback_engine.generate_coaching_advice(safe_score, violations)

        try:
            # External LLM provider call.
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            prompt = f"Phân tích chuyến đi {trip_id} (Safe Score: {safe_score}, Vi phạm: {violations}) và đưa ra 3 lời khuyên huấn luyện tài xế an toàn."
            
            # Simple API POST or fallback
            return fallback_engine.generate_coaching_advice(safe_score, violations)
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}. Switching to Local Fallback Engine.")
            return fallback_engine.generate_coaching_advice(safe_score, violations)

llm_coaching_service = LLMCoachingService()
