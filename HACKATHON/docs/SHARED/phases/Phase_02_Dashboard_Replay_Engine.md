# PHASE 2: MASTER FLEET DASHBOARD & 20 FPS REPLAY ENGINE (XÂY DỰNG GIAO DIỆN & ENGINE)

---

## 1. MỤC TIÊU VÀ BÀI TOÁN GIAO THỰC CỦA PHASE 2

### 1.1 Mục tiêu của Phase 2 (Cho User & AI)
- **Cho User (Fleet Manager)**: Đánh giá chi tiết giao diện 3 màn hình chuyên biệt (Driver HUD, Fleet View, Business Report), trải nghiệm tua lại sự cố 20 FPS mượt mà và trực quan hóa bản đồ trajectory GPS thời gian thực.
- **Cho AI (Coding Assistant / Developer)**: Cung cấp đầy đủ kiến trúc WebSocket Stream Server 20 FPS (FastAPI), React Replay Engine Context Clock và mã nguồn Leaflet GPS Map Tracker để triển khai code không bị vỡ nhịp timing.

### 1.2 Bài toán thực tế Phase 2 giải quyết
Quản lý đội xe không thể ngồi xem hàng ngàn giờ video thô. Phase 2 giải quyết bằng cách **tua đồng bộ 20 FPS (50ms/frame)**: Khi tua video cabin, toàn bộ đồng hồ tốc độ, vị trí xe trên bản đồ GPS, biểu đồ va chạm TTC và cờ vi phạm sẽ **chạy mượt tự động cùng một thời điểm**.

---

## 2. CHI TIẾT GIAO DIỆN 3 MÀN HÌNH CHUYÊN BIỆT (3 VIEWS SPECIFICATION)

### 2.1 View 1: Driver HUD View (NHTSA 2s Glance Rule)
- **Mục đích**: Tối ưu cho góc nhìn lái xe cabin (không gây xao nhãng quá 2 giây).
- **Các Widget UI**:
  1. **Speedometer & G-Force Meter**: Đồng hồ kim/số hiển thị vận tốc ($km/h$) và gia tốc phanh ($m/s^2$).
  2. **TTC Assessment Gauge**: Đồng hồ thời gian va chạm. Nếu `min_ttc < 1.5s`, chuyển màu Đỏ rực.
  3. **Alertness Pill Score**: Thanh phần trăm tỉnh táo (0% - 100%).
  4. **Audio & Visual Alarm Synthesizer**: Tự động phát tiếng còi beep báo động 880Hz và nhấp nháy viền đỏ màn hình khi có nguy cơ tai nạn.

### 2.2 View 2: Fleet Manager View (Live Map & Leaderboard)
- **Mục đích**: Trung tâm điều hành giám sát toàn bộ đội xe thời gian thực.
- **Các Widget UI**:
  1. **GPS Trajectory Live Tracker**: Bản đồ Leaflet hiển thị vị trí xe, vệt di chuyển đường đi và tọa độ `lat`, `lon`.
  2. **Driver Safety Ranking (Leaderboard)**: Bảng xếp hạng 12 tài xế theo Safe Score (Top Safe vs. High Risk).
  3. **Violation Event Timeline**: Danh sách sự cố được đánh dấu theo khung giờ (Yawn, Drowsy, Microsleep, Harsh Brake).

### 2.3 View 3: Business & Insurance Report View
- **Mục đích**: Báo cáo tổng hợp dành cho C-Level / Đàm phán giảm chi phí bảo hiểm.
- **Các Widget UI**:
  1. **Donut Chart**: Biểu đồ phân bổ tỷ lệ thời gian trạng thái tài xế (Alert, Drowsy, Yawning, Microsleep).
  2. **SHAP Risk Contribution Matrix**: Biểu đồ phân tích nguyên nhân điểm phạt (45% do TTC va chạm, 35% do Vi ngủ).
  3. **Telemetry Comparison (Radar Chart)**: So sánh đa chiều 5 chỉ số an toàn giữa **Tài xế A vs Tài xế B**.

---

## 3. CHUẨN KỸ THUẬT ENGINE REPLAY 20 FPS (TEMPORAL REPLAY)

- **Tần số phát dữ liệu**: 20 FPS (tương đương 50ms cho mỗi frame telemetry).
- **Giao thức truyền**: WebSocket hai chiều (`/ws/replay/{trip_id}`).
- **Cơ chế Seek/Jump**: Khi người dùng kéo thanh tua timeline, Client gửi message `{"action": "seek", "frame_id": 450}`, Server lập tức chuyển con trỏ phát dữ liệu tới frame tương ứng.

---

## 4. CODE IMPLEMENTATION SPEC (DÀNH CHO AI / DEVELOPER)

### 4.1 Backend WebSocket Replay Server (`backend/app/modules/streaming/replay_server.py`)

```python
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/replay/{trip_id}")
async def replay_trip_websocket(websocket: WebSocket, trip_id: str):
    await websocket.accept()
    file_path = f"./{trip_id}.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            trip_data = json.load(f)
            frames = trip_data.get("telemetry_frames", trip_data.get("frames", []))
    except Exception as e:
        await websocket.send_json({"status": "error", "message": f"Dataset {trip_id} not found: {str(e)}"})
        await websocket.close()
        return

    fps = 20
    delay = 1.0 / fps  # 50ms
    current_idx = 0

    try:
        while current_idx < len(frames):
            frame = frames[current_idx]
            await websocket.send_json(frame)
            await asyncio.sleep(delay)
            current_idx += 1
    except WebSocketDisconnect:
        print(f"Client disconnected from trip stream {trip_id}")
```

### 4.2 Frontend Replay Context Engine (`frontend/src/core/ReplayContext.jsx`)

```jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const ReplayContext = createContext();

export const ReplayProvider = ({ children }) => {
  const [currentFrame, setCurrentFrame] = useState(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [activeView, setActiveView] = useState('driver'); // 'driver', 'fleet', 'business'

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/replay/T01d");
    
    ws.onmessage = (event) => {
      if (!isPlaying) return;
      const data = JSON.parse(event.data);
      setCurrentFrame(data);
    };

    return () => ws.close();
  }, [isPlaying]);

  return (
    <ReplayContext.Provider value={{ currentFrame, isPlaying, setIsPlaying, activeView, setActiveView }}>
      {children}
    </ReplayContext.Provider>
  );
};

export const useReplay = () => useContext(ReplayContext);
```

---

## 5. TIÊU CHÍ REVIEW & NGHIỆM THU PHASE 2 (CHECKLIST FOR USER)

- [ ] **Review Màn hình**: User trải nghiệm chuyển đổi mượt mà giữa 3 View (Driver HUD, Fleet Manager, Business Report).
- [ ] **Review Replay & Audio**: User kiểm tra khi xe gặp sự cố vi ngủ/phanh gấp, còi hiệu nhấp nháy đỏ bật lên chuẩn 20 FPS.
- [ ] **Nghiệm thu Code**: AI/Developer đảm bảo WebSocket Replay Server duy trì nhịp 50ms mà không bị lag hoặc đứt kết nối.
