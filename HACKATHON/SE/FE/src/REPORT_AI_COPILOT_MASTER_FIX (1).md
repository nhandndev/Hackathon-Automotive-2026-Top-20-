# REPORT_AI_COPILOT_MASTER_FIX.md

# FPTU DMS Vision — Master Fix for Report + AI Copilot

## Mục tiêu

README này dùng để sửa **toàn bộ tồn đọng của phần Report và AI Copilot**.

Vấn đề chính hiện tại không chỉ là AI hallucination.

Vấn đề lớn hơn là hệ thống đang có xu hướng:

```text
DATA ĐÃ CÓ
    ↓
GỬI CHO AI
    ↓
AI "PHÂN TÍCH LẠI"
    ↓
AI TRẢ VỀ SỐ / EVENT / ACTION
    ↓
UI HIỂN THỊ
```

Đây là architecture sai cho dashboard an toàn.

Kiến trúc đúng phải là:

```text
RAW DATA
    ↓
DETERMINISTIC DOMAIN LOGIC
    ↓
CANONICAL REPORT MODEL
    ↓
UI / EXPORT
    ↓
AI chỉ nhận canonical model để GIẢI THÍCH
```

---

# 1. Golden Rule

```text
IF THE VALUE CAN BE CALCULATED DIRECTLY
FROM TELEMETRY OR EXISTING APPLICATION DATA,
DO NOT ASK AI TO CALCULATE IT.
```

AI chỉ nên làm:

```text
- tóm tắt
- diễn giải
- nêu risk contributors
- viết recommendation
- viết fleet-level narrative
```

AI không nên làm:

```text
- tính Safety Score
- tính Risk Level
- đếm event
- đếm Near Miss
- phát hiện Harsh Brake
- xác định TTC
- xác định Distracted %
- xác định Fatigue count
- tạo DTC
- tạo Brake/Tire wear
- quyết định Coaching Priority
- quyết định Maintenance Priority
- tạo Action Order
- dựng Event Timeline
```

---

# 2. Vì sao không dùng AI cho dữ liệu đã có?

Ví dụ:

```text
Harsh Brake = 0
```

đã có thể tính trực tiếp từ canonical event list.

Không cần gửi cho AI hỏi:

```text
"Trip này có phanh gấp không?"
```

vì AI có thể trả:

```text
"Có một sự kiện phanh gấp ở 01:20"
```

dù dữ liệu thực tế là 0.

Tương tự:

```text
Near Miss = 2
Distracted = 55.8%
Safety Score = 12.5
Risk Level = CRITICAL
```

đều là deterministic values.

AI không có lý do gì phải tính lại.

---

# 3. Target architecture

```text
                         RAW TRIP DATA
                               ↓
                  CANONICAL SAFETY EVENTS
                               ↓
                  CANONICAL DRIVER METRICS
                               ↓
                   CANONICAL SAFETY SCORE
                               ↓
                  CANONICAL REPORT MODEL
                               ↓
             ┌─────────────────┴─────────────────┐
             ↓                                   ↓
       UI / EXPORT                         AI COPILOT INPUT
     deterministic                           canonical only
                                                 ↓
                                              BEDROCK
                                                 ↓
                                        Narrative JSON only
                                                 ↓
                                         Schema Validator
                                                 ↓
                                        Semantic Validator
                                                 ↓
                                   PASS → render narrative
                                   FAIL → deterministic fallback
```

---

# 4. One Source of Truth

Report phải có một canonical model duy nhất.

Ví dụ:

```ts
export interface VehicleReportModel {
  tripId: string;
  driverName: string;

  score: number;
  riskLevel: RiskLevel;
  rank: number;

  avgRisk: number;
  maxRisk: number;

  distractedPct: number;
  fatigueEvents: number;
  speedingPct: number;
  tailgatingPct: number;

  nearMissCount: number;
  harshBrakeCount: number;

  rawCriticalRiskFrames: number;

  events: CanonicalSafetyEvent[];

  eventSummary: {
    safe: number;
    warning: number;
    danger: number;
    total: number;
  };

  safetyAction:
    | 'COACHING_24H'
    | 'WARNING'
    | 'SAFE';

  maintenance: {
    brakeStress: number;
    tireStress: number;

    priority:
      | 'NORMAL'
      | 'WATCH'
      | 'INSPECT';

    dtcCode: string;
  };
}
```

