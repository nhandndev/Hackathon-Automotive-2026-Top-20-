# FPTU DMS Vision — Fleet Dashboard

Frontend Vite/React dành cho Fleet Manager. Màn **Live Cam** không dùng ảnh hay
số liệu mô phỏng:

- Road Cam nhận frame BTC đã được AI vẽ kết quả Challenge 1.
- Cabin Cam nhận frame webcam đã được AI vẽ kết quả Challenge 2.
- Risk Score, tốc độ, TTC, trạng thái và alertness nhận từ snapshot cùng frame.
- Event Log nhận canonical `DecisionEvent` từ Backend qua WebSocket.

Khi AI hoặc Backend chưa chạy, giao diện hiển thị `OFFLINE`/`WAITING`; không thay
bằng dữ liệu giả. Các màn lịch sử đọc JSON trip do BTC cung cấp và ghi rõ
`ORGANIZER DATA`.

## Setup

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\FE
npm install
Copy-Item .env.example .env.local
npm run dev
```

Backend mặc định chạy tại `http://127.0.0.1:8000`. Các endpoint có thể đổi trong
`.env.local`:

```dotenv
VITE_ALERTS_WS_URL=ws://127.0.0.1:8000/api/v1/alerts/live
VITE_ROAD_FRAME_URL=http://127.0.0.1:8000/api/v1/alerts/road-frame
VITE_CABIN_FRAME_URL=http://127.0.0.1:8000/api/v1/alerts/cabin-frame
VITE_LIVE_SNAPSHOT_URL=http://127.0.0.1:8000/api/v1/alerts/snapshot
```

## Kiểm tra

```powershell
npm run lint
npm run build
```

Runbook toàn sản phẩm: [`../../reportbtc/C2_END_TO_END_DEMO_SCRIPT.md`](../../reportbtc/C2_END_TO_END_DEMO_SCRIPT.md).
