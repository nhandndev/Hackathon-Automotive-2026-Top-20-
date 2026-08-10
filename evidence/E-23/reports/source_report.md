# E-23 - Dashboard Honest Failure States

Generated: `2026-08-10T05:10:00Z`  
Commit: `d41b8e168afb046da1cf26946e987246f42d7a14`

## Status

**PARTIAL / SOURCE FAILURE STATES VERIFIED; EMPTY STATE SCREENSHOT CAPTURED; FULL RUNTIME FAILURE MATRIX REQUIRED**

## Claim / outcome

Dashboard có source-level handling cho empty data, backend/WebSocket outage, saved-trip fallback, AI pending/unavailable status và no-data report states. Evidence hiện tại chứng minh UI không chỉ có happy path trong source và đã capture được empty/no-trip state sau khi xoá temporary saved trips. Tuy nhiên chưa đủ để claim full runtime recovery matrix vì API-down/WebSocket-reconnect/stale-data cases chưa được quay đủ.

## Điều kiện xác định đạt

- Empty data phải hiện trạng thái rỗng, không render dữ liệu giả.
- Backend/API down phải giữ last valid dashboard state hoặc hiển thị trạng thái fallback rõ ràng.
- WebSocket disconnect/reconnect phải không làm UI tự bịa trip mới.
- AI pending/unavailable phải giữ JSON/local baseline, không render mock insight.
- Invalid/no trip phải có no-data state.
- Runtime proof cần ảnh/video/log cho từng case.

## Kết quả quan sát

- `raw/source_locators.log` tìm thấy comment trong `App.tsx` về WebSocket reconnect/reload và giữ last valid dashboard state khi Backend unavailable.
- `FleetMapView.tsx` có empty state `No trip data loaded`.
- `DriverRankingView.tsx` có no-data state `No trip ranking data loaded`.
- `CopilotFleetReportPage.tsx` có state `loading`, `pending`, `validated`, `unavailable` và local fallback path.
- `server.ts` có `ai_status` contract gồm `validated`, `unavailable`, `pending`.
- `screenshots/03_empty_after_temp_delete.png` capture UI thật sau khi xoá temporary saved trip JSON; UI hiển thị `No trip data loaded.`
- `raw/bedrock_403_during_tmp_capture.log` ghi lại provider failure thật (`Bedrock 403: Forbidden`) trong lúc mở report bằng temporary trip.

## Evidence table

| Evidence | Source | Result |
|---|---|---|
| `raw/source_locators.log` | `rg` trên FE/server source | Locates UI/API fallback states |
| `derived/failure_state_matrix.csv` | Manual mapping from source locators | Maps failure case -> expected honest UI behavior |
| `screenshots/03_empty_after_temp_delete.png` | Real Chrome `screencapture` after cleanup | Shows empty/no-trip UI state |
| `raw/bedrock_403_during_tmp_capture.log` | Local FE server output | Captures real Bedrock 403 during report request |
| `reports/source_report.md` | This report | Defines claim boundary and runtime capture requirement |

## Failure state matrix summary

| Failure case | Expected honest behavior | Evidence level |
|---|---|---|
| Empty trips | Show no-trip/no-ranking state | Source + screenshot verified |
| Backend unavailable | Keep last valid state / allow reconnect-reload recovery | Source verified |
| WebSocket reconnect | Recover later without fabricating new data | Source verified |
| AI pending/unavailable | Show status and local baseline, no mock insight | Source verified |
| Invalid trip / no data | No-data state, not fake trip | Source verified |

## Recommended media capture

Add screenshots/video if available:

- `[ADD SCREENSHOT - Empty/no trip state]`
- `[ADD SCREENSHOT - Backend disconnected or API unavailable state]`
- `[ADD SCREENSHOT - AI pending/unavailable report state]`
- `[ADD SCREENSHOT - Invalid trip/no ranking state]`
- `[ADD VIDEO LINK - failure state and recovery capture]`

Suggested timestamp format:

```text
00:00 - 00:20 Empty/no trip state
00:20 - 00:40 Backend unavailable or reconnect state
00:40 - 01:00 AI pending/unavailable fallback
01:00 - 01:20 Recovery after data/API returns
```

## What can be claimed

- Dashboard source includes honest failure states and fallback handling.
- AI fallback states are explicit and typed.
- No-data states exist for map/ranking/report paths.
- Empty/no-trip state was captured after temporary saved trips were deleted.
- A real Bedrock 403 provider failure was observed during temporary report capture.

## What must not be claimed yet

- Do not claim all failure states were runtime-tested until screenshots/video/logs are attached.
- Do not claim exhaustive chaos testing.
- Do not claim production SLA or long-run frontend reliability.
- Do not use the empty-state screenshot as proof of API-down/WebSocket recovery.
- Do not use the Bedrock 403 log as proof of complete latency/cost/factuality audit.
