# E-19 - Copilot Grounded/Factual Audit

Generated: `2026-08-10T04:18:19.948323+00:00`  
Commit: `44e6cb3224a58fc0a5d804fc8fab5e233f89e477`

## Status

**PARTIAL / SOURCE CONTRACT AND GOLDEN SET CREATED; RAW BEDROCK FACTUAL REVIEW PENDING**

## What Was Verified

- Created a 30-case golden/adversarial review set in `golden_payloads/copilot_golden.jsonl`.
- Verified source-level grounding controls in `SE/FE/server.ts`, `CopilotFleetReportPage.tsx`, and `reportModel.ts`.
- Confirmed code paths for `ai_status` states, report-mode-specific prompt contract, Bedrock validation, timeout, in-flight/cache handling, and Word/DOC export.

## Evidence Files

- `golden_payloads/copilot_golden.jsonl`
- `derived/factuality_summary.csv`
- `derived/copilot_grounding_summary.json`
- `raw/server.ts.grep.log`
- `raw/CopilotFleetReportPage.tsx.grep.log`
- `raw/reportModel.ts.grep.log`

## Limitation

This is **not** a completed formal factuality audit yet. It does not include raw Bedrock outputs or human reviewer labels. It proves the contract/validator/golden-set preparation and source safeguards, not production factual accuracy.
