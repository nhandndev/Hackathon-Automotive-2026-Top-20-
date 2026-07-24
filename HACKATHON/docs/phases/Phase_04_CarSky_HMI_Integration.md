# PHASE 4: CARSKY HMI COCKPIT INTEGRATION (HƯỚNG DẪN KẾT NỐI DỮ LIỆU AI/SE SANG CARSKY HMI)

---

## 1. MỤC TIÊU VÀ BÀI TOÁN GIAO THỰC CỦA PHASE 4

### 1.1 Mục tiêu của Phase 4 (Cho User & AI)
- **Cho User (Fleet Manager / Team Leader)**: Hiểu rõ thao tác từng bước để lấy dữ liệu từ Output thô của AI (`T01d.json`), đi qua bộ lọc xử lý của SE Backend (`carsky_adapter.py`), và đẩy thẳng lên giao diện **CarSky HMI Cockpit** trong cabin xe để nhận trọn **+15 điểm thưởng từ BTC**.
- **Cho AI (Coding Assistant / Developer)**: Cung cấp đầy đủ hướng dẫn map dữ liệu (Data Field Mapping), mã nguồn Adapter, và script Luau chạy trong CarSky Script Node để khi gõ code là kết nối thành công 100%.

### 1.2 Bài toán thực tế Phase 4 giải quyết
User chưa biết thao tác kết nối dữ liệu từ AI/SE sang CarSky thế nào. Phase 4 đóng vai trò là **Cầu nối dữ liệu (Bridge Specification)** hướng dẫn từng bước click giao diện CarSky Workbench và từng dòng code Python/Luau để truyền dữ liệu thời gian thực.

---

## 2. QUY TRÌNH KẾT NỐI TỪ OUPUT AI/SE LÊN CARSKY HMI (STEP-BY-STEP)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [BƯỚC 1: AI RAW OUTPUT] - T01d.json (20 FPS)                             │
│  - speed_kmh: 65.2, min_ttc: 1.2s, driver.state: "drowsy"               │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ [BƯỚC 2: SE BACKEND PROCESSING] - carsky_adapter.py                     │
│  - Phát hiện rủi ro (min_ttc < 1.5s hoặc state == "drowsy")             │
│  - Sinh ai_generated_reasoning: "Tài xế A vi ngủ 2s tại vận tốc 65km/h" │
│  - Đóng gói JSON Payload chuẩn CarSky Schema                            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼ (HTTP POST / REST API Push)
┌─────────────────────────────────────────────────────────────────────────┐
│ [BƯỚC 3: CARSKY WORKBENCH CANVAS] - Nydus Blueprint                     │
│  - Node: Script Node (hmi_bridge.luau) / GPIO Panel Node                │
│  - Pin: KUKSA / VSS Pin hoặc HTTP Webhook Listener                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ [BƯỚC 4: CARSKY HMI COCKPIT WIDGETS] - Cabin Driver Display             │
│  - Signal Watch Widget: Hiện TTC (1.2s) & Vận tốc (65.2 km/h)           │
│  - Custom Alert Box Widget: Đèn Đỏ nhấp nháy + Tiếng Beep Còi báo      │
│  - Coaching Text Widget: Hiển thị lời nhắc từ GenAI Reasoning           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. BẢNG MAPPING CHI TIẾT CÁC TRƯỜNG DỮ LIỆU (DATA MAPPING TABLE)

| Đầu Vào Dữ Liệu (AI & SE Output) | Trường Dữ Liệu Gốc | Xử Lý Tại SE Backend (`carsky_adapter.py`) | Đích Đến Trên Giao Diện CarSky HMI |
| :--- | :--- | :--- | :--- |
| **Tốc độ xe** | `ego.speed_kmh` (65.2) | Giữ nguyên dạng float | **Gauge Speedometer / Signal Watch Widget** |
| **Thời gian va chạm** | `safety_metrics.min_ttc` (1.2) | Nếu chuỗi `"inf"`, đổi thành `999.0` | **TTC Assessment Gauge / Signal Watch Widget** |
| **Trạng thái tài xế** | `driver.state` (`drowsy`) | Map màu: `drowsy` $\rightarrow$ Đỏ (`CRITICAL`) | **Driver State Icon & Status Pill Badge** |
| **Điểm rủi ro** | `risk.final_risk_score` (84.0) | Tính $\text{Safe Score} = 100 - 84.0 = 16.0$ | **Safe Score Progress Bar Widget** |
| **Lời văn Coaching** | `ai_generated_reasoning.summary` | SE Backend tự động sinh lời văn GenAI | **Coaching Text Display Box Widget** |

