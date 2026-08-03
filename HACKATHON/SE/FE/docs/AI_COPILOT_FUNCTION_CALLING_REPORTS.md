# AI Copilot Function Calling Reports — Fleet Dashboard

File này dùng làm memory cho AI/SE khi tiếp tục làm Fleet AI Copilot. Từ ngày 03/08/2026, Fleet Copilot đã chuyển sang gọi AI thật qua AWS Bedrock Bearer Token ở server-side. FE không được tự sinh thêm trip giả để demo; máy nào có full dataset thì phải dùng trip thật từ Backend/dataset của team.

## 1. Mục tiêu feature

Fleet AI Copilot trong Dashboard hỗ trợ:

- So sánh 2 hoặc nhiều tài xế/trip.
- Trả lời “xe/tài xế nào cần coaching hoặc bảo trì”.
- Tạo báo cáo an toàn đội xe.
- Khi report đã sẵn sàng, Copilot hiển thị card “Ấn vào đây để xem báo cáo chi tiết”.
- Khi bấm vào card, mở tab web mới với report chuyên nghiệp gồm KPI, event log, comparison table và AI Copilot Insight.

## 2. Quy tắc bắt buộc khi user yêu cầu so sánh tài xế

Nếu user nói “so sánh 2 tài xế”, “compare 3 drivers”, “so sánh n xe/tài xế” thì user phải cung cấp đủ `trip_id`.

Ví dụ hợp lệ:

```txt
So sánh 2 tài xế T01d và T02d
Compare 3 drivers T01d T02d T03d
```

Ví dụ thiếu thông tin:

```txt
So sánh 2 tài xế
```

Khi thiếu `trip_id`, AI Copilot phải hỏi lại:

```txt
Bạn muốn so sánh 2 tài xế/trip, nhưng hiện chưa có trip_id nào.
Bạn gửi thêm 2 trip_id còn thiếu nha.
Trip hiện có sẽ lấy từ dataset/backend đang chạy.
Ví dụ: "so sánh T01d và T02d".
```

Không được tự chọn bừa 2 trip đầu nếu user đang yêu cầu so sánh driver cụ thể.

## 3. Function calling / tool routing hiện tại

FE không tự mock report card nữa. UI gửi câu hỏi + trip context vào `POST /api/copilot`. Server-side `SE/FE/server.ts` validate `trip_id`, gọi AWS Bedrock Converse API, rồi trả `reply` hoặc `cardType/cardData` cho FE render.

Biến môi trường cần có:

```env
AWS_BEARER_TOKEN_BEDROCK=bedrock-api-key-...
AWS_DEFAULT_REGION=ap-southeast-2
BEDROCK_MODEL_ID=deepseek.v3.2
```

Phase sau nếu provider/model hỗ trợ native tool calling thì giữ nguyên các function contract dưới đây và chuyển routing trong `server.ts` sang native tool call.

### Function 1: `create_driver_comparison_report`

Input:

```json
{
  "trip_ids": ["T01d", "T02d"],
  "requested_count": 2
}
```

Quy tắc:

- Nếu `trip_ids.length < requested_count` thì không tạo report.
- AI phải hỏi lại trip nào còn thiếu.
- Khi đủ trip, tạo report route:

```txt
/?view=copilot-report&type=compare&trip_ids=T01d,T02d
```

### Function 2: `create_fleet_safety_report`

Input:

```json
{
  "trip_ids": ["T01d", "T02d", "T03d"],
  "date_range": {
    "from": "2026-08-03",
    "to": "2026-08-03"
  }
}
```

Dùng cho câu hỏi:

- “Báo cáo an toàn tuần này”
- “Safety report”
- “Tổng hợp rủi ro fleet”

### Function 3: `create_maintenance_priority_report`

Input:

```json
{
  "trip_ids": ["T01d", "T02d", "T03d"],
  "threshold": {
    "max_risk_score": 60,
    "harsh_event_count": 5,
    "near_miss_count": 3
  }
}
```

Dùng cho câu hỏi:

- “Xe nào cần bảo trì?”
- “Tài xế/xe nào cần ưu tiên kiểm tra?”

### Function 4: `ask_missing_trip_ids`

Input:

```json
{
  "requested_count": 3,
  "provided_trip_ids": ["T01d"],
  "available_trip_ids": ["T01d", "T02d", "T03d"]
}
```

Output là câu hỏi follow-up cho user, không mở report.

## 4. AI contract field được phép dùng

Không đổi tên field. Dashboard/report phải đọc theo contract AI đã thống nhất:

- `trip_id`
- `metadata.trip_id`
- `metadata.description`
- `metadata.duration_sec`
- `metadata.fps`
- `metadata.speed_limit_kmh`
- `frames[].frame_id`
- `frames[].timestamp`
- `frames[].ego.speed_kmh`
- `frames[].driver.state`
- `frames[].driver.alertness_score`
- `frames[].min_ttc`
- `frames[].headway_sec`
- `frames[].behavior_flags.harsh_brake`
- `frames[].behavior_flags.harsh_accel`
- `frames[].behavior_flags.harsh_corner`
- `frames[].behavior_flags.speeding`
- `frames[].behavior_flags.tailgating`
- `frames[].risk.final_risk_score`

FE hiện cũng dùng các aggregate đã có trong data:

- `trip_aggregate.safe_driving_score`
- `trip_aggregate.avg_risk_score`
- `trip_aggregate.max_risk_score`
- `trip_aggregate.near_miss_count`
- `trip_aggregate.speeding_pct_time`
- `trip_aggregate.tailgating_pct_time`
- `driver_summary.average_alertness_score`
- `driver_summary.microsleep_count`
- `driver_summary.state_distribution_pct`

## 5. Những gì đã làm

### Fleet Ranking

File chính:

- `SE/FE/src/components/DriverRankingView.tsx`
- `SE/FE/src/components/DriverRankingAnalysisPage.tsx`

Đã có:

- Ranking driver theo Safety Score.
- Explain Ranking mở tab mới.
- Report giải thích điểm ranking, risk factor, event log, action/coaching plan.
- Prompt yêu cầu AI giải thích theo kiểu audit/reasoning: mốc thời gian, frame, field nào làm giảm điểm.

### AI Copilot report card

File chính:

- `SE/FE/src/components/AICopilotDrawer.tsx`

Đã có:

- Quick action chips:
  - “So sánh 2 tài xế ...”
  - “Xe nào cần bảo trì?”
  - “Báo cáo an toàn”
- Server-side tool routing qua `/api/copilot`.
- Nếu compare thiếu `trip_id`, Copilot hỏi lại.
- Nếu đủ `trip_id`, Copilot tạo card report.
- Card có nút mở tab mới để xem report chi tiết.

### Copilot report page

File chính:

- `SE/FE/src/components/CopilotFleetReportPage.tsx`

Đã có:

- Report nhiều tài xế/trip.
- Tự ép layout 2/3/4 cột tùy số lượng trip.
- Business KPI.
- Event log theo từng trip.
- AI Copilot Insight gọi Bedrock qua `/api/copilot/report`: so sánh ưu điểm/nhược điểm từng tài xế, kết luận ai tốt nhất, ai cần coaching trước.

### Local trip data

File chính:

- `SE/FE/src/data/btcTripData.ts`

Hiện tại:

- Chỉ giữ local trip gốc đang có trong repo để fallback cho máy chưa có dataset đầy đủ.
- Không clone/synthesize thêm `T02-Mock`, `T03-Mock` hoặc bất kỳ trip giả nào trong FE.
- Khi bàn giao qua máy có full dataset, FE/Backend phải load các trip thật từ dataset/API.

## 6. Những phần còn mock và bắt buộc thay sau này

### Đã thay: Intent/report card không còn mock ở FE

Vị trí:

```txt
SE/FE/src/components/AICopilotDrawer.tsx
```

FE hiện gọi `/api/copilot`. Server trả `reply` hoặc `cardType/cardData`. Không tự dựng report card trong FE nữa.

### Đã thay: AI Copilot Insight không còn mock text

Vị trí:

```txt
SE/FE/src/components/CopilotFleetReportPage.tsx
```

Report page hiện gọi `/api/copilot/report`; server dùng Bedrock để viết insight business. Nếu token lỗi hoặc hết hạn, UI báo lỗi AI provider thay vì tự dựng insight giả.

### Mock 1: Event log trong report

Vị trí:

```txt
SE/FE/src/components/CopilotFleetReportPage.tsx
```

Comment trong code:

```ts
// mock: replace with Backend intervention/event-history endpoint when it exists.
```

Việc cần thay:

- Backend lưu event history/coaching log.
- FE đọc API event history thay vì derive từ frames.

### Đã xoá: Trip mock `T02-Mock`, `T03-Mock`

Vị trí:

```txt
SE/FE/src/data/btcTripData.ts
```

Quy tắc hiện tại:

- Không tự tạo thêm trip ở FE.
- Nếu máy local chỉ có `T01-Sample`, UI chỉ hiển thị đúng dữ liệu đang có.
- Máy có full dataset cần dùng API `/api/v1/alerts/trips` hoặc endpoint trips thật để nạp đủ trip.

## 7. Checklist test nhanh

Chạy FE:

```bash
cd SE/FE
npm run dev
```

Test trong UI:

1. Mở Fleet AI Copilot.
2. Gõ:

```txt
So sánh 2 tài xế
```

Kỳ vọng: Copilot hỏi lại cần trip nào, không mở report.

3. Gõ:

```txt
So sánh 2 tài xế T01d và T02d
```

Kỳ vọng: Copilot tạo card report.

4. Bấm:

```txt
Ấn vào đây để xem báo cáo chi tiết
```

Kỳ vọng: mở tab mới `/ ?view=copilot-report&type=compare&trip_ids=T01d,T02d`.

5. Gõ:

```txt
Compare 3 drivers T01d T02d T03d
```

Kỳ vọng: report 3 cột, có AI Copilot Insight so sánh từng tài xế.

## 8. Việc bắt buộc làm ở phase sau

Lần sau khi user yêu cầu “làm AI Copilot thật”, bắt buộc:

1. Không để Copilot tự chọn trip khi user yêu cầu compare cụ thể.
2. Nếu model/provider hỗ trợ tool calling native, chuyển routing trong `server.ts` sang native tool/function call.
3. FE chỉ render theo tool result từ Backend/server.
4. Không tự tạo trip mock trong FE. Chỉ thay event-history mock khi Backend có endpoint event/coaching log thật.
5. Giữ nguyên AI contract field name, không tự rename.
6. Nếu AI output thiếu field thì Backend/FE phải degrade gracefully, không crash UI.
