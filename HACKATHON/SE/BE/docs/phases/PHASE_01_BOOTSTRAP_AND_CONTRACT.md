# Phase 01 — Bootstrap, Configuration và API Contract

## Mục tiêu

Đưa Backend về trạng thái khởi động được trên máy bất kỳ, kiểm tra được health/readiness và khóa schema dùng chung trước khi phát triển nghiệp vụ.

## Quyết định đã khóa

- Runtime chuẩn: **Python 3.11**.
- Framework: FastAPI + Pydantic v2 + `pydantic-settings`.
- Test stack: `pytest`, `pytest-asyncio`, `httpx` và FastAPI `TestClient`/WebSocket client.
- API prefix chính thức: `/api/v1`; endpoint cũ chỉ là alias deprecated.
- Cấu hình đọc từ environment/`.env`; không có secret hoặc absolute user path trong source.
- Cache MVP là in-memory, được tạo trong FastAPI lifespan và chỉ đọc sau startup.
- `file` là source mode mặc định để demo chạy độc lập; `external_api` chỉ ready khi đủ cấu hình.

## Hiện trạng

- `app/modules/coaching/router.py` import `BaseModel` từ FastAPI nên app không import được.
- `DATASET_DIR` và `OUTPUT_SUBMISSION_DIR` đang gắn với đường dẫn máy cá nhân.
- CORS vừa liệt kê origin vừa có `*`, không phù hợp khi bật credentials.
- Router chưa dùng prefix/version thống nhất.
- Service để `FileNotFoundError` đi lên thành HTTP 500.
- Chưa có `.env.example`, readiness check và response schema chung.

## Công việc

### 1. Bootstrap

- [ ] Sửa toàn bộ import Pydantic model.
- [ ] Bổ sung `__init__.py` cho `app` và mọi Python package directory để import/test nhất quán.
- [ ] Kiểm tra versions trong `requirements.txt` tương thích Python mục tiêu.
- [ ] Chạy import smoke test trước khi mở server.

### 2. Configuration

- [ ] Chuyển Settings sang `pydantic-settings`.
- [ ] Hỗ trợ `DATASET_DIR`, `OUTPUT_SUBMISSION_DIR`, `CORS_ORIGINS`, `STREAM_FPS`, AI API, LLM và CarSky qua environment.
- [ ] Thêm `AI_SOURCE_MODE=file|external_api`, `AI_API_BASE_URL`, `AI_API_KEY`, `AI_API_TIMEOUT_SEC`, `AI_API_MAX_RETRIES` và `AI_API_CONCURRENCY`.
- [ ] Tạo `.env.example` không chứa secret.
- [ ] Không dùng fallback là đường dẫn tuyệt đối trên máy Nhân.
- [ ] Parse CORS từ danh sách phân tách dấu phẩy; mặc định chỉ cho `http://localhost:5173` và `http://127.0.0.1:5173`, bật credentials, không dùng wildcard.

Giá trị mặc định trong `.env.example`:

```env
APP_ENV=development
API_V1_PREFIX=/api/v1
DATASET_DIR=./data
OUTPUT_SUBMISSION_DIR=./submissions
STREAM_FPS=20
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
AI_SOURCE_MODE=file
AI_API_BASE_URL=
AI_API_PATH=/v1/analyze/trip
AI_API_KEY=
AI_API_TIMEOUT_SEC=30
AI_API_MAX_RETRIES=2
AI_API_CONCURRENCY=4
AI_FALLBACK_TO_FILE=true
LLM_PROVIDER=none
CARSKY_ENABLED=false
CARSKY_MODE=offline
```

### 3. Health và lifecycle

- [ ] `GET /health` trả process status, version và FPS.
- [ ] `GET /ready` kiểm tra dataset directory, đủ 10 trip và trạng thái pre-ingest cache.
- [ ] Dùng FastAPI lifespan thay cho side effect không kiểm soát khi import.
- [ ] Log startup, thời gian ingest và lỗi cấu hình với context.

