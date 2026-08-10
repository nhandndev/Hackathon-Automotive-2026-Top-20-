# E-22 - Dashboard Workflow Evidence

Generated: `2026-08-10T05:10:00Z`  
Commit: `d41b8e168afb046da1cf26946e987246f42d7a14`

## Status

**PARTIAL / SOURCE WORKFLOW VERIFIED; TEMPORARY UI SCREENSHOTS CAPTURED; CANONICAL VIDEO STILL REQUIRED**

## Claim / outcome

Fleet Dashboard có workflow source-level cho saved/live trip context, trip detail, ranking, ranking analysis, performance insights và Copilot report navigation. Evidence hiện tại chứng minh flow tồn tại trong code và có UI screenshots thật bằng temporary saved trips. Temporary JSON đã được xoá sau capture, nên các ảnh này chỉ chứng minh UI workflow/rendering, không chứng minh model hoặc canonical metric accuracy.

## Điều kiện xác định đạt

- Dashboard phải đọc được saved trip hoặc live trip context.
- Saved trip không được là hidden seeded mock; source phải trỏ tới `src/data/saved_trips`.
- User flow cần thể hiện được: list/map -> trip detail -> ranking -> ranking analysis -> insights/report.
- Video/screenshot cần hiển thị trip ID/provenance hoặc URL query rõ ràng.
- Không dùng E-22 để claim time-saving, usability improvement hoặc production reliability.

## Kết quả quan sát

- `raw/source_locators.log` tìm thấy saved trip loading trong `SE/FE/src/data/btcTripData.ts`, `SE/FE/src/App.tsx` và `SE/FE/server.ts`.
- `App.tsx` có standalone route cho `ranking-analysis` và `copilot-report`.
- `DriverRankingView.tsx` có navigation sang ranking analysis.
- `PerformanceInsightsView.tsx`, `TripDetailView.tsx`, `FleetMapView.tsx` tồn tại trong source flow.
- `CopilotFleetReportPage.tsx` có report route, trip detail link và Word/DOC export handler.
- Runtime screenshots đã capture bằng temporary trip IDs `TMP-E22-SAFE`, `TMP-E22-WATCH`, `TMP-E22-CRITICAL`.
- Temporary files `SE/FE/src/data/saved_trips/TMP-E22-*.json` đã được xoá sau capture.

## Evidence table

| Evidence | Source | Result |
|---|---|---|
| `raw/source_locators.log` | `rg` trên `SE/FE/src` và `SE/FE/server.ts` | Locates saved trips, route/view flow, report/export navigation |
| `derived/workflow_matrix.csv` | Manual mapping from source locators | Maps Dashboard workflow step -> source file -> current proof level |
| `screenshots/*.png` | Real Chrome `screencapture` with temporary saved trips | Shows Fleet Map, Trip Detail, Ranking, Ranking Analysis, Insights and Copilot Report render |
| `reports/source_report.md` | This report | States what is verified and what still needs runtime capture |

## Captured screenshots

- `screenshots/01_fleet_map_tmp_saved_trips.png`
- `screenshots/02_trip_detail_tmp_critical.png`
- `screenshots/03_ranking_tmp_trips.png`
- `screenshots/04_ranking_analysis_tmp_critical.png`
- `screenshots/05_performance_insights_tmp_critical.png`
- `screenshots/06_copilot_report_tmp_critical.png`

## Recommended canonical media capture

Add canonical replay screenshots/video if available:

- `[ADD SCREENSHOT - Fleet Map/List showing real saved trip IDs]`
- `[ADD SCREENSHOT - Trip Detail for one real/canonical saved trip]`
- `[ADD SCREENSHOT - Ranking table from real/canonical saved trips]`
- `[ADD SCREENSHOT - Ranking Analysis for selected real/canonical trip]`
- `[ADD SCREENSHOT - Performance Insights from real/canonical trip]`
- `[ADD VIDEO LINK - list -> trip -> ranking -> analysis -> report workflow]`

Suggested timestamp format:

```text
00:00 - 00:15 Fleet Map/List loads saved trips
00:15 - 00:35 Open Trip Detail
00:35 - 00:55 Open Ranking
00:55 - 01:15 Open Ranking Analysis
01:15 - 01:35 Open Performance Insights / Report
```

## What can be claimed

- Dashboard workflow is implemented at source level.
- Saved trip loading is traceable to `src/data/saved_trips`.
- Main dashboard views are present and linked in source.
- UI render workflow was captured using temporary saved trip JSON and then cleaned up.

## What must not be claimed yet

- Do not claim canonical data accuracy from temporary screenshots.
- Do not claim measured reviewer time improvement from this evidence.
- Do not claim production-grade dashboard reliability from this evidence.
- Do not claim full canonical workflow DONE until real replay/saved-trip video or screenshots are attached.
