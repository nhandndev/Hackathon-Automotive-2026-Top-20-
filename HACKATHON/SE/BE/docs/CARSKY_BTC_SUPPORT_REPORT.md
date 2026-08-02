# Báo cáo kỹ thuật CarSky/KUKSA — FPTU DMS Vision

> Tài liệu này ghi nhận sự cố tích hợp để gửi BTC khi cần. Không chứa tài khoản,
> API key hoặc secret. Trạng thái cloud phải được operator xác nhận lại tại thời
> điểm rehearsal; nội dung trong repo không thể chứng minh deployment đang Running.

## 1. Phạm vi

Luồng mục tiêu:

```text
AI DecisionEvent
  → POST Backend /api/v1/alerts
  → Backend CarSky mapper/publisher
  → CarSky Signals API
  → KUKSA Signal Broker
  → HMI Bridge
  → Android HMI
```

Backend không thay đổi quyết định AI. Nó chỉ dịch canonical event sang 14 VSS
paths và gửi bất đồng bộ đến CarSky.

## 2. Sự cố đã tìm thấy trong repository

File `SE/BE/carsky/dms-vss-signals.json` từng chứa merge-conflict và hai định dạng
khác nhau:

- một nhánh là JSON object/map;
- một nhánh bọc object trong JSON array.

KUKSA VSS artifact yêu cầu root là object/map. Dạng array hoặc file còn marker
`<<<<<<<` không phải JSON hợp lệ và có thể làm broker không khởi động.

Repository đã được sửa về một JSON object hợp lệ, chứa đúng 14 paths mà mapper và
HMI sử dụng:

```text
Vehicle.Speed
Vehicle.SpeedLimit
Vehicle.Driver.State
Vehicle.Driver.AlertnessScore
Vehicle.ADAS.MinTTC
Vehicle.ADAS.Headway
Vehicle.ADAS.FinalRiskScore
Vehicle.ADAS.CriticalAlert
Vehicle.ADAS.DisplaySeverity
Vehicle.ADAS.AlertReasonCode
Vehicle.ADAS.RecommendedActionCode
Vehicle.ADAS.EventTransition
Vehicle.ADAS.AIStatus
Vehicle.ADAS.DataAgeMs
```

`MinTTC` và `Headway` chỉ được gửi khi hữu hạn; Backend không đổi `Infinity` thành
0. Các field quyết định (`severity`, lifecycle, reason) giữ nguyên semantics AI.

## 3. Điều cần BTC/CarSky hỗ trợ nếu deployment vẫn lỗi

Nếu blueprint hợp lệ nhưng node vẫn `Pending`, `CrashLoopBackOff` hoặc không thấy
signal, nhờ BTC kiểm tra:

1. VSS artifact version có thực sự mount đúng bytes vào KUKSA Broker không.
2. Runtime-generated command/arguments có trỏ đúng VSS file không.
3. Broker, bridge và Android node có cùng room/network và đúng edge không.
4. Signals API credential có quyền actuate đúng room/node không.
5. Log broker có lỗi parse schema, image pull hay volume mount không.

Thông tin cần gửi kèm, đã che secret:

- room/deployment ID;
- blueprint/version và VSS artifact/version;
- trạng thái ba node;
- broker/bridge log;
- HTTP status + response body của request `values` hoặc `actuate`;
- ảnh Signal Watch và Android Screen.

## 4. Kiểm tra local trước khi gửi support request

Từ `HACKATHON/SE/BE`, sau khi cài requirements và cấu hình `.env`:

```powershell
python -c "import json, pathlib; json.loads(pathlib.Path('carsky/dms-vss-signals.json').read_text(encoding='utf-8')); print('VSS JSON OK')"
python scripts\carsky_phase05.py status
python scripts\carsky_phase05.py nodes
python scripts\carsky_phase05.py values
```

Sau đó chạy Backend và gửi một canonical event từ AI. `scenario warning` hoặc
`scenario critical` chỉ là test transport/HMI dự phòng, không phải proof AI
end-to-end.

## 5. Tiêu chí nghiệm thu

- deployment có đủ Broker, Bridge và Android node ở trạng thái Running;
- Backend nhận DecisionEvent và không tạo duplicate khi retry cùng key;
- event audience `driver_display` được publisher nhận;
- Signal Watch đổi đúng severity/reason/action/transition;
- Android HMI đổi cùng trạng thái;
- CarSky lỗi không làm endpoint Backend hoặc Dashboard WebSocket bị treo;
- không lộ credential trong log, ảnh hoặc repository.

Runbook chính: [`../../../reportbtc/C2_END_TO_END_DEMO_SCRIPT.md`](../../../reportbtc/C2_END_TO_END_DEMO_SCRIPT.md).
