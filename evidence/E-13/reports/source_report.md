# Source Report - E-13 C1 Critical Cases

| Evidence | Source | Note |
|---|---|---|
| `derived/c1_metrics.json` | `evidence/E-01/derived/final_evaluation_summary.json` | C1 metrics/per-trip values summarized into evidence |
| `derived/c1_per_trip_metrics.csv` | `c1_metrics.json -> per_trip` | Per-trip C1 metrics table |
| `derived/c1_critical_case_summary.json` | `c1_metrics.json -> per_trip` | Numeric critical/danger-frame summary; not a PDF case report |
| `commands/commands.log` | E-01 evaluator command + read-only checks | How to rerun/check source |

## Missing / not generated

- `c1_cases.pdf` has not been generated.
- Separate prediction/GT CSV bundle for case-level review has not been created.
- Bin/case definition is not finalized; Tam should review before rendering PDF cases.
- This evidence did not rerun evaluator; it uses repo evidence summaries.
