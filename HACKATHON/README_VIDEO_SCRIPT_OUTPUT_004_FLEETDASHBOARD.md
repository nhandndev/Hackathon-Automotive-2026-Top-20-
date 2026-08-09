# Video Script - Output #004 FleetDashBoard

Mục tiêu video: chứng minh Fleet Dashboard chạy thật, đọc saved trip JSON, hiển thị đủ các view chính và export Word/DOC. Video này dùng cho evidence của `Output #004 - FleetDashBoard`.

## Chuẩn bị trước khi quay

1. Chạy Backend:

```bash
cd SE/BE
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2. Chạy Frontend:

```bash
cd SE/FE
npm run dev
```

3. Kiểm tra nhanh:

```bash
curl -s http://127.0.0.1:8000/health
curl -I http://127.0.0.1:3000/
find SE/FE/src/data/saved_trips -maxdepth 1 -name '*.json' | sort
```

Kỳ vọng:

```text
Backend health: status ok
Frontend: HTTP 200
Saved trips: T01-Sample.json -> T06-Sample.json
```

4. Mở browser:

```text
http://127.0.0.1:3000/?view=MAP
```

## Script quay video

### 00:00 - 00:10 | Mở Fleet Dashboard

Thao tác:

- Mở `http://127.0.0.1:3000/?view=MAP`.
- Quay rõ header/app shell của Dashboard.

Lời nói gợi ý:

```text
Fleet Dashboard đang chạy local. Backend và Frontend đã start, giao diện mở từ local dev server.
```

Evidence cần thấy:

- Dashboard render được.
- Không có màn lỗi trắng.
- Không có crash overlay.

### 00:10 - 00:25 | Chứng minh saved trips có data

Thao tác:

- Cho thấy danh sách trip hoặc map/list có `T01-Sample` đến `T06-Sample`.
- Nếu đang ở view khác, chuyển về Fleet Map/List.

Lời nói gợi ý:

```text
Dashboard đang đọc saved trip JSON trong SE/FE/src/data/saved_trips. Các trip T01 đến T06 được load làm completed trip context.
```

Evidence cần thấy:

- Tối thiểu một vài trip sample xuất hiện.
- Tốt nhất thấy đủ `T01-Sample`, `T02-Sample`, `T03-Sample`, `T04-Sample`, `T05-Sample`, `T06-Sample`.

### 00:25 - 00:45 | Trip Detail

Thao tác:

- Click một trip, ví dụ `T02-Sample`.
- Mở `Trip Detail`.
- Quay rõ các metric: speed/risk/ranking score/event summary/location/recorded summary.

Lời nói gợi ý:

```text
Trip Detail lấy số liệu từ JSON/local AI baseline. Nếu live camera hoặc AI runtime chưa chạy thì UI hiển thị trạng thái waiting/offline, không tự bịa data.
```

Evidence cần thấy:

- Trip detail mở được.
- Có trip id đúng.
- Có metric hoặc fallback state rõ ràng.

### 00:45 - 01:05 | Ranking

Thao tác:

- Chuyển sang view `Ranking`.
- Quay bảng ranking.

Lời nói gợi ý:

```text
Ranking dùng Ranking Score tính từ JSON/local AI. Risk và average risk là chỉ số audit, không dùng để thay thế ranking score.
```

Evidence cần thấy:

- Bảng ranking có các trip.
- Có score/risk/events/coaching hoặc các cột tương đương.
- Thứ tự ranking hiển thị ổn định.

### 01:05 - 01:25 | Ranking Analysis

Thao tác:

- Mở Ranking Analysis cho một trip, ví dụ:

```text
http://127.0.0.1:3000/?view=ranking-analysis&trip_id=T03-Sample
```

- Quay rõ phần explanation/penalty/bậc xếp hạng.

Lời nói gợi ý:

```text
Ranking Analysis giải thích vì sao trip đứng ở bậc này, gồm ranking method, penalty breakdown và audit trail từ local AI telemetry.
```

Evidence cần thấy:

- Có trip id đúng.
- Có giải thích rank reason.
- Có penalty/score breakdown hoặc audit reasoning.

### 01:25 - 01:45 | Performance Insights

Thao tác:

- Mở Performance Insights.
- Quay risk timeline, contributing factors, full trip insight/local AI summary.

Lời nói gợi ý:

```text
Performance Insights tổng hợp toàn trip, không chỉ frame cuối. Các chart và factor lấy từ JSON/local AI telemetry.
```

Evidence cần thấy:

- Risk timeline.
- Top contributing factors.
- Full trip insight hoặc local AI summary.

### 01:45 - 02:20 | Safety Report Detail

Thao tác:

- Mở Copilot Report detail cho một trip:

```text
http://127.0.0.1:3000/?view=copilot-report&type=safety&trip_ids=T02-Sample
```

- Quay phần header, KPI, trip safety detail, event log, local report/Bedrock status.

Lời nói gợi ý:

```text
Safety detail report render baseline từ JSON/local AI trước. Bedrock là explanation layer; nếu chưa có phản hồi hợp lệ thì UI giữ local report và không hiển thị insight giả.
```

Evidence cần thấy:

- Report detail mở được.
- Score format nhất quán.
- Có trạng thái Bedrock rõ ràng: waiting/validated/unavailable.
- Không có mock static insight thay thế khi AI chưa sẵn sàng.

### 02:20 - 02:50 | Safety Report Overview

Thao tác:

- Mở report overview nhiều trip:

```text
http://127.0.0.1:3000/?view=copilot-report&type=safety&trip_ids=T02-Sample%2CT01-Sample%2CT03-Sample%2CT05-Sample%2CT04-Sample%2CT06-Sample
```

- Quay Fleet Summary, Review Priority, Trip Cards, Safety KPI Context.

Lời nói gợi ý:

```text
Safety overview là fleet-level report cho toàn bộ batch, không phải detail report. Review priority và relative ranking được tách rõ.
```

Evidence cần thấy:

- Fleet Summary.
- Trips analyzed.
- Review Priority.
- Multiple trip cards.
- KPI context.

### 02:50 - 03:20 | Maintenance Report

Thao tác:

- Mở maintenance report detail hoặc overview nếu UI có nút dropdown `Báo cáo trip`.
- Ví dụ nếu route hỗ trợ:

```text
http://127.0.0.1:3000/?view=copilot-report&type=maintenance&trip_ids=T02-Sample
```

Lời nói gợi ý:

```text
Maintenance report là rule-based từ JSON/local AI telemetry. Bedrock chỉ diễn giải insight, không tự tạo KPI bảo trì.
```

Evidence cần thấy:

- Maintenance report mở được.
- Có priority/KPI/context.
- Không ghi nhầm `xe` hoặc `driver` nếu data chỉ là trip.

### 03:20 - 03:50 | Word/DOC Export

Thao tác:

- Click `Export Report`.
- Tải file `.doc`.
- Mở file DOC vừa tải hoặc cho thấy file download.

Lời nói gợi ý:

```text
Final demo scope dùng Word/DOC export. PDF không nằm trong final claim vì từng có rủi ro browser export trắng.
```

Evidence cần thấy:

- Export button hoạt động.
- File `.doc` được tải.
- DOC có title/report content/metrics.

### 03:50 - 04:10 | Honest Fallback

Thao tác:

- Quay một trạng thái waiting/offline/loading nếu có, ví dụ camera frame offline hoặc Bedrock waiting.

Lời nói gợi ý:

```text
Khi AI hoặc live runtime chưa sẵn sàng, Dashboard hiển thị waiting/offline/loading thay vì sinh số liệu giả.
```

Evidence cần thấy:

- UI có fallback/degraded/loading state rõ ràng.
- Không có kết luận SAFE giả khi thiếu data.

## Dòng điền vào report sau khi quay

Sau khi quay xong, điền `Video timestamp` cho Output #004 như sau:

```text
00:00-00:10 Fleet Dashboard mở được
00:10-00:25 saved trips/list hiển thị
00:25-00:45 mở Trip Detail
00:45-01:05 mở Ranking
01:05-01:25 mở Ranking Analysis
01:25-01:45 mở Performance Insights
01:45-02:20 mở Safety Detail Report
02:20-02:50 mở Safety Overview Report
02:50-03:20 mở Maintenance Report
03:20-03:50 export Word/DOC
03:50-04:10 fallback/loading/offline state
```

## Evidence locator nên ghi trong Output #004

```text
SE/FE/package.json
SE/FE/server.ts
SE/FE/src/App.tsx
SE/FE/src/data/btcTripData.ts
SE/FE/src/data/saved_trips/T01-Sample.json
SE/FE/src/data/saved_trips/T02-Sample.json
SE/FE/src/data/saved_trips/T03-Sample.json
SE/FE/src/data/saved_trips/T04-Sample.json
SE/FE/src/data/saved_trips/T05-Sample.json
SE/FE/src/data/saved_trips/T06-Sample.json
SE/FE/src/components/CopilotFleetReportPage.tsx
Video: FleetDashboard_Output004_[date].mp4
Exported DOC: FleetSafety_or_Maintenance_Report_[date].doc
```

## Checklist đạt/chưa đạt

- [ ] FE mở được tại `http://127.0.0.1:3000`.
- [ ] BE `/health` trả `status: ok`.
- [ ] Saved trips T01-T06 hiển thị.
- [ ] Trip Detail mở được.
- [ ] Ranking mở được.
- [ ] Ranking Analysis có giải thích điểm/rank.
- [ ] Performance Insights có full-trip insight.
- [ ] Safety Detail Report mở được.
- [ ] Safety Overview Report mở được.
- [ ] Maintenance Report mở được.
- [ ] Word/DOC export tải được.
- [ ] Fallback/loading/offline state được quay rõ.