Mọi nơi phải dùng model này:

```text
Report UI
Fleet card
Trip detail
AI input
PDF export
Word export
Comparison report
Safety report
Maintenance report
```

---

# 5. Không tạo model phụ trong từng page

Không:

```text
DriverRankingView tự tính A
Report Page tự tính B
AI tự tính C
Export tự tính D
```

Phải:

```text
ONE canonical domain model
```

---

# 6. Canonical event extractor

Tạo một shared event extractor.

Ví dụ:

```ts
extractCanonicalSafetyEvents(trip)
```

Output:

```ts
interface CanonicalSafetyEvent {
  timestampSec: number;
  timeLabel: string;

  kind:
    | 'HARSH_BRAKE'
    | 'TAILGATING'
    | 'SPEEDING'
    | 'DROWSY'
    | 'DISTRACTED'
    | 'MICROSLEEP'
    | 'YAWNING'
    | 'LOW_TTC'
    | 'STATE_CHANGE';

  severity:
    | 'SAFE'
    | 'WARNING'
    | 'DANGER';

  riskScore: number | null;
  ttcSec: number | null;
  headwaySec: number | null;
  alertnessScore: number | null;
}
```

---

# 7. Frame != Event

Không được:

```text
10 FPS
6 giây drowsy
= 60 fatigue events
```

Nếu field tên là:

```text
fatigueEvents
```

thì phải dùng event semantics, không phải frame count.

---

# 8. Near Miss phải có một định nghĩa

Không:

```ts
nearMissCount =
  frames.filter(lowTtc).length;
```

nếu UI gọi là:

```text
Near Miss Events
```

Dùng debounced canonical LOW_TTC events.

---

# 9. Harsh Brake phải lấy từ event list

```ts
const harshBrakeCount =
  events.filter(
    event =>
      event.kind === 'HARSH_BRAKE'
  ).length;
```

Không cho AI tự detect lại.

---

# 10. Fatigue count phải lấy từ event list / canonical event logic

Không để:

```text
frontend = debounced
ranking = raw frames
AI = model guess
```

---

# 11. TTC threshold phải dùng chung

Search toàn repo:

```text
2.5
3.0
LOW_TTC
min_ttc
```

Tạo:

```ts
export const SAFETY_POLICY = {
  LOW_TTC_SEC: 3.0,
  HIGH_RISK_SCORE: 60,
  CRITICAL_RISK_SCORE: 80,
  EVENT_DEBOUNCE_SEC: 3.0,
} as const;
```

Nếu business rule chọn 2.5:

```text
đổi ONE shared value
```

không để từng page tự hard-code.

---

# 12. Safety Score chỉ có một nguồn

Không được có:

```text
row.score = 36
trip_aggregate.safe_driving_score = 71
AI says 71
```

Phải chọn một canonical final score.

Recommended:

```text
DriverScoreBreakdown.finalScore
```

---

# 13. Score breakdown phải reconcile

```text
Baseline
- Risk penalties
- Distraction
- Fatigue
- Near Miss
- Harsh behavior
- Other canonical penalties
+/- Policy cap
= Final Score
```

Nếu final score không reconcile:

```text
đừng gọi breakdown là exact audit
```

---

# 14. Aggregate score không được silently override

Không:

```ts
finalScore =
  aggregateScore ?? calculatedScore;
```

nếu aggregate có thể dùng formula cũ.

Recommended:

```ts
finalScore = calculatedScore;
```

Legacy aggregate chỉ làm:

```text
reference
```

---

# 15. Risk Level derive từ canonical score

```ts
riskLevel =
  scoreLabel(finalScore);
```

AI không được tự đổi:

```text
CRITICAL → WATCH
```

---

# 16. Ranking deterministic

```text
sort score
assign rank
```

AI không quyết định rank.

---

# 17. Event summary deterministic

```ts
const eventSummary = {
  safe:
    events.filter(
      e => e.severity === 'SAFE'
    ).length,

  warning:
    events.filter(
      e => e.severity === 'WARNING'
    ).length,

  danger:
    events.filter(
      e => e.severity === 'DANGER'
    ).length,

  total:
    events.length,
};
```

