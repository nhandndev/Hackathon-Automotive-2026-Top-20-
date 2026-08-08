Bạn đang đứng trong repo của dự án Fleet Dashboard / Vision Command.

Nhiệm vụ của bạn: đọc toàn bộ codebase và tạo một file markdown mới tên:

README_AI_COPILOT_CONTEXT.md

Mục tiêu của file này là cung cấp đầy đủ context cho một AI khác có thể hiểu và fix phần AI Copilot report, Fleet Ranking, Performance Insights và Executive Report mà không cần đoán.

Yêu cầu quan trọng:
- Không sửa code ở bước này.
- Chỉ đọc, phân tích và tạo README_AI_COPILOT_CONTEXT.md.
- Không viết chung chung.
- Phải ghi rõ tên file, tên component, tên function, tên hook, tên API route, tên data file nếu tìm thấy.
- Nếu không tìm thấy thông tin nào, ghi rõ “Not found in current codebase”.
- Nếu có nhiều nguồn tính score khác nhau, phải chỉ rõ từng nguồn và khả năng gây lệch số.
- Nếu có hard-code/mock data/local JSON, phải liệt kê đầy đủ.

README_AI_COPILOT_CONTEXT.md phải có các section sau:

# README AI Copilot Context

## 1. Project Overview
Mô tả project này là gì, dashboard phục vụ mục tiêu gì, các màn hình chính gồm gì:
- Overview / Map
- Monitor / Live Cam
- Trip Detail
- Insights
- Ranking
- AI Copilot
- Executive Report

## 2. Tech Stack
Liệt kê framework, language, package chính:
- React/Next/Vite nếu có
- Tailwind/CSS nếu có
- Chart library nếu có
- Backend/API nếu có
- AI provider nếu có: AWS Bedrock, OpenAI, local AI, mock response...

## 3. Folder Structure Relevant To AI Copilot
Liệt kê các folder/file quan trọng liên quan tới:
- data loading
- scoring
- risk calculation
- ranking table
- insights page
- copilot chat
- report generation
- executive report
- UI components

Format:
| Path | Purpose | Notes |
|---|---|---|

## 4. Current Data Model
Đọc code/data và mô tả data model hiện tại.

Cần làm rõ các entity:
- Fleet
- Vehicle
- Driver
- Trip
- Dataset sample
- Frame
- Risk
- Driver state
- TTC
- Headway
- Behavior flags
- Event log

Nếu hiện tại T01-Sample/T02-Sample đang bị dùng lẫn giữa trip, driver, vehicle hoặc dataset sample thì ghi rõ.

## 5. Input Data Contract
Liệt kê cấu trúc JSON/local AI/BTC data đang được dùng.

Cần chỉ rõ các field:
- trip_id
- metadata
- frames
- frame_id
- timestamp
- ego
- driver
- driver.state
- alertness_score
- min_ttc
- headway_sec
- behavior_flags
- risk.final_risk_score
- speed
- near_miss
- fatigue/microsleep
- distracted
- tailgating
- harsh behavior

Nếu có sample object, trích một object ngắn đại diện.

## 6. Canonical Scoring Logic
Tìm và mô tả chính xác công thức tính Ranking Score.

Cần ghi rõ:
- base score là bao nhiêu
- average risk penalty
- max risk penalty
- critical frame penalty
- distracted penalty
- fatigue penalty
- harsh behavior penalty
- TTC/tailgating/near miss penalty nếu có
- rounding rule
- clamp min/max nếu có
- điểm cuối lấy từ đâu

Format mong muốn:

Ranking Score = Base Score - Total Penalty

Base Score: 100

Penalty breakdown:
| Factor | Formula | Weight | Example |
|---|---|---|---|

Ví dụ:
Average Risk Penalty = avgRisk * 0.45
Max Risk Penalty = maxRisk * 0.20
Critical Frame Penalty = criticalFrameRatio * 0.15

Nếu code hiện tại khác ví dụ trên, ghi theo code thật.