---

## 4. MA NGUỒN VÀ THAO TÁC LẬP TRÌNH (CODE IMPLEMENTATION SPEC)

### 4.1 SE Backend Push Adapter (`backend/app/adapters/carsky_adapter.py`)

```python
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Cấu hình địa chỉ CarSky Workbench đang chạy (Local hoặc Cluster)
CARSKY_API_URL = "http://localhost:9000/v1/rooms/fptu-dms-room/hmi/push"
CARSKY_API_KEY = "carsky_secret_key_123"

async def push_hmi_alert_to_carsky(enriched_frame: Dict[str, Any]) -> bool:
    """
    Hàm đẩy dữ liệu từ Output AI & SE Backend sang CarSky HMI Cockpit.
    """
    telemetry = enriched_frame.get("telemetry_frame", enriched_frame)
    ego = telemetry.get("ego", {})
    driver = telemetry.get("driver", {})
    safety = telemetry.get("safety_metrics", {})
    reasoning = enriched_frame.get("ai_generated_reasoning", {})

    min_ttc = safety.get("min_ttc", 999.0)
    ttc_val = 999.0 if str(min_ttc).lower() in ["inf", "infinity"] else float(min_ttc)
    driver_state = driver.get("state", "normal")

    # Đóng gói Payload theo đúng Schema mà CarSky HMI Widgets yêu cầu
    carsky_payload = {
        "device_target": "in_cabin_hmi",
        "timestamp": telemetry.get("timestamp", 0.0),
        "telemetry": {
            "speed_kmh": ego.get("speed_kmh", 0.0),
            "ttc_seconds": ttc_val,
            "driver_state": driver_state,
            "alertness_score": driver.get("alertness_score", 1.0)
        },
        "hmi_widgets": {
            "alert_banner": {
                "active": (ttc_val < 1.5 or driver_state in ["drowsy", "microsleep"]),
                "title": "DROWSY DRIVER DETECTED" if driver_state in ["drowsy", "microsleep"] else "COLLISION WARNING",
                "severity": "CRITICAL" if ttc_val < 1.5 else "WARNING",
                "coaching_message": reasoning.get("summary", "Chú ý giữ khoảng cách an toàn!"),
                "trigger_audio_beep": True
            }
        }
    }

    headers = {"Authorization": f"Bearer {CARSKY_API_KEY}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(CARSKY_API_URL, json=carsky_payload, headers=headers, timeout=1.5)
            return res.status_code == 200
    except Exception as e:
        logger.warning(f"CarSky HMI connection skipped: {str(e)}")
        return False
```

### 4.2 Script Node Luau trên CarSky Canvas (`hmi_bridge.luau`)
Dán mã Luau này vào phần Config của **Script Node** trên CarSky Nydus Canvas:

```luau
-- File: hmi_bridge.luau (Chạy trong CarSky Script Node)
local pins = ...

-- Lắng nghe gói JSON push từ SE Backend
pins.net.on_json_received(function(data)
    if data.hmi_widgets and data.hmi_widgets.alert_banner then
        local banner = data.hmi_widgets.alert_banner
        
        if banner.active then
            -- 1. Bật Đèn LED Đỏ nhấp nháy trên CarSky GPIO Panel Node
            pins.gpio.set_pin("RED_ALARM_LED", 1)
            -- 2. Đẩy dòng chữ Coaching từ GenAI lên Text Box Widget
            pins.display.set_text("COACHING_WIDGET", banner.coaching_message)
            -- 3. Phát tiếng còi BEEP báo động 880Hz
            if banner.trigger_audio_beep then
                pins.audio.play_beep(880, 0.5)
            end
        else
            pins.gpio.set_pin("RED_ALARM_LED", 0)
        end
    end
end)
```

---

## 5. TIÊU CHÍ REVIEW & NGHIỆM THU PHASE 4 (CHECKLIST FOR USER)

- [ ] **Review Thao tác Kết nối**: User đã hiểu rõ luồng đi từ `T01d.json` $\rightarrow$ `carsky_adapter.py` $\rightarrow$ REST API $\rightarrow$ CarSky HMI Widgets.
- [ ] **Review Hiển thị CarSky**: Xác nhận màn hình HMI trong cabin nhấp nháy đỏ và phát tiếng còi khi `min_ttc < 1.5s` hoặc `driver.state == 'drowsy'`.
- [ ] **Nghiệm thu Code**: AI/Developer test thử file `carsky_adapter.py` chạy mượt mà không làm trễ nhịp Stream 20 FPS.