Invariant:

```text
safe + warning + danger = total
```

---

# 18. Raw Critical Detections phải đổi semantics rõ

Nếu là frame-level:

```text
Raw Critical Risk Frames
```

không gọi:

```text
Critical Events
```

Nếu UI có:

```text
Raw Critical Risk Frames = 7
Danger Events = 0
```

hai số có thể cùng đúng vì chúng khác semantics.

Tooltip:

```text
Raw Critical Risk Frames:
frame-level high-risk detections.

Danger Events:
canonical debounced safety events
classified as danger.
```

---

# 19. Active Alerts không cộng historical detections

Không:

```ts
activeCriticalAlerts =
  liveAlerts
  + historicalCriticalCount;
```

Tách:

```text
Active Critical Alerts
Historical Critical Risk Frames
```

---

# 20. Report không được nhờ AI tính KPI

Không gửi prompt kiểu:

```text
Hãy tính Safe Score
Hãy xác định Risk Level
Hãy cho biết số Near Miss
```

Những giá trị đó application đã biết.

---

# 21. Report không được nhờ AI dựng Event Timeline

Timeline phải từ:

```text
canonical events
```

AI không dựng:

```text
00:15
01:20
TTC 1.8s
Harsh Brake
```

nếu data không có.

---

# 22. Report không cần AI tạo Core Metrics

Frontend đã có:

```text
Score
Risk
Distracted
Speeding
Harsh Brake
Near Miss
```

AI section không cần tạo lại:

```text
### Core Metrics
```

vì đó là nơi dễ xảy ra conflict.

---

# 23. AI Copilot role đúng

AI chỉ nên nhận:

```text
canonical metrics
canonical events
canonical risk contributors
deterministic safety action
```

và trả:

```text
pros
concerns
recommendation
fleet insight
```

---

# 24. Copilot input type

```ts
interface CopilotTripInput {
  tripId: string;
  driverName: string;

  safety: {
    score: number;
    riskLevel: string;
    maxRisk: number;

    distractedPct: number;
    fatigueEvents: number;
    speedingPct: number;
    tailgatingPct: number;

    nearMissCount: number;
    harshBrakeCount: number;

    safetyAction: string;
  };

  eventSummary: {
    safe: number;
    warning: number;
    danger: number;
    total: number;
  };

  events: CanonicalSafetyEvent[];

  riskContributors: RiskContributor[];
}
```

---

# 25. Không gửi trip_aggregate nếu chứa KPI cạnh tranh

Remove khỏi Bedrock payload:

```text
trip_aggregate.safe_driving_score
legacy score
legacy near miss
legacy risk level
```

Nếu `trip_aggregate` cần cho phần khác:

```text
extract only required non-conflicting fields
```

---

# 26. Không gửi driver_summary nếu AI không cần

Nếu AI chỉ cần:

```text
canonical safety metrics
```

không gửi raw:

```text
driver_summary
```

vì nó có thể chứa counter/percentage khác canonical model.

---

# 27. Không gửi raw frames cho AI để detect event

Raw frames chỉ nên vào:

```text
deterministic event detector
```

không vào Bedrock report explanation.

---

# 28. Build Copilot input một lần

Không:

```text
signature uses object A
request body uses object B
```

Phải:

```ts
const copilotInput =
  buildCopilotInput(
    reportModels
  );
```

Dùng cho cả:

```text
request signature
request body
debug
tests
```

---

# 29. AI response JSON only

Không cho model trả full Markdown:

```text
### Core Metrics
### Event Timeline
### Root Cause
```

Return:

```json
{
  "fleet_insight": "...",
  "trip_insights": {
    "T04-Sample": {
      "pros": [],
      "concerns": [],
      "recommendation": ""
    }
  }
}
```

---

# 30. AI không output authoritative numeric fields

Không schema:

```text
score
riskLevel
nearMiss
TTC
DTC
maintenancePriority
coachingPriority
```

AI không sở hữu chúng.

---

# 31. System prompt bắt buộc

