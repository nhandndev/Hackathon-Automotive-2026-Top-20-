from typing import List, Dict, Any

class FallbackRuleEngine:
    """Local Rule-based template fallback engine when GenAI API key is unavailable or offline."""

    def generate_coaching_advice(self, safe_score: float, violations: List[str]) -> str:
        advice_parts = []
        
        if safe_score >= 90.0:
            advice_parts.append("Tài xế có phong cách lái xe rất an toàn (Safe Score > 90 điểm). Vận tốc và khoảng cách quan sát luôn trong tầm kiểm soát.")
        elif safe_score >= 70.0:
            advice_parts.append("Tài xế duy trì mức độ an toàn trung bình khá (Safe Score 70-90 điểm). Cần chú ý hơn tới nhịp phanh và duy trì khoảng cách an toàn.")
        else:
            advice_parts.append("Tài xế có nguy cơ rủi ro cao (Safe Score < 70 điểm). Hệ thống khuyến nghị quản lý đoàn xe nhắc nhở và đào tạo lại.")

        if "MICROSLEEP" in violations or "DROWSY" in violations:
            advice_parts.append("⚠️ CẢNH BÁO MỆT MỎI: Phát hiện dấu hiệu vi ngủ/buồn ngủ trong chuyến đi. Khuyến nghị tài xế tấp xe vào lề đường nghỉ ngơi 15-20 phút trước khi tiếp tục hành trình.")
        if "HARSH_BRAKE" in violations:
            advice_parts.append("⚠️ HÀNH VI PHANH GẤP: Phát hiện các sự kiện giảm tốc đột ngột (longitudinal accel < -3.0 m/s²). Khuyến nghị chủ động giảm tốc từ xa khi tới giao lộ.")
        if "HARSH_CORNER" in violations:
            advice_parts.append("⚠️ HÀNH VI CUA GẮT: Phát hiện lực ly tâm ngang lớn (lateral accel > 3.5 m/s²). Khuyến nghị giảm tốc dưới 30 km/h trước khi vào khúc cua.")

        advice_parts.append("💡 Khuyên dùng: Sử dụng tính năng cảnh báo ADAS cabin real-time để duy trì phản ứng < 2.0 giây chuẩn NHTSA.")
        
        return "\n\n".join(advice_parts)

fallback_engine = FallbackRuleEngine()
