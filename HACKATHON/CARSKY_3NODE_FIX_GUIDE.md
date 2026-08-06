# HƯỚNG DẪN CHI TIẾT LƯU TRÌNH VẬN HÀNH & FIX LỖI CARSKY 3-NODE TOPOLOGY
## DỰ ÁN: FPTU DMS VISION — AUTOMOTIVE HMI INTEGRATION

> Tài liệu này hướng dẫn chi tiết từng bước vận hành và khắc phục sự cố cho luồng chuẩn 3 Nodes trên CarSky Workbench (Node Producer đã được gỡ bỏ):
> ```text
> Backend/Mac ──(REST Signal API)──> [DMS Signal Broker] ──> [DMS HMI Bridge] ──> [DMS Android HMI]
> ```

---

## 1. TỔNG QUAN TOPOLOGY VÀ LUỒNG CHUYỂN DỮ LIỆU chuẩn 3 NODES

Hệ thống được thiết kế theo đúng chuẩn kiến trúc Connected Car:

1. **Backend / REST API (Nguồn dữ liệu):** AI Pipeline hoặc script Python gửi các kịch bản rủi ro (`normal`, `critical`) lên CarSky REST Endpoint.
2. **Node 1 — DMS Signal Broker (KUKSA Databroker):** Nhận tín hiệu VSS và lưu trữ trong cây tín hiệu xe.
3. **Node 2 — DMS HMI Bridge (Script Node):** Subscribe tín hiệu KUKSA, mã hóa (Encoding) và gọi `pins.vhal:push()` đẩy sang Android VHAL.
4. **Node 3 — DMS Android HMI (Skycraft AAOS APK):** Đọc giá trị VHAL Property và thay đổi màu sắc/cảnh báo trên giao diện Android Automotive OS.

---

## 2. PHÂN TÍCH NGUYÊN NHÂN SỰ CỐ HIỆN TẠI (ROOT CAUSE ANALYSIS)

Dựa trên đối chiếu trực tiếp với tài liệu hướng dẫn chính thức của CarSky (**`carsky-guideline-web 5/index.html`**), nguyên nhân APK kẹt ở giá trị `0.0` đã được làm rõ:

### Sự cố 1: Custom Vendor Property bị OS chặn
- **Nguyên nhân:** 8 Custom Vendor DMS Properties (như `559940608`) chưa được Android AAOS `CarPropertyService` đăng ký HAL manifest nên bị OS chặn không cho APK truy cập.

### Sự cố 2: VHAL Speed Property bị Android Emulator ghi đè
- **Nguyên nhân:** Khi dùng cơ chế Multiplex đẩy dữ liệu qua property chuẩn `PERF_VEHICLE_SPEED` (`0x11600207`), dịch vụ mô phỏng xe mặc định của Android AAOS liên tục phát đè giá trị `0.0` mỗi 100ms.

---

## 3. HƯỚNG DẪN CHI TIẾT TỪNG BƯỚC THỰC HIỆN FIX LỖI (STEP-BY-STEP GUIDE)

### BƯỚC 1: Cập nhật Script Content chuẩn cho `DMS HMI Bridge` Node

1. Mở file [dms_hmi_bridge.lua](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/carsky/dms_hmi_bridge.lua).
2. Copy toàn bộ đoạn mã Lua đã chuẩn hóa cú pháp VHAL Push (3 tham số: `property_id`, `area_id = 0`, `encoded_value`):