```text
You are DMS Fleet Copilot.

You are an explanation engine only.

The canonical JSON supplied by the
application is authoritative.

Never recalculate or replace:
- Safety Score
- Risk Level
- Ranking
- Event counts
- TTC
- Driver metrics
- Maintenance priority
- Safety action
- DTC

Never invent:
- timestamps
- TTC/headway
- harsh braking
- distraction
- fatigue
- phone usage
- reaction time
- DTC
- physical wear
- cost
- downtime
- inventory
- work orders

Use only supplied canonical fields.

If unavailable:
"Không có dữ liệu".

Do not expose chain-of-thought.
```

---

# 32. AI không infer phone usage

```text
driver.state = distracted
```

không chứng minh:

```text
đang nhìn điện thoại
```

Reject AI claim:

```text
phone
smartphone
điện thoại
```

nếu source không có.

---

# 33. AI không infer reaction time

Không:

```text
reaction time chậm 1.2s
```

nếu system không có reaction-time field.

---

# 34. AI không infer smooth driving

```text
Harsh Brake = 0
```

chỉ support:

```text
Không ghi nhận phanh gấp.
```

Không support:

```text
Vận hành mượt mà.
```

---

# 35. Root Cause → Risk Contributors

Nếu không có causal model:

```text
Root Cause
Nguyên nhân gốc rễ
```

đổi thành:

```text
Risk Contributors
Các yếu tố đóng góp vào rủi ro
```

---

# 36. Risk contributors deterministic

Ví dụ:

```ts
const contributors: RiskContributor[] = [];

if (distractedPct > 30) {
  contributors.push({
    kind: 'DISTRACTION',
    evidence:
      `${distractedPct.toFixed(1)}%`,
  });
}

if (fatigueEvents > 0) {
  contributors.push({
    kind: 'FATIGUE',
    evidence:
      `${fatigueEvents} events`,
  });
}

if (nearMissCount > 0) {
  contributors.push({
    kind: 'LOW_TTC',
    evidence:
      `${nearMissCount} events`,
  });
}
```

---

# 37. Coaching reason deterministic

Không static:

```text
xao nhãng/vi ngủ/near miss
```

Build từ canonical data.

T04:

```text
Distracted 55.8
Fatigue 0
Near Miss 2
```

Expected reason:

```text
xao nhãng cao + TTC/near miss
```

Không được có:

```text
vi ngủ
```

---

# 38. Nếu "Bắt buộc coaching" không phải policy thật

Prefer:

```text
Khuyến nghị coaching ưu tiên trong 24h
```

Không overclaim business policy.

---

# 39. Deterministic pros

Build trực tiếp:

```ts
if (speedingPct === 0) {
  pros.push(
    'Không ghi nhận hành vi vượt tốc trong dữ liệu hiện tại.'
  );
}

if (harshBrakeCount === 0) {
  pros.push(
    'Không ghi nhận sự kiện phanh gấp.'
  );
}
```

Không cần AI phát hiện hai facts này.

---

# 40. Deterministic concerns

```ts
if (distractedPct > 30) {
  concerns.push(
    `Tỷ lệ xao nhãng cao (${distractedPct.toFixed(1)}%).`
  );
}

if (fatigueEvents > 0) {
  concerns.push(
    `Có ${fatigueEvents} fatigue event.`
  );
}

if (nearMissCount > 0) {
  concerns.push(
    `Có ${nearMissCount} TTC/near-miss event.`
  );
}
```

---

# 41. AI chỉ nên viết recommendation

Safest version:

```text
Deterministic Pros
Deterministic Concerns
Deterministic Action
        ↓
Bedrock
        ↓
1 short recommendation / fleet summary
```

---

# 42. Response schema validation

Use Zod or equivalent.

```ts
const tripInsightSchema =
  z.object({
    pros:
      z.array(z.string()).max(5),

    concerns:
      z.array(z.string()).max(5),

    recommendation:
      z.string().max(2000),
  });
```

---

# 43. Semantic validation

Schema valid chưa đủ.

AI vẫn có thể trả:

```text
Safety Score 71/100
```

trong string.

Need semantic validator.

---

# 44. Semantic validator pipeline

```text
Bedrock output
↓
JSON parse
↓
Schema validation
↓
Trip ID allowlist
↓
Metric consistency
↓
Event claim consistency
↓
TTC/timestamp consistency
↓
Unsupported inference guard
↓
Action contradiction guard
↓
PASS
```

