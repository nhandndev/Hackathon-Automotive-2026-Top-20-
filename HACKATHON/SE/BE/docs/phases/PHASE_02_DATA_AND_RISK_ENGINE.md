# Phase 02 — External AI Gateway, Output Ingestion và Aggregation

## Mục tiêu

Tích hợp API AI bên ngoài, nhận output theo schema AI chính thức, bảo toàn dữ liệu nguyên gốc, tạo aggregate/episode cần cho Backend và cache kết quả để API/WebSocket không phụ thuộc trực tiếp vào độ trễ mạng.

## Hiện trạng

- Adapter hỗ trợ CSV/JSON nhưng dùng `T01-Sample.json` làm fallback cho mọi trip; điều này có thể khiến T02–T10 dùng nhầm dữ liệu.
- Adapter hiện chuyển `ego/driver/min_ttc/risk` sang schema rút gọn `telemetry/ai_vision`, làm mất metadata và nhiều trường AI.
- Backend đang chạy detector và NHTSA model để tính lại risk dù AI đã trả `behavior_flags` và `risk.final_risk_score`.
- Event aggregate hiện có nguy cơ đếm từng frame thay vì gom episode.
- Code tính safe score theo average/critical penalty thay vì aggregate trực tiếp từ AI risk.
- Chưa có HTTP client/gateway để gọi AI API bên ngoài.

## Kiến trúc nguồn AI

```text
AI_SOURCE_MODE=file
Dataset JSON ──> AITrip validator ──> Cache ──> REST/WebSocket

AI_SOURCE_MODE=external_api
Input trip/frame ──> AI Gateway ──> External AI API ──> AITrip validator ──> Cache ──> REST/WebSocket
```

`file` là chế độ fallback/demo ổn định. `external_api` là chế độ tích hợp thật. Cả hai phải tạo cùng một `AITrip` domain model để phần còn lại của Backend không cần biết nguồn dữ liệu.

## Contract External AI v1

Để Agent có thể triển khai provider ngay, Backend khóa wire contract phía mình như sau. AI service thật phải đáp ứng contract này hoặc chỉ cần thay riêng request/response mapper trong `ExternalAIProvider`.

```http
POST {AI_API_BASE_URL}{AI_API_PATH}
Authorization: Bearer {AI_API_KEY}
Content-Type: application/json
Idempotency-Key: {trip_id}-{content_sha256}
```

Request mặc định là source trip JSON chưa có kết quả fusion:

```json
{"trip_id":"T01d","metadata":{},"frames":[]}
```

Response thành công phải là một `AITrip` hoàn chỉnh theo Phase 01. Không chấp nhận response tự bọc bằng key khác. Nếu API thật dùng multipart/job polling/schema khác, chỉ adapter mapper thay đổi; domain/cache/REST/WebSocket giữ nguyên.

Runtime policy:

- `file`: load trực tiếp AITrip hoàn chỉnh.
- `external_api`: pre-ingest từng trip bằng `POST`; không gọi lại nếu content hash đã có trong cache.
- Connect timeout 2 giây; read timeout 30 giây/trip; tối đa 2 retry với backoff 250 ms và 500 ms.
- Retry network error, timeout, 429 và 5xx; tôn trọng `Retry-After` nhưng tối đa 2 giây trong demo.
- Không retry 400/401/403/404/409/422.
- Concurrency tối đa 4 trip; breaker mở sau 3 failure liên tiếp trong 30 giây.
- Fallback sang file chỉ khi có file đúng cùng `trip_id`; tuyệt đối không dùng trip khác.

## Công việc

### 1. External AI Gateway