### 4. Schema và error contract

- [ ] Tạo Pydantic schemas khớp output AI: `TripMetadata`, `Ego`, `Geolocation`, `Driver`, `BehaviorFlags`, `AIRisk`, `AIFrame`, `AITrip`.
- [ ] `AIFrame` phải giữ đúng các key `ego`, `driver`, `min_ttc`, `headway_sec`, `behavior_flags`, `risk`; không đổi sang `telemetry/ai_vision` ở public contract.
- [ ] Tạo response schemas cho health, leaderboard, compare, events, coaching và replay envelope.
- [ ] Dùng `Field` để khóa range: score 0–100, alertness 0–1, speed không âm.
- [ ] Dùng `default_factory=list` thay cho mutable default list.
- [ ] Chuẩn hóa driver-state enum; serialize `Infinity` thành chuỗi `"Infinity"` tại JSON boundary và deserialize về infinity nội bộ khi cần so sánh.
- [ ] Cho phép giữ các AI field bổ sung như `targets`, `events_active`, `world_frame` mà không làm mất dữ liệu.
- [ ] Tách `backend_enrichment` khỏi frame AI trong response schema.
- [ ] Tạo error payload `{code, message, details?, request_id?}`.
- [ ] Map trip không tồn tại → 404; query/body sai → 422; dataset lỗi → 503.

Required fields của contract v1:

```text
AITrip: trip_id, metadata, frames
TripMetadata: trip_id, description, duration_sec, fps, map,
              driver_profile, carla_version, random_seed, speed_limit_kmh
AIFrame: frame_id, timestamp, ego, driver, min_ttc, headway_sec,
         behavior_flags, risk
Ego: speed_kmh, longitudinal_accel, lateral_accel, geolocation
Geolocation: lat, lon, alt
Driver: state, alertness_score, eye_state, head_pose, mouth_state,
        nthu_subject_id
BehaviorFlags: harsh_brake, harsh_accel, harsh_corner, speeding, tailgating
AIRisk: base_risk, driver_factor, final_risk_score
```

`world_frame`, `targets`, `events_active`, `location` và `rotation` là optional extra fields nhưng phải được round-trip giữ nguyên. Driver enum v1: `alert|drowsy|yawning|distracted|microsleep`; unknown enum làm frame invalid, không tự đổi thành `alert`.

Error payload chính thức:

```json
{"code":"TRIP_NOT_FOUND","message":"Trip T99d was not found","details":{"trip_id":"T99d"},"request_id":"..."}
```

## Public interface

```json
GET /health
{"status":"ok","service":"dms-backend","version":"1.0.0","stream_fps":20}
```

```json
GET /ready
{"status":"ready","dataset_ready":true,"cached_trips":10}
```

## File dự kiến ảnh hưởng

- `app/main.py`, `app/core/config.py`
- `app/domain/schemas/*`
- `app/modules/coaching/router.py`
- `.env.example`, `requirements.txt`
- `tests/conftest.py`, `tests/test_health.py`, `tests/test_contract.py`

## Kiểm thử

- Import `app.main:app` không phát sinh exception.
- Health luôn trả 200 khi process chạy.
- Ready trả 503 nếu dataset thiếu và 200 khi đủ 10 trip.
- Environment override thay đổi dataset path/FPS đúng.
- Thiếu AI credential trong `external_api` mode làm readiness fail rõ ràng; `file` mode không yêu cầu credential.
- Invalid score/state bị Pydantic từ chối.
- Round-trip test chứng minh một AI payload parse rồi serialize không mất hoặc đổi giá trị nguồn.
- Trip không tồn tại trả error schema và HTTP 404.

## Definition of Done

- [ ] Server khởi động bằng lệnh trong README.
- [ ] Swagger hiển thị schema và endpoint chính xác.
- [ ] Không còn đường dẫn máy cá nhân làm default bắt buộc.
- [ ] Health/readiness và error handling có automated tests.
- [ ] Frontend và AI có một contract Pydantic thống nhất để tích hợp.