---

# 45. Score mismatch guard

Canonical:

```text
36
```

AI mentions:

```text
71/100
```

→ reject.

---

# 46. Risk mismatch guard

Canonical:

```text
CRITICAL
```

AI says:

```text
WATCH
```

→ reject.

---

# 47. Fatigue guard

If:

```text
fatigueEvents = 0
```

AI positive claim:

```text
vi ngủ
microsleep
buồn ngủ
fatigue
```

→ reject.

Negative:

```text
Không ghi nhận fatigue
```

→ allow.

---

# 48. Harsh Brake guard

If:

```text
harshBrakeCount = 0
```

AI says:

```text
Ghi nhận phanh gấp
```

→ reject.

AI says:

```text
Không ghi nhận phanh gấp
```

→ allow.

---

# 49. Speeding guard

If:

```text
speedingPct = 0
```

AI says event occurred:

```text
reject
```

Negative statement allowed.

---

# 50. Distracted guard

If:

```text
distractedPct = 0
```

AI cannot claim distracted occurred.

---

# 51. TTC guard

If AI mentions exact TTC:

value must exist in canonical events.

T04 allowed:

```text
2.61
1.06
```

T04 not allowed:

```text
1.8
```

---

# 52. Timestamp guard

Only canonical event timestamps allowed.

T02 fake:

```text
01:20
```

must fail.

---

# 53. "No events" guard

If:

```text
events.length > 0
```

AI cannot say:

```text
Không có sự kiện nổi bật.
```

T04 regression.

---

# 54. Action contradiction guard

If:

```text
safetyAction = COACHING_24H
```

AI cannot say:

```text
Không cần can thiệp.
```

---

# 55. Retry + fallback

If AI fails validation:

```text
retry once
```

If still fails:

```text
deterministic fallback
```

Do not show invalid AI.

---

# 56. Deterministic fallback

```ts
return {
  pros:
    buildDeterministicPros(model),

  concerns:
    buildDeterministicConcerns(model),

  recommendation:
    buildDeterministicRecommendation(model),
};
```

---

# 57. Frontend must require validated AI

Backend:

```json
{
  "ai_validated": true
}
```

Frontend:

```ts
if (
  payload.ai_validated !== true
) {
  useFallback();
  return;
}
```

---

# 58. Invalid AI must not enter export

PDF / Word:

```text
canonical deterministic report
+
validated AI narrative only
```

If invalid:

```text
fallback narrative
```

---

# 59. AI Action Orders must be removed from authority

Search:

```text
action_orders
aiActionOrders
```

Action Orders must be deterministic.

---

# 60. AI diagnostics must be removed from authority

Search:

```text
vehicle_diagnostics
aiDiagnostics
brake_wear_pct
tire_wear_pct
```

AI cannot create mechanical diagnostics.

---

# 61. Fake DTC must be removed

Search:

```text
C0035
P0000
```

DTC only from:

```text
obd.dtc_codes
vehicle_health.dtc_codes
```

else:

```text
N/A
```

---

# 62. Brake/Tire Stress != Wear

Keep:

```text
Brake Stress Index
Tire Stress Index
```

Do not output:

```text
phanh mòn 35%
lốp mòn 45%
```

unless actual wear sensor exists.

---

# 63. Maintenance priority deterministic

```text
NORMAL
WATCH
INSPECT
```

rule engine owns it.

AI can explain:

```text
why WATCH
```

but cannot change WATCH → INSPECT.

---

# 64. Cost/downtime

If deterministic heuristic:

label:

```text
(dự tính)
Rule-based estimate
```

AI cannot create different values.

---

# 65. Work order

If no real ERP/workshop integration:

```text
Recommended — not created
```

AI cannot claim:

```text
Pending Approval
Parts Ordered
WO-123
```

---

# 66. Report wording

Report title/subtitle must reflect authority.

Bad:

```text
AI Copilot đánh giá ưu tiên bảo trì
```

if priority is rule-based.

Good:

```text
Rule-based maintenance priority;
AI Copilot provides explanation.
```

---

# 67. AI Confidence

If no true model confidence:

```text
N/A
```

Do not map:

```text
Safety Score → AI Confidence
```