## 7. Severity / Safety Classification Rules
Tìm rule hiện tại để phân loại:
- SAFE
- LOW
- MEDIUM
- HIGH
- CRITICAL

Cần làm rõ:
- Ranking Score bao nhiêu thì CRITICAL?
- Max Risk bao nhiêu thì CRITICAL?
- Critical frame ratio bao nhiêu thì HIGH/CRITICAL?
- Distracted %, fatigue, harsh events threshold là gì?
- Nếu không có threshold rõ trong code, ghi “threshold not explicitly defined”.

Đề xuất format:
| Level | Rule | Source file |
|---|---|---|

## 8. Current Ranking Data
Liệt kê ranking hiện tại của 6 trip/sample theo code/data thật.

Format:
| Rank | Trip | Ranking Score | Avg Risk | Max Risk | High-risk Frames | Distracted | Fatigue | Near Miss | Safety |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|

Phải kiểm tra xem số ở:
- Ranking page
- Copilot answer
- Executive report
- Insights page

có bị lệch nhau không. Nếu lệch, ghi rõ:
| Trip | Ranking Page | Copilot | Executive Report | Problem |
|---|---:|---:|---:|---|

## 9. AI Copilot Current Implementation
Tìm phần code AI Copilot.

Cần ghi rõ:
- component render chat nằm ở file nào
- state messages nằm ở đâu
- suggested prompts/chips nằm ở đâu
- function gửi message nằm ở đâu
- API route/backend endpoint là gì
- system prompt hiện tại là gì
- user prompt được build ra sao
- context nào được gửi vào AI
- response được parse/render như thế nào
- có markdown renderer không
- có structured cards không
- có hard-coded replies không

Format:
| Item | Location | Description |
|---|---|---|

## 10. AI Copilot Problems Found
Phân tích lỗi hiện tại của AI Copilot, đặc biệt:
- Copilot tự tính lại score thay vì dùng canonical score
- số bị lệch với Ranking page
- report quá dài hoặc dump dữ liệu
- gọi “best driver” dù vẫn CRITICAL
- trả lời maintenance dù không có vehicle-health telemetry
- action plan không khớp dữ liệu
- nói nghỉ/nghỉ an toàn dù fatigue = 0
- nói giảm distracted/tailgating/near miss dù các metric đó đang bằng 0
- trộn trip/driver/vehicle
- trộn tiếng Anh và tiếng Việt

## 11. Target AI Copilot Behavior
Mô tả behavior mong muốn:

AI Copilot KHÔNG được tự tính lại score nếu canonical ranking đã có.
AI Copilot phải dùng canonical scoring/ranking data từ source chung.
AI Copilot phải phân biệt:
- Relative ranking
- Absolute safety
- Driver behavior risk
- Traffic/environment risk
- Data unavailable

AI Copilot phải biết từ chối hoặc giới hạn khi thiếu dữ liệu:
Ví dụ user hỏi “Xe nào cần bảo trì?” nhưng chỉ có DMS/safety telemetry, không có engine/battery/brake/tire/DTC data.
Copilot nên trả:
“Hiện chưa có vehicle-health telemetry để kết luận bảo trì. Tôi có thể ưu tiên xe/chuyến cần review an toàn dựa trên driving-risk data.”

## 12. Standard Copilot Report Format
Đề xuất format chuẩn cho Copilot khi user hỏi báo cáo an toàn fleet:

### Fleet Safety Summary
- Fleet status:
- Trips analyzed:
- Fleet avg ranking score:
- Fleet avg risk:
- High-risk frames:
- Trips requiring review:

### Priority Ranking
| Priority | Trip | Score | Absolute Safety | Main Reason |
|---|---|---:|---|---|

### Main Risk Contributors
- Average risk:
- High-risk frames:
- Distraction:
- Harsh behavior:
- Fatigue:
- Near miss / unsafe TTC:

### Recommended Actions
- Immediate:
- Monitoring:
- Coaching:
- Next review:
- Success metric:

### Data Limitations
- GPS available?
- Camera available?
- Maintenance telemetry available?
- Synthetic/mock/local JSON?

## 13. Standard Trip-Level Report Format
Đề xuất format chuẩn khi user hỏi riêng một trip như T02-Sample:

### Trip Safety Report: T02-Sample

#### 1. Executive Summary
- Relative fleet rank:
- Ranking score:
- Absolute safety:
- Coaching priority:
- Main conclusion:

Important wording:
“#1 chỉ là xếp hạng tương đối trong fleet hiện tại, không đồng nghĩa với chuyến đi an toàn tuyệt đối.”

#### 2. Score Breakdown
Base score:
Average risk penalty:
Max risk penalty:
Critical frame penalty:
Driver behavior penalty:
Final ranking score:

#### 3. Why This Trip Is Still Critical
Explain with thresholds:
- Max risk:
- Avg risk:
- Critical frames:
- Any trigger that sets CRITICAL:

#### 4. Driver Behavior Evidence
- Distracted:
- Fatigue:
- Alertness:
- Speeding:
- Tailgating:
- Near miss:

Nếu tất cả đều thấp/0 thì phải nói rõ:
“Critical classification appears driven mainly by AI risk/environment/traffic factors, not observable driver-attention violations.”

#### 5. Action Plan
Action phải khớp data.
Không được yêu cầu nghỉ nếu fatigue = 0.
Không được yêu cầu giảm distracted nếu distracted = 0.
Không được yêu cầu giảm tailgating nếu tailgating = 0.
Nếu primary issue là risk/critical frames thì action phải là review high-risk segments.

#### 6. Success Metrics
- Ranking score increases
- Avg risk decreases
- Max risk decreases
- Critical frame ratio decreases
- Distraction/tailgating/near miss remain at 0 if currently 0

## 14. Required Fixes
Tạo checklist fix code theo thứ tự ưu tiên:

P0:
- One canonical scoring source
- Copilot uses canonical score
- Fix score mismatch across Ranking/Copilot/Report/Insights
- Rename Best Driver to Highest-ranked / Lowest-risk trip
- Fix maintenance answer when no vehicle-health telemetry
- Separate Trip/Driver/Vehicle semantics

P1:
- Add severity threshold explanation
- Add chart legend
- Add fleet action summary
- Standardize language
- Fix action plans to match evidence

P2:
- Improve report readability
- Collapse technical audit by default
- Add data limitation section

## 15. Acceptance Criteria
Viết acceptance criteria rõ ràng để biết fix thành công:

- T02 score phải giống nhau ở Ranking, Insights, Copilot, Executive Report.
- T01 score phải giống nhau ở Ranking, Insights, Copilot, Executive Report.
- Copilot không được tự tạo điểm mới.
- Copilot phải luôn phân biệt relative rank và absolute safety.
- Nếu trip #1 vẫn CRITICAL, Copilot phải nói rõ #1 không có nghĩa là safe.
- Nếu maintenance telemetry không tồn tại, Copilot không được kết luận xe cần bảo trì.
- Nếu fatigue = 0, Copilot không được khuyên nghỉ vì fatigue.
- Nếu distracted = 0, Copilot không được nói giảm distracted.
- Report phải có score breakdown có thể audit được.
- Report phải có data limitation.
- UI không còn dùng Best Driver nếu best vẫn CRITICAL.

## 16. Files To Modify Later
Dựa trên codebase, liệt kê các file nên sửa ở bước tiếp theo.

Format:
| Priority | File | Reason |
|---|---|---|

## 17. Questions / Missing Context
Liệt kê các câu hỏi còn thiếu nếu codebase chưa đủ thông tin:
- threshold lấy từ đâu?
- scoring formula có phải final không?
- T01/T02 là trip hay vehicle?
- Copilot dùng provider nào?
- report cần tiếng Anh hay tiếng Việt?
- maintenance telemetry có tồn tại không?

Sau khi hoàn thành, tạo file README_AI_COPILOT_CONTEXT.md với nội dung đầy đủ.