# PHASE 1: CORE SE & AI SYSTEM ALIGNMENT (NỀN TẢNG CỐT LÕI & CHUẨN HÓA GIAO TIẾP DỮ LIỆU)

---

## 1. MỤC TIÊU VÀ BÀI TOÁN THỰC TẾ CỦA PHASE 1

### 1.1 Mục tiêu của Phase 1 (Cho User & AI)
- **Cho User (Fleet Manager / Leader)**: Nắm rõ ranh giới phân định chính xác giữa AI Team và SE Team. Hiểu nguyên gốc JSON payload thô do AI sinh ra và cách SE Backend xử lý sinh lời văn giải thích (**AI Risk Reasoning**) & tư vấn đào tạo (**Coaching**).
- **Cho AI (Coding Assistant / Developer)**: Cung cấp 100% Data Schema chuẩn từ dataset AI (`T01d.json`), định nghĩa Pydantic Model chính xác theo nguyên gốc để SE Backend nạp dữ liệu và tự động sinh phần Reasoning.

### 1.2 Bài toán thực tế Phase 1 giải quyết
AI Team chỉ xử lý mô hình thị giác và động lực học (xuất ra các con số thô: `speed_kmh`, `predicted_driver_state`, `min_ttc`, `final_risk_score`). **SE Team sẽ nhận các con số thô này và dùng SE Backend GenAI Engine để tự động tổng hợp sinh ra chuỗi `ai_generated_reasoning`** (lời văn giải thích lý do rủi ro, mức độ nghiêm trọng và hành động khuyến nghị cho Fleet Manager).

---

## 2. MA TRẬN PHÂN ĐỊNH TRÁCH NHIỆM CHÍNH THỨC SE vs AI

| Thành phần / Trường Dữ Liệu | Đội Ngũ Cung Cấp / Phụ Trách | Chi Tiết Xử Lý & Hiển Thị trên Dashboard |
| :--- | :---: | :--- |
| **`trip_id` & `metadata`** | **AI Team (Cung cấp nguyên gốc)** | Tên chuyến đi, thời lượng (`duration_sec`), tốc độ giới hạn (`speed_limit_kmh: 80`). SE hiển thị Header Card. |
| **`ego` Telemetry** | **AI Team (Cung cấp nguyên gốc)** | Tốc độ (`speed_kmh`), gia tốc dọc/ngang, tọa độ GPS (`geolocation`). SE render Đồng hồ tốc độ & Bản đồ Leaflet. |
| **`driver` DMS State** | **AI Team (Cung cấp nguyên gốc)** | Trạng thái tài xế (`distracted`, `drowsy`), chỉ số tỉnh táo (`alertness_score`), `eye_state`, `mouth_state`, `nthu_subject_id`. SE render Badge góc Video. |
| **`safety_metrics` ADAS** | **AI Team (Cung cấp nguyên gốc)** | Chỉ số va chạm va chạm `min_ttc` (có thể là `Infinity`), `headway_sec`, cờ vi phạm `behavior_flags` (`harsh_brake`, `speeding`, `tailgating`). SE vẽ Indicator & Timeline. |
| **`risk` Scores** | **AI Team (Cung cấp nguyên gốc)** | Điểm phạt thô `base_risk`, hệ số tài xế `driver_factor`, và điểm rủi ro tổng hợp `final_risk_score`. |
| **`ai_generated_reasoning`** | **SE Backend (Tự động Sinh)** | **SE Backend gọi GenAI/Template Engine để tự động tạo** đoạn văn giải thích `summary`, mức độ `severity` (`CRITICAL`), và hành động `recommended_action`. |

---

## 3. CHUẨN DỮ LIỆU JSON PAYLOAD NGUYÊN GỐC (DATA CONTRACT)

### 3.1 Dữ liệu thô nguyên gốc từ AI Team (AI Payload Output)
Mỗi frame (20 FPS - 50ms), AI Team cấp gói JSON thô chứa dữ liệu telemetry, DMS và điểm rủi ro:

