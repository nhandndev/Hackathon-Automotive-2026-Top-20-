# Backend Documentation — Nhân

Tài liệu này là điểm bắt đầu cho phần Backend của dự án **AI Fleet Management & Driver Intelligence Platform**.

## Người phụ trách

- **Nhân — Backend Lead Engineer**
- Phạm vi: FastAPI core, bảo toàn và phân phối output AI, data aggregation, fleet APIs, WebSocket replay, AI Copilot gateway, CarSky adapter và submission exporter. Backend không tính lại hoặc ghi đè risk do AI cung cấp.

## Trạng thái sau khi rà soát

| Hạng mục | Hiện trạng | Ưu tiên |
|---|---|---|
| FastAPI bootstrap | Phase 01 đã implement; chạy Python 3.11, 19 automated tests pass | Hoàn thành |
| Dataset adapter | Đã có, còn hard-code path và fallback sai trip | P0 |
| AI output/risk | Canonical Pydantic contract đã có; Phase 02 còn phải chuyển adapter/pipeline legacy sang contract mới | P0 |
| External AI API | Chưa có AI Gateway/client, authentication, timeout hoặc fallback mode | P0 |
| Fleet REST API | Có summary/trajectory, chưa đúng contract SRS | P0 |
| WebSocket replay | Có loop 20 FPS, cần sửa seek/timing/error handling | P0 |
| Copilot | Hiện luôn dùng fallback, chưa xử lý câu hỏi fleet | P1 |
| CarSky | Tài liệu nói đã xong nhưng code chưa tồn tại | P1 |
| Submission | Có exporter/validator, cần tăng validation | P0 |
| Automated tests | Có 19 test cho Phase 01; các phase sau chưa đủ test | P0 |

## Tài liệu

- [Phase 01 — Bootstrap và contract](phases/PHASE_01_BOOTSTRAP_AND_CONTRACT.md)
- [Phase 02 — AI output ingestion và aggregation](phases/PHASE_02_DATA_AND_RISK_ENGINE.md)
- [Phase 03 — REST API và fleet](phases/PHASE_03_REST_API_AND_FLEET.md)
- [Phase 04 — WebSocket replay](phases/PHASE_04_WEBSOCKET_REPLAY.md)
- [Phase 05 — Copilot và CarSky](phases/PHASE_05_COPILOT_AND_CARSKY.md)
- [Phase 05.1 — Runbook đưa cảnh báo lên CarSky HMI](phases/PHASE_05_1_CARSKY_HMI_RUNBOOK.md)
- [Phase 05.2 — Checklist thao tác CarSky HMI từ đầu đến cuối](phases/PHASE_05_2_CARSKY_HMI_ACTION_CHECKLIST.md)
- [Phase 06 — Test, submission và demo](phases/PHASE_06_TEST_SUBMISSION_DEMO.md)

## Luồng triển khai

Thực hiện theo thứ tự Phase 01 → 06. Không đánh dấu phase hoàn thành chỉ vì code đã tồn tại; chỉ hoàn thành khi toàn bộ Definition of Done của phase đạt.

## Lệnh chạy mục tiêu

```bash
cd SE/BE
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Sau khi khởi động:

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- WebSocket: `ws://localhost:8000/ws/replay/T01d`

Backend có hai nguồn AI được chọn bằng `AI_SOURCE_MODE`:

- `file`: đọc output AI đã có trong dataset, dùng cho demo ổn định.
- `external_api`: gọi AI service bên ngoài qua AI Gateway, sau đó validate/cache output trước khi replay.
