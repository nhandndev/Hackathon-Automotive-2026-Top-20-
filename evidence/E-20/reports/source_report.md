# E-20 - Copilot Latency / Cost / Failure

Generated: `2026-08-10T04:23:54Z`  
Commit: `44e6cb3224a58fc0a5d804fc8fab5e233f89e477`

## Status

**PARTIAL / OFFLINE FAILURE AND COST-BUDGET EVIDENCE CREATED; REAL BEDROCK LATENCY PENDING**

## What Was Verified

- Created fixed prompt set for Copilot latency/cost measurement.
- Estimated token/cost budget from prompt sizes without contacting Bedrock.
- Verified source controls for server-side `SE/BE/.env`, timeout, unavailable/pending state, and cache/in-flight handling.
- Ran provider-down simulation against localhost only, with **no external egress**.

## Observed Summary

```json
{
  "generated_at": "2026-08-10T04:23:54Z",
  "commit": "44e6cb3224a58fc0a5d804fc8fab5e233f89e477",
  "status": "PARTIAL_OFFLINE_FAILURE_AND_COST_BUDGET_EVIDENCE_NO_EXTERNAL_BEDROCK_CALL",
  "external_bedrock_calls": 0,
  "reason_no_external_call": "External Bedrock probe was not executed to avoid unapproved egress of project prompts/data and credentials.",
  "fixed_prompt_count": 3,
  "provider_down_simulation_runs": 3,
  "provider_down_failures_captured": 3,
  "source_checks_found": 6,
  "source_checks_total": 15
}
```

## Evidence Files

- `raw/fixed_prompts.jsonl`
- `raw/provider_down_simulation.jsonl`
- `derived/fixed_prompt_cost_estimate.csv`
- `derived/source_controls.csv`
- `derived/copilot_latency_cost_failure_summary.json`
- `raw/server.ts.grep.log`
- `raw/CopilotFleetReportPage.tsx.grep.log`
- `raw/benchmark_bedrock.ts.grep.log`

## Limitation

This evidence does **not** prove real Bedrock p50/p95 latency or real provider token usage. A real provider benchmark must be run separately only after explicit approval to send the fixed prompt set to Bedrock.