---

# 68. Local rule-based analysis

If `buildLocalAnalysis()` is deterministic:

label:

```text
Rule-based Score Explanation
```

not:

```text
AI Reasoning
```

---

# 69. Report model owns driver identity

Use one driver name resolver.

Do not display:

```text
trip ID
```

under:

```text
Best Driver
```

unless driver name unavailable.

---

# 70. Selected trip consistency

Ensure:

```text
selectedVehicle
selectedTripId
selectedRow
Report header
Copilot input
```

always same trip.

No silent fallback when requested trip invalid.

---

# 71. Request signature

Build from same canonical Copilot input that is sent.

```ts
const copilotInput =
  buildCopilotInput(reportModels);

const signature =
  JSON.stringify(copilotInput);
```

---

# 72. Request ID and policy version

Include:

```text
request_id
policy_version
input_signature
```

for debugging.

---

# 73. Logs

Log:

```text
request ID
trip IDs
policy version
model ID
validation pass/fail
retry count
fallback used
```

Never AWS credentials.

---

# 74. Demo-safe mode

Config:

```ts
COPILOT_REQUIRE_VALIDATION = true;
```

Invalid AI:

```text
do not render
```

---

# 75. Bedrock unavailable

UI:

```text
AI narrative unavailable.
Deterministic safety metrics remain valid.
```

Do not make user think whole report failed.

---

# 76. T02 Regression

Must fail AI output containing:

```text
71/100
WATCH
TTC 1.8
01:20
Harsh Brake occurred
Phone usage
Reaction time 1.2s
```

---

# 77. T04 Regression

Must fail:

```text
No notable events
Fatigue/vi ngủ when fatigue=0
Smooth driving unsupported
Fake TTC
```

Must allow:

```text
Distracted 55.8% concern
TTC concern
No harsh brake
No speeding
```

---

# 78. Synthetic Fatigue Test

```text
10 FPS
6 sec drowsy
```

must not result in:

```text
60 fatigue events
```

---

# 79. Synthetic LOW_TTC Test

```text
20 consecutive low-TTC frames
```

must follow canonical debounce policy.

---

# 80. Raw Critical Test

```text
risk >= 80 over multiple frames
```

must distinguish:

```text
Raw Critical Risk Frames
vs
Danger Events
```

---

# 81. Missing telemetry test

```text
min_ttc=null
risk=undefined
alertness=undefined
```

Expected:

```text
N/A
```

No fake zero.

---

# 82. Conflicting score test

Fixture:

```text
canonical score = 36
legacy aggregate = 71
```

Bedrock serialized input must contain authoritative score only.

---

# 83. AI invalid JSON test

Expected:

```text
retry once
fallback
```

---

# 84. Unknown trip test

AI returns:

```text
UNKNOWN trip
```

reject/remove.

---

# 85. Export test

Invalid AI response must not appear in exported report.

---

# 86. Repository search checklist

Search and classify all occurrences:

```text
trip_aggregate
safe_driving_score
aiActionOrders
action_orders
aiDiagnostics
vehicle_diagnostics
brake_wear_pct
tire_wear_pct
C0035
P0000
AI Confidence
Root Cause
Core Metrics
Event Timeline
xao nhãng/vi ngủ/near miss
vận hành mượt mà
Không có sự kiện nổi bật
```

---

# 87. Definition of Done — Report

- [ ] Report uses one VehicleReportModel.
- [ ] UI metrics deterministic.
- [ ] Event log deterministic.
- [ ] Export metrics deterministic.
- [ ] No duplicate score source.
- [ ] No duplicate event source.
- [ ] Raw frames and events clearly separated.
- [ ] TTC threshold shared.
- [ ] Coaching reasons dynamic.
- [ ] Maintenance authority rule-based.
- [ ] AI sections narrative-only.

---

# 88. Definition of Done — AI Copilot

- [ ] Canonical input only.
- [ ] No trip_aggregate KPI conflicts.
- [ ] No raw frames for re-detection.
- [ ] Strict system prompt.
- [ ] JSON-only output.
- [ ] Runtime schema validator.
- [ ] Semantic validator.
- [ ] Score guard.
- [ ] Risk guard.
- [ ] Event guard.
- [ ] TTC guard.
- [ ] Timestamp guard.
- [ ] Unsupported inference guard.
- [ ] Action contradiction guard.
- [ ] Retry max 1.
- [ ] Deterministic fallback.
- [ ] ai_validated flag.
- [ ] Invalid AI never rendered/exported.

