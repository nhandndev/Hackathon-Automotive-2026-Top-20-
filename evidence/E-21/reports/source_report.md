# E-21 - Report Export Accuracy / Readability

Generated: `2026-08-10T05:17:00Z`  
Commit: `d41b8e168afb046da1cf26946e987246f42d7a14`

## Status

**PARTIAL / SOURCE EXPORT VERIFIED; TEMP REPORT SCREENSHOTS CAPTURED; CANONICAL KPI AUDIT PENDING**

## Claim / outcome

Copilot Report has source-level support for safety detail, safety overview, maintenance detail/overview report modes and Word-compatible DOC export. Runtime screenshots were captured from the real local UI for three temporary report samples: safety detail, safety overview and maintenance detail. Temporary JSON was deleted after capture.

This evidence is intentionally scoped as **readability/layout + source export verification**. It does not claim canonical KPI accuracy because the screenshots use temporary data for UI rendering.

## Điều kiện xác định đạt

- Generate at least three report samples.
- Confirm report title, summary metric blocks and main sections are visible.
- Verify source path for DOC export.
- Keep caveat if data is temporary and not canonical.
- Do not claim PDF export as final scope.

## Kết quả quan sát

- `raw/source_locators.log` locates report modes, report model, score formatting, Word/DOC export handler and AI status/fallback logic.
- `report_samples/` contains three real Chrome screenshots:
  - `safety_detail_tmp_critical.png`
  - `safety_overview_tmp_fleet.png`
  - `maintenance_detail_tmp_critical.png`
- Report date displayed current date `10/08/2026`.
- Header, report type, trip/fleet metrics and report cards are visible in screenshots.
- Word/DOC export source is located in `CopilotFleetReportPage.tsx` through `handleExportWord`, `application/msword` and `.doc` filename generation.
- Runtime provider failure was observed as `Bedrock 403: Forbidden`; UI still rendered local report content.
- Temporary files `SE/FE/src/data/saved_trips/TMP-E21-*.json` were deleted after capture.

## Evidence table

| Evidence | Source | Result |
|---|---|---|
| `raw/source_locators.log` | `rg` over FE report source | Locates report modes, score formatting and DOC export source |
| `report_samples/*.png` | Real Chrome `screencapture` | Shows report UI layout/readability for three report samples |
| `derived/report_qa.csv` | Manual QA from screenshots/source | Lists visual result and caveats |
| `raw/bedrock_403_during_report_qa.log` | Local FE server output | Captures real Bedrock 403 during report requests |
| `derived/manifest.json` | Evidence metadata | Captures claim/not-claim boundary |

## Report samples

- `[SCREENSHOT] report_samples/safety_detail_tmp_critical.png`
- `[SCREENSHOT] report_samples/safety_overview_tmp_fleet.png`
- `[SCREENSHOT] report_samples/maintenance_detail_tmp_critical.png`

## What can be claimed

- Report UI renders safety detail, safety overview and maintenance detail layouts.
- Word/DOC export handler exists in source and targets `.doc` / `application/msword`.
- Report UI keeps local JSON/local AI content visible even when Bedrock fails.
- Temporary screenshots demonstrate layout/readability at the first viewport.

## What must not be claimed yet

- Do not claim canonical KPI accuracy from temporary screenshots.
- Do not claim downloaded DOC file visual review until a real `.doc` sample is exported and opened.
- Do not claim PDF export as final scope.
- Do not claim full pagination/print layout QA across all report depths from first-viewport screenshots only.
- Do not claim Bedrock factuality, latency or cost from the 403 log.

## Required before DONE

1. Generate report samples from canonical saved trips or replay output.
2. Open/download at least three Word/DOC files and attach them under `report_samples/`.
3. Compare key KPI values in each DOC/UI report with source JSON and record results in `report_qa.csv`.
4. Add screenshots or video covering deeper sections/pagination if final report is longer than first viewport.