```json
{
  "trip_id": "T01d",
  "metadata": {
    "trip_id": "T01d",
    "description": "DEBUG 30s: highway evening, motorcycle cut-in + mild lead brake (compressed)",
    "duration_sec": 90,
    "fps": 20,
    "map": "Town01",
    "driver_profile": "normal",
    "carla_version": "0.9.15",
    "random_seed": 1001,
    "speed_limit_kmh": 80
  },
  "telemetry_frame": {
    "frame_id": 450,
    "timestamp": 22.5,
    "ego": {
      "speed_kmh": 65.2,
      "longitudinal_accel": -4.2,
      "lateral_accel": 0.15,
      "geolocation": {
        "lat": -0.00123,
        "lon": -0.000485,
        "alt": 0.16
      }
    },
    "driver": {
      "state": "drowsy",
      "alertness_score": 0.15,
      "eye_state": "closed",
      "head_pose": "straight",
      "mouth_state": "normal",
      "nthu_subject_id": "14"
    },
    "safety_metrics": {
      "min_ttc": 1.2,
      "headway_sec": 0.85,
      "behavior_flags": {
        "harsh_brake": true,
        "harsh_accel": false,
        "harsh_corner": false,
        "speeding": false,
        "tailgating": true
      }
    },
    "risk": {
      "base_risk": 35.0,
      "driver_factor": 2.4,
      "final_risk_score": 84.0
    }
  }
}
```

---

### 3.2 Dữ liệu sau khi SE Backend bổ sung phần Reasoning (SE Enriched Payload)
SE Backend tự động tổng hợp dữ liệu thô trên để sinh khối `ai_generated_reasoning` truyền cho Dashboard Frontend & CarSky HMI:

```json
{
  "ai_generated_reasoning": {
    "summary": "Tài xế A (Xe VH-04) sụt giảm tỉnh táo xuống 15% do vi ngủ (microsleep) kéo dài 2 giây. Xe phanh gấp ở vận tốc 65km/h với khoảng cách va chạm TTC nguy kịch 1.2s.",
    "severity": "CRITICAL",
    "recommended_action": "Gửi lịch nghỉ đề xuất & Gọi điện can thiệp"
  }
}
```

---

## 4. CODE IMPLEMENTATION SPEC (DÀNH CHO AI / DEVELOPER)

### 4.1 Pydantic Model Schema (`backend/app/domain/schemas/telemetry.py`)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Union

class GeoLocation(BaseModel):
    lat: float
    lon: float
    alt: Optional[float] = 0.0

class EgoData(BaseModel):
    speed_kmh: float
    longitudinal_accel: float
    lateral_accel: Optional[float] = 0.0
    geolocation: GeoLocation

class DriverData(BaseModel):
    state: str  # alert, distracted, drowsy, yawning, microsleep
    alertness_score: float
    eye_state: Optional[str] = "open"
    head_pose: Optional[str] = "straight"
    mouth_state: Optional[str] = "normal"
    nthu_subject_id: Optional[str] = "14"

class BehaviorFlags(BaseModel):
    harsh_brake: bool = False
    harsh_accel: bool = False
    harsh_corner: bool = False
    speeding: bool = False
    tailgating: bool = False

class SafetyMetrics(BaseModel):
    min_ttc: Union[float, str]  # Chấp nhận số float hoặc chuỗi "Infinity"/"inf"
    headway_sec: Union[float, str]
    behavior_flags: BehaviorFlags

class RiskData(BaseModel):
    base_risk: float = 0.0
    driver_factor: float = 1.0
    final_risk_score: float = Field(..., ge=0.0, le=100.0)

class ReasoningData(BaseModel):
    summary: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommended_action: str

# Schema dữ liệu thô nguyên gốc từ AI Team
class RawAITelemetryFrame(BaseModel):
    model_config = ConfigDict(extra='allow')
    frame_id: int
    timestamp: float
    ego: EgoData
    driver: DriverData
    safety_metrics: SafetyMetrics
    risk: RiskData

# Schema đầy đủ sau khi SE Backend sinh thêm phần Reasoning
class EnrichedTelemetryFrame(RawAITelemetryFrame):
    ai_generated_reasoning: ReasoningData
```

---

## 5. TIÊU CHÍ REVIEW & NGHIỆM THU PHASE 1 (CHECKLIST FOR USER)

- [ ] **Review Phân công Trách nhiệm**: User xác nhận AI Team chỉ cung cấp dữ liệu thô nguyên gốc (`telemetry`, `driver`, `safety_metrics`, `risk`), phần `ai_generated_reasoning` do SE Backend tự sinh.
- [ ] **Review Data Payload**: User duyệt định dạng JSON nguyên gốc khớp 100% với file dữ liệu mẫu `T01d.json`.
- [ ] **Nghiệm thu Code**: AI/Developer kiểm tra Pydantic Schema `RawAITelemetryFrame` xử lý tốt các giá trị `Infinity` của `min_ttc` mà không bị ném ngoại lệ.