- [ ] Tạo interface `BaseAIProvider.analyze_trip(source_trip) -> AITrip`; per-frame live provider không thuộc MVP v1.
- [ ] Tạo `FileAIProvider` đọc output có sẵn và `ExternalAIProvider` gọi HTTP API.
- [ ] Dùng async HTTP client dùng chung connection pool; không tạo client mới cho mỗi frame.
- [ ] Gửi API key qua header cấu hình, không hard-code hoặc log secret.
- [ ] Đặt connect/read timeout, concurrency semaphore và retry exponential backoff có giới hạn.
- [ ] Chỉ retry network error, timeout và 5xx; không retry vô hạn với 4xx/schema error.
- [ ] Validate response qua `AITrip`/`AIFrame` trước khi ghi cache.
- [ ] Gắn metadata nội bộ `source`, `received_at`, `latency_ms`, `request_id`; không trộn vào frame AI.
- [ ] Circuit breaker mở sau 3 lỗi liên tiếp/30 giây; nếu `AI_FALLBACK_TO_FILE=true` thì dùng file đúng trip, nếu false hoặc file thiếu thì trip ingest thất bại và readiness degraded.
- [ ] Implement wire contract v1 ở trên; cô lập request/response mapper để thay khi AI team cung cấp contract khác.

### 2. Chính sách gọi API AI

- [ ] Ưu tiên API xử lý cả trip hoặc batch frame để giảm số request.
- [ ] Pre-ingest external output trước khi bắt đầu replay nếu đây là dữ liệu recorded demo.
- [ ] Nếu AI chỉ hỗ trợ per-frame live inference, dùng async queue/workers và cache theo `(trip_id, frame_id)`.
- [ ] WebSocket sender đọc kết quả đã sẵn sàng; không chờ một HTTP call AI trong vòng lặp 50 ms.
- [ ] Recorded demo chỉ cho replay sau khi trip ingest hoàn tất. Live mode gửi `ai_pending` tối đa 3 giây; quá hạn đóng stream với `AI_RESULT_TIMEOUT`, không tự tạo risk giả.

### 3. Dataset discovery và validation

- [ ] Chỉ chấp nhận whitelist `T01d`–`T10d` cho fleet demo.
- [ ] Resolve file theo đúng trip; không fallback sang trip khác.
- [ ] Kiểm tra `total_frames`, frame ID liên tục và timestamp đơn điệu.
- [ ] Đọc và giữ nguyên `metadata`, `ego`, `driver`, `min_ttc`, `headway_sec`, `behavior_flags`, `risk`.
- [ ] Chuẩn hóa `Infinity` chỉ ở serialization boundary; tuyệt đối không đổi thành 0 hoặc risk giả.
- [ ] Không tự điền telemetry/risk giả cho required field bị thiếu; đánh dấu trip/frame invalid.
- [ ] Phân biệt required field với optional/extra field và không loại bỏ field AI bổ sung.
- [ ] Kiểm tra URL ảnh road/driver theo frame và hỗ trợ trạng thái ảnh thiếu.

### 4. Aggregation pipeline

- [ ] Dùng trực tiếp `driver.state` và các cờ trong `behavior_flags` làm nguồn event.
- [ ] Không gọi temporal filter để thay đổi state/cờ AI. Aggregator chỉ tạo episode và `display_severity` trong `backend_enrichment`.
- [ ] Gom trạng thái/cờ liên tục thành episode với `start_frame`, `end_frame`, `duration_sec`, `peak_value`, `severity`.
- [ ] Nếu có `events_active` từ AI thì bảo toàn và đưa vào aggregate, không tái tạo ID của AI.

Critical/display rules v1:

```text
CRITICAL nếu final_risk_score >= 75
         hoặc min_ttc hữu hạn <= 1.5
         hoặc driver.state == microsleep

WARNING nếu không CRITICAL và:
        final_risk_score >= 45
        hoặc min_ttc hữu hạn <= 2.5
        hoặc driver.state thuộc {drowsy, distracted}

SAFE cho các trường hợp còn lại.
```

