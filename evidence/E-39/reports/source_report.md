# E-39 - Driver-Warning Human-Factors Review

Generated: `2026-08-10T05:10:00Z`  
Commit: `d41b8e168afb046da1cf26946e987246f42d7a14`

## Status

**NOT EXECUTED / CLAIM CONTROL ONLY - NO HUMAN-FACTORS OUTCOME CLAIM**

## Finding

No formal driver human-factors study was executed in this evidence package. Therefore the project should **not** claim measured alert-fatigue reduction, driver acceptance, comprehension rate, reaction-time improvement, distraction reduction, or real-world safety outcome from the HMI warning UI.

## What is verified

- Source/APK-level HMI warning states exist, including `SAFE`, `WARNING`, `CRITICAL`, TTC, alertness, driver state and action wording.
- The UI/HMI source indicates warning content can be displayed to a driver-facing screen.
- E-24 can support a technical integration claim for CarSky/HMI signal path.

## What is not verified

- No participant protocol.
- No consent record.
- No reviewer/driver survey.
- No alert-fatigue measurement.
- No reaction-time experiment.
- No real vehicle safety outcome.

## Evidence table

| Evidence | Source | Result |
|---|---|---|
| `raw/source_locators.log` | `rg` over HMI/BE sources | Locates driver warning UI strings and warning-state code |
| `derived/human_factors_claim_register.json` | Claim-control register | Lists allowed and disallowed claims |
| `reports/source_report.md` | This report | Defines truthful boundary |

## Allowed wording

```text
Android HMI implements a driver-facing warning display for SAFE/WARNING/CRITICAL states and shows risk/TTC/alertness/action information from the DMS signal path.
```

## Disallowed wording

```text
The HMI reduces driver reaction time.
The HMI reduces alert fatigue.
Drivers accept or prefer the warning UI.
The warning UI improves real-world safety outcomes.
The HMI warning policy is validated by a human-factors study.
```

## Required before claiming human-factors outcome

1. Define participant protocol and consent.
2. Define warning scenarios and baseline UI.
3. Measure comprehension, reaction time, false alarm perception and alert fatigue.
4. Store raw participant results and anonymized labels.
5. Summarize limitations and sample size.

## Optional media placeholder

If you have screenshots/video of the HMI warning UI, attach them as technical UI evidence only:

- `[ADD SCREENSHOT - Android HMI SAFE state]`
- `[ADD SCREENSHOT - Android HMI WARNING state]`
- `[ADD SCREENSHOT - Android HMI CRITICAL state]`
- `[ADD VIDEO LINK - HMI state transition demo]`

These media files do **not** convert E-39 into a human-factors study by themselves.

