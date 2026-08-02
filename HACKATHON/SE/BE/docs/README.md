# Backend Documentation — Nhân

Tài liệu này là điểm bắt đầu cho phần Backend của dự án **AI Fleet Management & Driver Intelligence Platform**.

## Người phụ trách

- **Nhân — Backend Lead Engineer**
- Phạm vi: FastAPI core, bảo toàn và phân phối output AI, data aggregation, fleet APIs, WebSocket replay, AI Copilot gateway, CarSky adapter và submission exporter. Backend không tính lại hoặc ghi đè risk do AI cung cấp.

## Trạng thái sau khi rà soát

| Hạng mục | Hiện trạng | Ưu tiên |
|---|---|---|
| FastAPI bootstrap | Phase 01 đã implement; chạy Python 3.11, automated tests pass | Hoàn thành |
| Dataset adapter | Đã có, còn hard-code path và fallback sai trip | P0 |
| AI output/risk | Canonical Pydantic contract đã có; Phase 02 còn phải chuyển adapter/pipeline legacy sang contract mới | P0 |
| External AI API | Chưa có AI Gateway/client, authentication, timeout hoặc fallback mode | P0 |
| Fleet REST API | Có summary/trajectory, chưa đúng contract SRS | P0 |
| WebSocket replay | Có loop 20 FPS, cần sửa seek/timing/error handling | P0 |
| Copilot | Hiện luôn dùng fallback, chưa xử lý câu hỏi fleet | P1 |
| CarSky | Mapper/client/queue, VSS, bridge và Android APK đã có; Blueprint valid, deployment còn vướng visibility của VSS artifact | P0 |
| Submission | Có exporter/validator, cần tăng validation | P0 |
| Automated tests | 23 Backend tests pass; runtime CarSky/Android chưa nghiệm thu | P0 |

## Tài liệu

- [AI contract, compatibility và change memory](AI_CONTRACT_AND_CHANGELOG.md)
- [CarSky deployment self-check — kiểm tra không sửa tài nguyên](CARSKY_DEPLOYMENT_SELF_CHECK.md)
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

### Nhận cảnh báo live từ AI Decision Engine

Backend nhận canonical event tại:

```text
POST /api/v1/alerts
Idempotency-Key: <giống idempotency_key trong payload>
```

Response `202` xác nhận đã nhận. Retry cùng key trả `duplicate=true` và không
tạo cảnh báo thứ hai. Endpoint demo để Dashboard/SE kiểm tra dữ liệu gần nhất:

```text
GET /api/v1/alerts/recent?limit=100
WS  /api/v1/alerts/live
```

Store hiện tại là RAM tối đa 1.000 event, phù hợp demo local. SE cần thay bằng
database/outbox trước production nhưng phải giữ nguyên schema, event lifecycle
và idempotency do AI phát. Dashboard kết nối WebSocket `alerts/live`; Backend
broadcast nguyên canonical event mới nhận và không broadcast duplicate.

Event được xử lý theo đúng hai audience do AI cung cấp:

- `fleet_dashboard`: broadcast canonical payload qua `/api/v1/alerts/live`;
- `driver_display`: map sang VSS và enqueue bất đồng bộ tới CarSky nếu integration
  external đã bật.

Mapper chỉ dịch field/vocabulary (`open → START`, `resolved → END`, alert type →
action code), không tính lại `severity` hoặc risk của AI. Runbook tích hợp chính:
[`../../../reportbtc/C2_END_TO_END_DEMO_SCRIPT.md`](../../../reportbtc/C2_END_TO_END_DEMO_SCRIPT.md).

Sau khi khởi động:

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- WebSocket: `ws://localhost:8000/ws/replay/T01d`

Backend có hai nguồn AI được chọn bằng `AI_SOURCE_MODE`:

- `file`: đọc output AI đã có trong dataset, dùng cho demo ổn định.
- `external_api`: gọi AI service bên ngoài qua AI Gateway, sau đó validate/cache output trước khi replay.