```lua
-- DMS KUKSA -> AAOS HMI Bridge Script Node (dms_hmi_bridge.lua)
local PROP_SPEED = 291504647 -- 0x11600207 (PERF_VEHICLE_SPEED)

local severity_code = { SAFE = 0, WARNING = 1, CRITICAL = 2, RECOVERY = 3 }
local driver_code = { alert = 0, drowsy = 1, yawning = 2, distracted = 3, microsleep = 4 }
local ai_code = { ONLINE = 0, DEGRADED = 1, OFFLINE = 2 }
local action_code = { NONE = 0, FOCUS_FORWARD = 1, TAKE_BREAK = 2, BRAKE_SAFE = 3, REDUCE_SPEED = 4 }

local mapping = {
    ["Vehicle.Speed"] = { encode = function(v) return tonumber(v) or 0 end },
    ["Vehicle.ADAS.FinalRiskScore"] = { encode = function(v) return 41.000 + ((tonumber(v) or 0) / 1000) end },
    ["Vehicle.ADAS.DisplaySeverity"] = { encode = function(v) return 42.000 + ((severity_code[v] or 0) / 1000) end },
    ["Vehicle.Driver.State"] = { encode = function(v) return 43.000 + ((driver_code[v] or 0) / 1000) end },
    ["Vehicle.Driver.AlertnessScore"] = { encode = function(v) return 44.000 + (((tonumber(v) or 0) * 100) / 1000) end },
    ["Vehicle.ADAS.MinTTC"] = { encode = function(v) return 45.000 + (((tonumber(v) or 0) * 10) / 1000) end },
    ["Vehicle.ADAS.CriticalAlert"] = { encode = function(v) return 46.000 + (((v == true or v == 1 or v == "true") and 1 or 0) / 1000) end },
    ["Vehicle.ADAS.AIStatus"] = { encode = function(v) return 47.000 + ((ai_code[v] or 2) / 1000) end },
    ["Vehicle.ADAS.RecommendedActionCode"] = { encode = function(v) return 48.000 + ((action_code[v] or 0) / 1000) end },
}

local paths = {}
for path, _ in pairs(mapping) do paths[#paths + 1] = path end

pins.kuksa:on_change(function(ev)
    local target = mapping[ev.path]
    if not target or ev.value == nil then return end
    local encoded = target.encode(ev.value)
    
    -- CÚ PHÁP CHUẨN CỦA CARSKY GUIDELINE (3 tham số):
    pins.vhal:push(PROP_SPEED, 0, encoded)
    log(string.format("DMS_HMI_MUX %s=%s -> %s on 0x%08X", ev.path, tostring(ev.value), tostring(encoded), PROP_SPEED))
end)

pins.kuksa:subscribe(paths)
log(string.format("DMS HMI multiplex bridge subscribed to %d paths", #paths))
```

3. Dán đoạn mã trên vào phần **Script Content** của node `DMS HMI Bridge` trên giao diện CarSky Workbench và nhấn **Save**.

---

### BƯỚC 2: Phát dữ liệu Scenario từ Backend / Laptop

Mở Terminal tại thư mục `HACKATHON` và gửi kịch bản rủi ro nguy cấp để đẩy dữ liệu lên KUKSA Broker:

```bash
cd SE/BE
source .venv/bin/activate

# Gửi kịch bản An toàn (SAFE)
python scripts/carsky_phase05.py scenario normal

# Gửi kịch bản Nguy cấp (CRITICAL)
python scripts/carsky_phase05.py scenario critical
```

---

### BƯỚC 3: Kiểm tra Logs trên CarSky Workbench

1. Nhấp vào node **`DMS HMI Bridge`** $\rightarrow$ chọn **View Logs**.
2. Kiểm tra log xuất hiện đúng định dạng:
   ```text
   DMS HMI multiplex bridge subscribed to 9 paths
   DMS_HMI_MUX Vehicle.Driver.State=microsleep -> 43.004 on 0x11600207
   DMS_HMI_MUX Vehicle.ADAS.FinalRiskScore=88 -> 41.088 on 0x11600207
   ```
   *Nếu log hiển thị như trên nghĩa là luồng từ REST API $\rightarrow$ KUKSA $\rightarrow$ Bridge đã HOÀN THÀNH 100%.*

---

### BƯỚC 4: Gửi Mẫu Tin Nhắn Đề Nghị BTC CarSky Hỗ Trợ (Bypass Lỗi Emulator 0.0)

Nếu APK trên Android VM vẫn chỉ hiển thị `0.0`, hãy gửi tin nhắn dưới đây cho BTC CarSky để nhờ hỗ trợ cấu hình Android VM:

> **Kính gửi BTC CarSky Support,**  
> Deployment 3 Nodes của team DMS (`DMS Signal Broker` $\rightarrow$ `DMS HMI Bridge` $\rightarrow$ `DMS Android HMI`) đã chạy trạng thái `Running 3/3 ready`. 
> 
> Script Node Bridge đã subscribe KUKSA thành công và log `DMS_HMI_MUX` gọi `pins.vhal:push(291504647, 0, encoded)` liên tục khi gửi API. Tuy nhiên Android AAOS VM trên Skycraft vẫn bị dịch vụ emulator mô phỏng tốc độ mặc định phát đè giá trị `0.0` làm APK không đọc được dữ liệu VHAL push.
> 
> Nhờ BTC hỗ trợ tắt service mô phỏng tốc độ mặc định của AAOS hoặc hướng dẫn cách cấu hình Custom Vendor VHAL Properties cho APK. Team có đầy đủ log sẵn sàng hỗ trợ BTC. Em xin cảm ơn!

---
*Tài liệu hướng dẫn vận hành 3-Node Topology được cập nhật chuẩn theo CarSky Guideline Web 5.*