---

# 89. Definition of Done — Domain

- [ ] One final score source.
- [ ] Score breakdown reconciles.
- [ ] One LOW_TTC threshold.
- [ ] One event debounce policy.
- [ ] Fatigue event semantics documented.
- [ ] Near Miss semantics documented.
- [ ] Harsh Brake semantics documented.
- [ ] Critical frame semantics documented.
- [ ] Missing telemetry remains N/A.

---

# 90. Required tests

Run actual repository commands:

```bash
tsc --noEmit
npm run lint
npm test
```

or repo-native pnpm/yarn/vitest/jest commands.

Do not claim passed without executing.

---

# 91. Required final response from Codex / Claude

Must report:

```text
1. Files changed
2. Canonical Safety Score source
3. LOW_TTC threshold
4. Event debounce policy
5. Fatigue definition
6. Near Miss definition
7. Harsh Brake definition
8. Raw Critical definition
9. VehicleReportModel source
10. Copilot input schema
11. Bedrock output schema
12. Semantic validators added
13. Fallback behavior
14. T02 test result
15. T04 test result
16. TypeScript result
17. Lint result
18. Test result
19. Remaining limitations
```

---

# 92. Questions Codex must answer before DONE

```text
Why is AI being used for this value?

Can this value be calculated directly from canonical data?

If yes, remove AI authority.

Where does Safety Score come from?

Where does Risk Level come from?

Where do events come from?

What exactly is a Near Miss?

What exactly is a Fatigue Event?

What exactly is Raw Critical?

What can Bedrock see?

What can Bedrock return?

What happens if Bedrock lies?

What happens if Bedrock is down?
```

---

# 93. Recommended implementation phases

```text
PHASE 1
Canonical domain data
- events
- thresholds
- score
- report model

PHASE 2
Remove AI from deterministic values
- KPI
- event counts
- actions
- diagnostics
- maintenance priority

PHASE 3
Copilot contract
- canonical input
- strict JSON output
- prompt

PHASE 4
Validation
- schema
- semantic
- fallback

PHASE 5
UI/export
- validated narrative only
- no duplicate AI KPI
- no AI timeline

PHASE 6
Tests
- T02
- T04
- synthetic event cases
- export
- TypeScript/lint
```

---

# 94. Critical instruction

Do NOT solve this by:

```text
adding more prompt text only
```

A correct solution requires:

```text
Canonical domain logic
+
Canonical report model
+
AI authority reduction
+
Strict AI contract
+
Schema validation
+
Semantic validation
+
Fallback
+
Regression tests
```

---

# 95. Do not hard-code sample trips

Never:

```ts
if (tripId === 'T04-Sample') ...
```

T02/T04 are tests only.

---

# 96. Do not hide bad AI output with CSS

Bad data must be blocked before render.

---

# 97. Final target

```text
DATA decides facts.
RULE ENGINE decides score/action.
REPORT renders facts.
AI explains facts.
VALIDATOR checks AI.
```

---

# 98. Final acceptance statement

AI Copilot is complete when:

```text
Even if the LLM internally hallucinates,
the application never allows unsupported
AI-generated facts to reach the user.
```

---

# 99. Prompt to give Codex / Claude Code

```text
Read REPORT_AI_COPILOT_MASTER_FIX.md completely.

Audit the entire repository, especially:
- Report
- Driver Ranking
- Safety event extraction
- scoring
- /api/copilot/report
- Bedrock prompt/service
- AI response handling
- PDF/Word export

For every output field, ask:
"Can this be calculated directly from canonical data?"

If yes:
remove AI authority for that field.

Fix the project end-to-end.
Do not only edit the prompt.

Do not mark DONE until:
- all P0 issues are resolved,
- T02 and T04 regression tests pass,
- TypeScript/lint/tests are actually run,
- and remaining limitations are reported.

Do not hard-code sample trip IDs.
Do not allow AI-generated numbers/events/actions
to become authoritative report data.
```
