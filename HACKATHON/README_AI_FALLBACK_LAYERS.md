# Report: Multi-Layer AI Fallback

## Objective

Fleet AI Copilot must keep the report reliable even when Bedrock is slow, times out, fails, or returns an invalid payload.

The system does not use mock AI insight. JSON/local AI telemetry is the canonical baseline. Bedrock is only an explanation layer that can update the report after its response is validated.

## Fallback Diagram

```text
User opens report / requests AI Copilot
            |
            v
[Layer 1] JSON / Local AI Telemetry Baseline
            |
            |-- Canonical data available?
            |       |
            |       |-- No
            |       |       v
            |       |   UI shows missing JSON/local AI data
            |       |
            |       |-- Yes
            |               v
            |       Render deterministic report immediately
            |
            v
[Layer 2] Bedrock Lazy Request
            |
            |-- Called only when the user opens/requests the report
            |-- Detail report sends only the selected trip
            |-- Overview report sends fleet-level aggregate numbers
            |
            v
[Layer 3] Timeout / Abort / Page Exit Guard
            |
            |-- Bedrock timeout
            |-- User leaves the page
            |-- Request is aborted
            |
            v
[Layer 4] Payload Validation
            |
            |-- Valid Bedrock payload?
            |       |
            |       |-- No
            |       |       v
            |       |   Keep JSON/local AI report
            |       |   Do not show fake AI insight
            |       |
            |       |-- Yes
            |               v
            |       Apply Bedrock insight
            |
            v
[Layer 5] Validated Insight Cache / Restore
            |
            |-- Cache validated insight by input signature
            |-- Prevent local fallback from overwriting validated AI
            |
            v
Final UI
```

## Layer 1: JSON / Local AI Telemetry Baseline

This is the source of truth for the report.

Data sources:

- Saved trip JSON
- Local AI telemetry
- Ranking score
- Risk score
- TTC / headway
- Behavior flags
- Event log
- Rule-based maintenance triage

Responsibilities:

- Render the report immediately.
- Keep the UI usable without Bedrock.
- Avoid fabricated metrics.
- Provide canonical data for audit and validation.

## Layer 2: Bedrock Lazy Request

Bedrock is not called aggressively.

Rules:

- Call Bedrock only when the user opens or requests a report.
- Safety detail sends only the selected trip.
- Maintenance detail sends only the selected trip.
- Safety overview sends fleet-level aggregate numbers.
- Maintenance overview sends fleet-level aggregate numbers.

Purpose:

- Reduce Bedrock bottlenecks.
- Improve user experience.
- Prioritize the report the user is currently viewing.

## Layer 3: Timeout / Abort Guard

If Bedrock is slow or the user leaves the page, the pending request can be aborted.

The system should:

- Stop waiting for the old request.
- Avoid updating a page the user has already left.
- Keep resources available for newer requests.
- Preserve the local report already visible on screen.

## Layer 4: Payload Validation

Bedrock output is used only if it passes validation.

Validation rules:

- `ai_status` must be `validated`.
- Safety reports must not contain maintenance-only conclusions.
- Maintenance reports must not fabricate DTC, repair cost, downtime, or work orders.
- Metrics with value `0` must not be described as active risks or violations.
- Bedrock must not overwrite canonical scores, risk levels, event counts, TTC, or maintenance priority.
- The payload must match the requested trip/report input.

If validation fails:

- Do not apply Bedrock insight.
- Keep the JSON/local AI report.
- Do not show fake fallback insight.

## Layer 5: Validated Insight Cache / Restore

When Bedrock returns a valid payload, the system stores it by input signature.

Responsibilities:

- Display a validated AI status.
- Keep the Bedrock insight stable across re-renders.
- Avoid calling Bedrock repeatedly for the same report input.
- Prevent JSON/local fallback from overwriting a validated Bedrock response.

## Success Flow

```text
User opens report
  -> JSON/local AI report renders immediately
  -> Bedrock request starts lazily
  -> Bedrock returns valid payload
  -> Validation passes
  -> UI switches to validated AI insight
  -> Insight is cached by input signature
```

## Failure / Timeout Flow

```text
User opens report
  -> JSON/local AI report renders immediately
  -> Bedrock request starts lazily
  -> Bedrock fails, times out, or returns invalid payload
  -> Validation fails or request is aborted
  -> UI keeps JSON/local AI report
  -> No fake AI insight is displayed
```

## Current Implementation Reference

Main file:

```text
SE/FE/src/components/CopilotFleetReportPage.tsx
```

Important concepts:

- `AiInsightStatus`: tracks `loading`, `pending`, `validated`, and `unavailable`.
- `showLocalFallback()`: keeps the JSON/local AI report when Bedrock is unavailable.
- `applyValidatedPayload()`: applies Bedrock insight only after validation.
- `restoreValidatedPayload()`: prevents local fallback from overwriting a validated Bedrock response.
- `isValidBedrockPayloadForRows()`: blocks invalid or mismatched Bedrock responses.

## Conclusion

Fleet AI Copilot uses JSON/local AI as the required baseline and Bedrock as an optional explanation layer.

If Bedrock is valid, the UI updates to validated AI insight. If Bedrock is invalid, slow, or unavailable, the system safely keeps the deterministic JSON/local AI report and avoids fake data.