- Episode được tạo riêng theo loại: mỗi driver state bất thường và mỗi behavior flag là một loại episode.
- Episode bắt đầu ở frame đầu tiên điều kiện true, kết thúc sau **10 frame liên tiếp** điều kiện false.
- Khoảng 10 frame an toàn là hysteresis; các frame này không tính vào `end_frame`, `end_frame` là frame true cuối cùng.
- Overall display severity của frame là mức cao nhất theo rules trên; đây là enrichment, không sửa AI risk.

### 5. Risk ownership và Backend enrichment

- [ ] Dùng nguyên gốc `risk.base_risk`, `risk.driver_factor`, `risk.final_risk_score` do AI trả.
- [ ] Giữ file NHTSA legacy để tham chiếu nhưng không import/gọi từ provider, aggregation, REST, WebSocket hoặc exporter v1.
- [ ] Không clamp/sửa giá trị AI âm thầm; dữ liệu ngoài range phải tạo validation error.
- [ ] Tính trip safe score dẫn xuất: `100 - max(risk.final_risk_score)`.
- [ ] Sinh `display_severity` và reasoning trong `backend_enrichment`, dựa trên evidence AI nhưng không sửa frame nguồn.

### 6. Pre-ingestion cache

- [ ] Khi startup, xử lý 10 trip một lần.
- [ ] Cache frames đã normalize, risk summary, episodes, trajectory, metrics và leaderboard input.
- [ ] Cache chỉ đọc trong MVP; có hàm reload chủ động cho development.
- [ ] Nếu một trip lỗi, readiness báo degraded và liệt kê trip lỗi.

## Data output chính

```json
{
  "trip_id": "T01d",
  "risk_source": "ai",
  "total_frames": 1800,
  "max_risk_score": 100.0,
  "safe_score": 0.0,
  "event_episode_count": 3,
  "status": "CRITICAL"
}
```

## File dự kiến ảnh hưởng

- `app/adapters/csv_file_adapter.py`
- `app/domain/interfaces/base_ai_provider.py`
- `app/adapters/external_ai_provider.py` và `file_ai_provider.py`
- `app/modules/event_detection/*` (chuyển thành aggregation từ AI flags/state)
- `app/modules/risk_fusion/*` (router/service chuyển sang aggregate AI; thuật toán NHTSA legacy không được gọi)
- Một cache/pre-ingestion service mới trong `app/modules/fleet/` hoặc `app/core/`

## Kiểm thử

- Mỗi trip load đúng file và đúng 1.800 frame.
- External provider gửi đúng auth/request và parse đúng AI response qua mock HTTP server.
- Timeout/5xx được retry giới hạn; 401/422 không retry.
- Hai source mode tạo cùng một normalized `AITrip`.
- WebSocket test xác nhận không gọi external HTTP trong vòng lặp gửi từng frame đã pre-ingest.
- Trip bị thiếu không dùng T01 làm fallback.
- AI payload parse/serialize round-trip không mất metadata hoặc field frame.
- TTC/headway `Infinity` được JSON hóa đúng mà không biến thành 0.
- Backend giữ nguyên state AI; chuỗi `microsleep` ngắn hay dài đều không bị sửa. Aggregator chỉ gom theo episode/hysteresis 10 frame.
- Event episode không đếm lặp từng frame.
- Safe score bằng chính xác `100 - max(risk.final_risk_score)`.
- Cache có đủ 10 trip và dữ liệu API không thay đổi giữa hai lần đọc.

## Definition of Done

- [ ] 10 trip ingest thành công hoặc readiness chỉ rõ trip hỏng.
- [ ] External AI API được cô lập sau provider interface và có integration tests mock.
- [ ] Replay không bị khóa bởi latency của external AI API.
- [ ] Không có NaN/risk ngoài range trong normalized output.
- [ ] AI risk được bảo toàn và aggregate/event rules có unit tests tại các boundary.
- [ ] Leaderboard và các trip API đọc từ cache.
- [ ] Công thức trong code, docs và CSV exporter hoàn toàn nhất quán.
