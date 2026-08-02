# Decision Engine & Vigilance-Lapse Research Plan

Tài liệu này là kế hoạch cho công đoạn sản phẩm cuối cùng của FPTU DMS Vision:
quyết định **khi nào một tín hiệu AI đủ tin cậy để trở thành cảnh báo**, sau đó
phát sự kiện cho hai luồng tích hợp: Fleet Dashboard và màn hình xe CarSky.

Trạng thái hiện tại: **core policy v1, JSONL integration và FastAPI reference
contract đã triển khai; chưa nối endpoint production của SE/CarSky**.

## 1. Các quyết định đã chốt

1. Decision Engine nằm **sau Challenge 3 / Fusion(2)**.
2. Pipeline CSV của BTC vẫn giữ nguyên; Decision Engine không sửa 5 cột dự
   đoán và không tác động ngược vào điểm Challenge 1–3.
3. Decision Engine sản phẩm được quyền đọc đồng thời:
   - output Challenge 1;
   - output Challenge 2;
   - snapshot Challenge 3;
   - telemetry và trạng thái chất lượng cảm biến.
4. Có hai audience độc lập:
   - `fleet_dashboard`: sự kiện chi tiết để Fleet Manager theo dõi;
   - `driver_display`: cảnh báo ngắn, tức thời cho tài xế qua CarSky.
5. Team AI chỉ sở hữu pipeline suy luận, Decision Engine và canonical
   `DecisionEvent`. Team SE sở hữu FastAPI, OIDC, endpoint mapping, network
   delivery và adapter của Fleet Dashboard/CarSky.
6. “Giấc ngủ trắng” không được thêm thành nhãn CSV thi. Đây là một hướng
   nghiên cứu cảnh báo sản phẩm riêng.
7. Hệ thống dùng `driver_id`, không nhận diện khuôn mặt và không gửi raw cabin
   frame lên dashboard theo mặc định.

## 2. Vị trí trong kiến trúc

```text
Road cameras ──> Challenge 1: TTC ────────┐
                                          ├─> Challenge 3: BTC risk/safe score
Telemetry ────────────────────────────────┘

Face camera ──> Challenge 2: driver state ───────────────┐
Challenge 1: TTC + road quality ─────────────────────────┤
Challenge 3: running risk/safe score ────────────────────┤
Telemetry + sensor quality ──────────────────────────────┤
Optional research signals: lane/gaze/steering/response ──┘
                                                         │
                                                         v
                                                  DECISION ENGINE
                                              quality gate + temporal rules
                                              event state machine + evidence
                                                         │
                                                         v
                                              Canonical DecisionEvent
                                              (AI/SE integration boundary)
                                                         │
                                  ┌──────────────────────┴──────────────────┐
                                  v                                         v
                         audience: driver_display                  audience: fleet_dashboard
                                  │                                         │
                                  └────────────── TEAM SE ──────────────────┘
                                              │                    │
                                              v                    v
                                       CarSky adapter       FastAPI/Fleet adapter
                                              │                    │
                                              v                    v
                                       CarSky truck UI       Fleet Dashboard
```

Challenge 3 hiện tại bám đúng public evaluator BTC: TTC của Challenge 1 cộng
telemetry để tính penalty và safe score; nó **không dùng driver state**.
Decision Engine là lớp sản phẩm phía sau nên có thể kết hợp lại C1, C2 và C3
mà không làm sai contract cuộc thi.

## 3. Decision Engine làm gì?

Decision Engine không chạy lại detector và không tự tạo primitive feature. Nó:

- kiểm tra timestamp và chất lượng từng nguồn;
- tích lũy bằng chứng theo thời gian thay vì quyết định từ một frame;
- áp dụng motion context: đang chạy, tốc độ thấp hay đang dừng;
- nhận biết rủi ro kép, ví dụ TTC thấp đồng thời tài xế mất tập trung;
- chống cảnh báo rung bằng persistence, hysteresis và cooldown;
- gộp các frame liên tiếp thành một event duy nhất;
- nâng/hạ severity và phát sự kiện `open`, `update`, `resolved`;
- lưu reason/evidence để các giao diện giải thích được cảnh báo;
- gắn đúng `audiences` và trả `DecisionEvent` qua integration boundary.

Nó không:

- thay đổi output CSV của BTC;
- dùng safe score tích lũy làm bằng chứng duy nhất cho cảnh báo khẩn cấp;
- quy kết lỗi tài xế khi camera đang mất tín hiệu;
- gửi một request cho mỗi frame;
- tự đăng nhập OIDC hoặc tự gọi API CarSky/Fleet Dashboard;
- lưu hoặc truyền ảnh khuôn mặt nếu chưa có yêu cầu và chính sách riêng.

## 4. Input contract dự kiến

| Nhóm | Tín hiệu hiện đã có | Tín hiệu cần bổ sung/nghiên cứu |
|---|---|---|
| Challenge 1 | `predicted_ttc` | `ttc_confirmed`, collision confidence, road quality |
| Challenge 2 | state, confidence, alertness, eye/mouth/head state, EAR, MAR, PERCLOS, eye-closure duration, off-road duration, quality status | left/right-eye validity, valid-window coverage, gaze vector/dispersion, blink dynamics đã hiệu chỉnh |
| Challenge 3 | running risk/safe score, near-miss và harsh-event counters, speeding percentage | không bắt buộc |
| Telemetry | speed, longitudinal/lateral acceleration, trip timestamp | steering angle/rate, lane offset, yaw rate |
| Context | trip ID, frame ID, driver ID | time-on-task, thời điểm ngày, route monotony |
| HMI | chưa có | prompt ID, acknowledgment, response latency |

Mỗi snapshot đưa vào engine phải có `source_timestamp`, `quality_status` và
model/config version. Signal quá cũ hoặc chất lượng kém phải chuyển thành
`unavailable`, không được tự điền bằng giá trị “an toàn”.

## 5. Chính sách cảnh báo v1 — ngưỡng đã chốt

Đây là **bộ ngưỡng normative v1** để triển khai Decision Engine. Khi code,
mọi giá trị phải nằm trong `configs/decision_engine.yaml`; không tạo thêm
threshold ẩn trong Python.

Các ngưỡng này là policy vận hành của sản phẩm, không phải chứng nhận rằng hệ
thống đã đạt type approval. Sau pilot có thể phát hành `v1.1`, nhưng không
được sửa số trực tiếp trong cùng một version để chạy theo từng trip.

### 5.1 Quy tắc chung

Pipeline hiện chạy khoảng 20 FPS, nhưng Decision Engine phải tính theo
timestamp/millisecond, không đếm cứng số frame.

| Tham số | Giá trị v1 | Ý nghĩa |
|---|---:|---|
| `moving_speed_kmh` | 5 | xe được coi là đang di chuyển |
| `driver_warning_min_speed_kmh` | 20 | ngưỡng bật cảnh báo distraction/drowsiness thông thường |
| `max_source_skew_ms` | 100 | chênh timestamp tối đa giữa các nguồn dùng để fusion |
| `max_realtime_age_ms` | 500 | signal realtime cũ hơn mức này không được dùng để mở event |
| `min_valid_window_ratio` | 0.80 | ít nhất 80% mẫu trong temporal window phải hợp lệ |
| `min_driver_confidence` | 0.70 | confidence tối thiểu cho driver-state model |
| `startup_warmup_sec` | 5 | chưa dùng ML state để cảnh báo trong lúc face pipeline khởi động |
| `perclos_warmup_sec` | 10 | chưa dùng PERCLOS trước khi có tối thiểu 10 giây coverage |

Driver evidence chỉ hợp lệ khi:

```text
quality_status in {valid, valid_profile}
AND state_confidence >= 0.70
AND source age <= 500 ms
AND source skew <= 100 ms
```

`0.70` là operating threshold của Random-Forest `predict_proba`, chưa được
coi là xác suất tuyệt đối cho đến khi chạy probability calibration trên
driver hold-out.

Riêng hard rule continuous-eye-closure không phụ thuộc xác suất Random Forest,
nhưng bắt buộc face, hai mắt và landmark đều hợp lệ. TTC critical không phụ
thuộc cabin quality; lỗi một camera không được vô hiệu hóa camera còn lại.

### 5.2 State machine và thời điểm thực sự gửi event

```text
NORMAL -> WATCH -> WARNING -> CRITICAL -> RECOVERY -> NORMAL
   │          │          │         │
   └──────────┴──────────┴─────────┴──> DEGRADED (signal không đủ tin cậy)
```

| State | Có tạo network event? | Xử lý |
|---|---|---|
| `NORMAL` | Không | tiếp tục quan sát |
| `WATCH` | Không | chỉ ghi shadow/local diagnostic |
| `WARNING` | Có | tạo `open`; audience theo bảng từng rule |
| `CRITICAL` | Có ngay | tạo hoặc nâng cấp event hiện tại |
| `RECOVERY` | Chỉ `update` | chờ ổn định trước khi resolve |
| `DEGRADED` | Chỉ khi kéo dài | tạo `system_health`, không gán lỗi tài xế |

Có hai loại event đi Fleet:

1. **Safety alert:** phải vượt state machine lên WARNING/CRITICAL.
2. **Fleet KPI notification:** phát đúng một lần khi C3 đi qua tier 25/50/75;
   loại này có thể mang severity `info` và không điều khiển CarSky.

Điều kiện gửi Fleet Dashboard chính xác là:

```text
"fleet_dashboard" in event.audiences
AND event passes its source-quality gate
AND (
      decision_level in {WARNING, CRITICAL}
      OR alert_type in {fleet_risk_tier_1,
                        fleet_risk_tier_2,
                        fleet_risk_tier_3}
    )
```

`WATCH` không gửi API. Một single-frame signal yếu không được phát cảnh báo.

### 5.3 Collision/TTC

Áp dụng khi `speed_kmh >= 5`, TTC hữu hạn và đã qua danger confirmation của
Challenge 1. Pipeline C1 hiện đã yêu cầu 8 frame liên tiếp trong band dưới
3 giây trước khi tin TTC nguy hiểm; Decision Engine không chờ thêm đối với
critical event.

| Mức | Điều kiện | Persistence | Audience |
|---|---|---:|---|
| `WATCH` | `3.0 < TTC <= 5.0 s` | 0.5 s | không gửi |
| `WARNING` | `1.5 < TTC <= 3.0 s` | 0.5 s | CarSky + Fleet |
| `CRITICAL` | `TTC <= 1.5 s` | ngay sau C1 confirmation | CarSky + Fleet |

Resolve khi `TTC >= 4.0 s` hoặc không còn collision target liên tục 2 giây.
Cooldown sau resolve là 5 giây. Nếu TTC quay lại vùng critical trong cooldown,
vẫn phải mở episode mới; cooldown không được chặn hard safety event.

`1.5 s` cũng là near-miss boundary của BTC. Mốc warning `3.0 s` nằm trong
vùng cảnh báo va chạm được dùng trong nghiên cứu human factors; nó không phải
lệnh tự động phanh.

### 5.4 Microsleep và continuous eye closure

| Mức | Điều kiện | Audience |
|---|---|---|
| `CRITICAL` khi xe chạy | `speed >= 5 km/h` AND eye closure `>= 1,000 ms` AND both-eye evidence hợp lệ | CarSky + Fleet |
| `WARNING` từ ML-only | state=`microsleep`, confidence `>= 0.80`, kéo dài 2 s nhưng chưa có reliable closure | CarSky + Fleet |
| `WARNING` khi xe dừng | `speed < 5 km/h` AND reliable eye closure `>= 3,000 ms` | CarSky |
| Fleet escalation khi xe dừng | reliable eye closure `>= 10,000 ms` | Fleet + CarSky |

Resolve khi hai mắt mở hợp lệ liên tục 3 giây. Cooldown 30 giây, nhưng một eye
closure mới `>= 1,000 ms` khi xe chạy luôn được phép mở critical episode mới.

Ngưỡng 1,000 ms giữ nguyên production config hiện tại, cao hơn blink thông
thường và thận trọng hơn định nghĩa behavioral microsleep `>500 ms` trong một
số nghiên cứu naturalistic. Không được hạ xuống 500 ms nếu chưa đo lại false
alerts với kính, glare và blink dài.

### 5.5 Distraction/off-road glance

Runtime hiện dùng head yaw/pitch làm proxy cho off-road attention, chưa phải
gaze tracker chuẩn. Vì vậy event phải có face quality hợp lệ và không được mô
tả là đo ánh nhìn chính xác.

| Tốc độ | Điều kiện WARNING | Điều kiện CRITICAL | Audience |
|---:|---|---|---|
| `>= 50 km/h` | off-road liên tục `>= 3.5 s` | `>= 10 s` hoặc đồng thời `TTC <= 3 s` | CarSky + Fleet |
| `20–49.9 km/h` | off-road liên tục `>= 6.0 s` | `>= 10 s` hoặc đồng thời `TTC <= 3 s` | CarSky + Fleet |
| `5–19.9 km/h` | chỉ WATCH | chỉ nâng mức nếu `TTC <= 3 s` | khi compound: CarSky + Fleet |
| `< 5 km/h` | không cảnh báo distraction | không | không gửi |

Một khoảng quay lại nhìn đường dưới 100 ms không reset timer, tránh artefact
và saccade ngắn. Resolve khi on-road liên tục 2 giây. Cooldown 30 giây.

Các mốc `3.5 s @ >=50 km/h` và `6 s @ >=20 km/h` bám warning trigger của EU
ADDW 2023/2590. Vì hệ thống hiện chỉ có head-pose proxy, README không tuyên bố
tuân thủ ADDW cho đến khi có gaze-zone validation.

### 5.6 Drowsiness, PERCLOS và yawning

PERCLOS dùng rolling window 30 giây hiện có. Chỉ kích hoạt khi đã có ít nhất
10 giây dữ liệu và valid coverage `>= 80%`.

| Mức | Một trong các điều kiện | Audience |
|---|---|---|
| `WATCH` | PERCLOS `>= 0.15`; hoặc drowsy confidence `>= 0.65` trong 2 s; hoặc một strong-yawn `>= 2 s` | không gửi |
| `WARNING` | PERCLOS `>= 0.25` trong 3 s; hoặc state=drowsy confidence `>= 0.70` + alertness `<= 0.55` trong 5 s; hoặc 2 strong-yawn/60 s kèm PERCLOS `>=0.15` hoặc alertness `<=0.60` | CarSky + Fleet, nếu speed `>=20` |
| `CRITICAL` | PERCLOS `>= 0.40` trong 3 s; hoặc WARNING tồn tại 15 s; hoặc drowsy đồng thời `TTC <=3 s` | CarSky + Fleet |

Nếu tốc độ dưới 20 km/h, các rule PERCLOS/yawn chỉ giữ `WATCH`; hard eye
closure ở Mục 5.4 vẫn hoạt động từ 5 km/h.

Một lần ngáp đơn lẻ không gửi dashboard. Resolve drowsiness khi đồng thời:

```text
state == alert
AND alertness_score >= 0.65
AND PERCLOS < 0.15
```

duy trì 10 giây. Cooldown 60 giây. Các mức PERCLOS `0.15/0.25/0.40` phản ánh
ba vùng tăng dần được báo cáo trong nghiên cứu; chúng vẫn phải được kiểm tra
theo từng driver vì PERCLOS không có một threshold phổ quát cho mọi camera và
mọi người.

### 5.7 Speeding và harsh behavior

| Rule | Điều kiện | Audience |
|---|---|---|
| speeding warning | `speed > speed_limit + 5 km/h` liên tục 10 s | CarSky + Fleet |
| severe speeding | `speed > speed_limit + 15 km/h` liên tục 5 s | CarSky + Fleet, severity critical |
| repeated harsh behavior | ít nhất 3 episode harsh brake/accel/corner trong 60 s | Fleet warning |

Một harsh episode bắt đầu khi threshold BTC bị vượt ít nhất 100 ms và kết
thúc sau 500 ms trở lại bình thường. Dùng đúng threshold C3 hiện tại:

```text
harsh brake:  longitudinal_accel < -0.40g
harsh accel:  longitudinal_accel >  0.35g
harsh corner: |lateral_accel|    >  0.30g
```

Không gửi hai event cho cùng nguyên nhân: nếu harsh brake nằm trong một TTC
collision episode thì collision event là event chính, harsh brake chỉ nằm
trong `evidence`.

Resolve speeding khi `speed <= speed_limit + 3 km/h` liên tục 5 giây.
Cooldown speeding/harsh behavior là 60 giây.

### 5.8 Challenge 3 risk tier

`predicted_risk_score` là penalty tích lũy, không phải xác suất tai nạn tức
thời. Nó chỉ tạo Fleet KPI event một lần khi **đi lên qua** mỗi mốc:

| Crossing | Event | Audience |
|---:|---|---|
| risk `25` / safe `75` | `fleet_risk_tier_1`, severity info | Fleet |
| risk `50` / safe `50` | `fleet_risk_tier_2`, severity warning | Fleet |
| risk `75` / safe `25` | `fleet_risk_tier_3`, severity warning | Fleet |

Không bao giờ tạo `CRITICAL` chỉ từ C3 risk. C3 là monotonic và có thể tăng
do nhiều frame thuộc cùng một near-miss; critical safety phải đến từ TTC,
driver evidence hoặc compound rule.

### 5.9 Sensor degraded

| Điều kiện | Xử lý |
|---|---|
| face hoặc road signal mất/invalid `>=2 s` khi xe chạy | CarSky system warning |
| mất/invalid `>=10 s` khi xe chạy | Fleet `system_health` + CarSky |
| signal hợp lệ trở lại `>=5 s` | resolve event |

Sensor degraded không được biến thành `drowsy`, `microsleep` hoặc
`distracted`. Cooldown system-health là 60 giây.

### 5.10 Compound-risk escalation

Nâng đúng một severity level khi:

```text
TTC <= 3.0 s
AND driver_state in {drowsy, distracted, microsleep}
AND driver evidence hợp lệ
```

Nếu `TTC <=1.5 s`, kết quả luôn là `CRITICAL`. Compound event đi cả CarSky và
Fleet, dùng một `event_id`; không tạo thêm hai event TTC và driver-state riêng.

### 5.11 Hysteresis, lifecycle và chống spam

```text
NORMAL -> WATCH -> WARNING -> CRITICAL -> RECOVERY -> NORMAL
   │          │          │         │
   └──────────┴──────────┴─────────┴──> DEGRADED (signal không đủ tin cậy)
```

- `open`: phát đúng một lần khi rule đi từ WATCH lên WARNING/CRITICAL.
- `update`: tối đa 1 lần/giây khi evidence thay đổi; escalation gửi ngay.
- `resolved`: chỉ phát sau recovery time riêng của rule.
- Khi event còn mở, không tạo `event_id` mới cho cùng
  `trip_id + alert_type + source_target`.
- Cooldown chỉ chặn event lặp cùng mức; không chặn escalation hoặc hard safety.
- SE retry cùng `event_id` và `idempotency_key`, không sinh event mới.

### 5.12 Ví dụ đọc policy

**Ví dụ A — TTC 2.8 giây:** xe chạy 45 km/h, C1 hợp lệ và TTC ở 2.8 giây
liên tục 0.5 giây. Engine mở `collision_warning`, severity `warning`, gửi cả
CarSky và Fleet. Nếu TTC giảm xuống 1.4 giây, update cùng `event_id` thành
`critical` ngay.

**Ví dụ B — drowsy thoáng qua:** model trả drowsy confidence 0.74 trong 2 giây,
alertness 0.58 và PERCLOS 0.12. Engine chỉ ở WATCH, không gửi API. Nếu state
sau đó cả confidence `>=0.70` và alertness `<=0.55` được giữ đủ 5 giây khi xe
chạy trên 20 km/h, engine mới mở drowsiness warning.

**Ví dụ C — nhắm mắt:** xe chạy 35 km/h, hai mắt/landmark hợp lệ và continuous
closure đạt 1,000 ms. Engine mở microsleep critical ngay, không chờ Random
Forest voting thêm.

**Ví dụ D — camera bị che:** quality chuyển `face_missing`. Trong 2 giây đầu
không được đoán drowsy. Sau 2 giây xe đang chạy, CarSky báo camera; sau 10 giây
Fleet nhận `system_health`. Khi signal hợp lệ lại 5 giây, event được resolve.

**Ví dụ E — C3 risk=50:** Fleet nhận một `fleet_risk_tier_2` warning đúng lúc
risk đi từ dưới 50 lên 50 hoặc cao hơn. CarSky không nhận event này và C3
risk một mình không thể tạo critical alert.

## 6. “Giấc ngủ trắng” được định nghĩa thế nào?

“Giấc ngủ trắng” là cách gọi đời thường và chưa đủ chính xác để làm nhãn y
khoa. Trong hệ thống, tên vận hành đề xuất là:

```text
suspected_vigilance_lapse
```

Nó có nghĩa: **nghi ngờ tài xế tạm thời không xử lý đúng thông tin lái xe dù
mắt có thể vẫn mở**. Nó không đồng nghĩa hoàn toàn với:

- `microsleep`: thường có bằng chứng nhắm mắt hoặc dấu hiệu giấc ngủ rõ hơn;
- `distracted`: chú ý bị chuyển sang điện thoại, bên đường hoặc tác vụ khác;
- `mind_wandering`: chú ý nội tại rời nhiệm vụ nhưng người lái có thể vẫn đáp
  ứng;
- một chẩn đoán y khoa về mất ý thức.

Camera mặt hiện tại có thể nhận ra mắt, đầu và xu hướng hành vi, nhưng **không
thể chứng minh trạng thái nhận thức bên trong**. Vì vậy hệ thống chỉ được phát
`suspected_*`, kèm confidence và evidence; không hiển thị “driver was asleep”
như một kết luận chắc chắn.

## 7. Giả thuyết phát hiện vigilance lapse

Không dùng một threshold đơn. Hướng nghiên cứu là một chuỗi bằng chứng
10–60 giây:

1. **Ocular dynamics:** blink duration/rate thay đổi, PERCLOS trend, gaze trở
   nên cố định hoặc giảm hoạt động quét.
2. **Head dynamics:** giảm head micro-movement, nhìn thẳng bất thường quá lâu,
   phản ứng đầu chậm với thay đổi của đường.
3. **Vehicle control:** steering reversal rate giảm/bất thường, lane offset
   tăng, lane departure, speed control và reaction to hazard xấu đi.
4. **Context:** time-on-task, đường đơn điệu, giờ sinh học và lịch sử fatigue.
5. **Response evidence:** độ trễ hoặc không phản hồi một HMI check an toàn.

Model ONNX 468-landmark hiện tại đủ cho EAR/MAR/head pose nhưng không có bộ
iris landmark chuyên dụng để đo gaze chính xác. Trước khi dùng gaze làm tín
hiệu chính, phải đánh giá một gaze/iris model nhẹ hoặc backend 478-landmark.

### Passive suspicion và active verification

```text
Multimodal time series
        │
        v
passive suspicion score
        │
        ├─ thấp ──> tiếp tục theo dõi
        │
        ├─ vừa + bối cảnh an toàn ──> HMI prompt ngắn
        │                              │
        │                              ├─ phản hồi đúng hạn -> hạ suspicion
        │                              └─ không phản hồi -> tăng evidence
        │
        └─ cao + nhiều nguồn đồng thuận -> warning/critical theo policy
```

Không đưa prompt khi TTC đang critical, xe đang cua/phanh gấp hoặc thao tác
đó có thể làm tài xế phân tâm thêm. Không phản hồi HMI cũng không đủ để kết
luận một mình; nó phải kết hợp với tín hiệu thụ động và sensor quality.

### Research threshold v1 — chỉ shadow mode

Các số dưới đây được chốt để thu log và đánh giá lặp lại được, **không được
gán audience Fleet/CarSky khi chưa qua acceptance gate**:

| Mức shadow | Điều kiện |
|---|---|
| `WATCH` | speed `>=20 km/h`, probability `>=0.70` trong 5 s và có ít nhất 2 nhóm evidence hợp lệ |
| HMI prompt candidate | probability `>=0.80` trong 3 s, TTC `>3 s`, không harsh/corner và HMI chưa prompt trong 5 phút |
| shadow `WARNING` | probability `>=0.85` trong 3 s, không phản hồi HMI trong 3 s và có ít nhất 2 nhóm evidence |
| shadow `CRITICAL` | probability `>=0.90`, không phản hồi HMI và đồng thời có lane/steering anomaly hoặc `TTC <=3 s` |

Một nhóm evidence là một trong: ocular/gaze, head dynamics, vehicle control,
hoặc HMI response. Nhiều feature từ cùng mắt chỉ tính là **một nhóm**, tránh
giả đa nguồn. Reset suspicion khi probability `<0.50` liên tục 10 giây.

Feature flag mặc định:

```text
vigilance_lapse.enabled = false
vigilance_lapse.shadow_only = true
vigilance_lapse.audiences = []
```

Các probability cut-off là research operating points, không phải ngưỡng y
khoa. Chúng chỉ được đổi sau khi calibrate probability trên driver hold-out.

## 8. Chiến lược model

Phiên bản đầu nên là **hybrid**, không phải một model hộp đen quyết định thẳng
việc POST alert:

1. Rule/state machine giữ quyền quyết định cuối cho các hard safety event.
2. Một model time-series chỉ tạo `vigilance_lapse_probability` và confidence.
3. Engine quality-gate, làm mượt và kết hợp probability với context.
4. Chỉ khi model chứng minh tốt hơn baseline trên driver chưa từng thấy mới
   cân nhắc dùng nó để nâng severity.

Các baseline cần so sánh:

- luật thống kê trên rolling window;
- Isolation Forest/One-Class model theo baseline cá nhân cho anomaly;
- gradient boosting trên feature window;
- HMM hoặc Temporal Convolutional Network cho chuỗi thời gian.

Không chọn model theo accuracy frame. Phải chọn theo khả năng bắt **event**
và số cảnh báo giả mỗi giờ.

## 9. Kế hoạch dữ liệu và ground truth

Dataset BTC hiện tại không có nhãn vigilance lapse đáng tin cậy để train trực
tiếp. Cần một protocol nghiên cứu riêng:

1. Thu dữ liệu trong simulator hoặc closed track, có người giám sát an toàn;
   không chủ động gây thiếu ngủ trên đường công cộng.
2. Đồng bộ cabin video, road/lane, steering/telemetry và HMI response.
3. Thu KSS/self-report có kiểm soát, thought probe hoặc reaction task; dùng
   annotator độc lập và giữ nhãn `unknown` khi không chắc.
4. Label taxonomy tối thiểu:
   `alert`, `visual_distraction`, `mind_wandering`,
   `vigilance_lapse_eyes_open`, `drowsy`, `microsleep`,
   `sensor_degraded`, `unknown`.
5. Chia train/test theo **driver**, không chia ngẫu nhiên frame của cùng một
   người sang cả hai tập.
6. Chạy leave-one-driver-out và báo cáo kết quả từng người, ban ngày/ban đêm,
   kính, glare và các chất lượng camera khác nhau.

## 10. Integration boundary: Fleet Dashboard và CarSky

AI không gọi thẳng hai hệ thống đích. Interface mà SE cần nối là output của
Decision Engine:

```text
DecisionEngine.update(snapshot) -> list[DecisionEvent]
```

Mỗi `DecisionEvent` là canonical event dùng chung. Trường `audiences` cho biết
adapter nào phải nhận:

| Audience | Mục đích | Nội dung |
|---|---|---|
| `driver_display` | CarSky/màn hình trên xe | thông điệp rất ngắn, severity, âm thanh/rung, TTL |
| `fleet_dashboard` | quản lý đội xe | lifecycle, confidence, evidence, vị trí và recommended action |

Một critical compound-risk event thường đi cả hai audience. Event thống kê
trip hoặc sensor health có thể chỉ đi Fleet. Cảnh báo trực tiếp cho tài xế phải
ưu tiên latency; cảnh báo Fleet được phép có evidence chi tiết hơn.

Canonical payload tối thiểu do AI tạo:

```json
{
  "schema_version": "1.0",
  "event_id": "uuid",
  "idempotency_key": "trip_id:alert_type:episode_id",
  "trip_id": "T01",
  "driver_id": "driver_001",
  "timestamp_utc": "2026-07-29T10:30:15.250Z",
  "status": "open",
  "alert_type": "suspected_vigilance_lapse",
  "severity": "warning",
  "confidence": 0.82,
  "audiences": ["driver_display", "fleet_dashboard"],
  "driver_message": {
    "message_code": "TAKE_SAFE_BREAK",
    "display_text": "Fatigue risk detected. Stop safely.",
    "audible": true,
    "ttl_ms": 8000
  },
  "evidence": {
    "driver_state": "drowsy",
    "driver_state_confidence": 0.78,
    "predicted_ttc_sec": 4.2,
    "speed_kmh": 62.0,
    "response_latency_ms": 2500,
    "quality_status": "valid"
  },
  "recommended_action": "Contact driver and arrange a safe rest stop",
  "model_versions": {
    "challenge2": "driver_state_rf_v3_onnx",
    "decision_policy": "decision_engine_v1"
  }
}
```

### 10.1 Luồng Fleet Dashboard

Team đã chốt backend dùng FastAPI. Phần SE dự kiến:

```text
DecisionEvent[audience=fleet_dashboard]
  -> SE outbox/queue
  -> HTTP client
  -> FastAPI endpoint do team SE định nghĩa
  -> storage + WebSocket/SSE
  -> Fleet Dashboard
```

FastAPI là server nhận request; HTTP client/adapter của SE mới là thành phần
gửi request. Logic severity và alert type không được viết lại trong FastAPI.

### 10.2 Luồng CarSky

Thông tin tham chiếu được team cung cấp:

```text
Application base:
https://hackathon-1.carsky.io/

Observed OIDC authorization endpoint:
https://hackathon-1.carsky.io/auth/realms/hackathon01/protocol/openid-connect/auth

Observed client_id:
rework
```

URL trên là **OIDC authorization/login endpoint**, không phải endpoint nhận
alert. Các query `state`, `code_challenge`, `redirect_uri` và authorization
code là dữ liệu PKCE theo phiên; không được hard-code hoặc commit nguyên URL
đăng nhập đã cung cấp vào config.

Trước khi tích hợp, team SE phải lấy từ BTC/CarSky:

- API/WebSocket/MQTT endpoint thực sự dùng để đẩy cảnh báo;
- OIDC discovery/token endpoint và client configuration chính thức;
- scope/role cần thiết;
- payload schema, rate limit và quy tắc refresh token;
- cơ chế mapping `driver_id`, `vehicle_id` và CarSky device/session.

Điểm nối của SE:

```text
DecisionEvent[audience=driver_display]
  -> CarSky adapter do SE triển khai
  -> map driver_message sang contract CarSky
  -> authenticate/refresh token
  -> CarSky truck display
```

### 10.3 Ranh giới trách nhiệm

| Hạng mục | AI | SE |
|---|:---:|:---:|
| C1/C2/C3 inference | ✓ | |
| temporal policy, severity, confidence | ✓ | |
| canonical `DecisionEvent` + audiences | ✓ | |
| message code và recommended action | ✓ | phối hợp UX |
| FastAPI reference contract/client | ✓ | phối hợp |
| FastAPI production/database/WebSocket | | ✓ |
| Fleet/CarSky payload mapping | | ✓ |
| OIDC/PKCE/token/secret | | ✓ |
| outbox, retry, timeout, circuit breaker | | ✓ |
| monitoring network delivery | | ✓ |

Yêu cầu chung cho SE adapter:

- mất mạng không được chặn hoặc làm giảm FPS của AI;
- idempotency để retry không sinh event trùng;
- không gửi `NaN`/`Infinity`;
- giữ UTC timestamp, schema/model version và `event_id`;
- raw image/video tắt mặc định;
- secrets/token không nằm trong repo AI.

## 11. Cấu trúc code hiện tại

```text
AI/
├── core/
│   └── decision_engine/
│       ├── __init__.py
│       ├── README.md
│       ├── schemas.py
│       ├── policy.py
│       └── engine.py
├── configs/
│   └── decision_engine.yaml
├── integrations/
│   └── se_client.py
├── services/
│   └── se_reference_api.py
└── scripts/
    ├── run_inference.py
    ├── serve_se_reference_api.py
    └── send_decision_events.py
```

`core/decision_engine` không được import FastAPI/httpx. Core phải test được
offline. `integrations/se_client.py` là client contract để AI/SE thử nghiệm;
`services/se_reference_api.py` là receiver in-memory, không thay thế backend
production do team SE quản lý.

### 11.1 Cách chạy hiện tại

Sinh CSV BTC và canonical DecisionEvent trong hai folder tách biệt:

```powershell
python AI\scripts\run_inference.py `
  --data-dir <BTC_DATA_DIR> `
  --samples-only `
  --out AI\artifacts\predictions `
  --decision-events-dir AI\artifacts\decision_events `
  --driver-id driver_001
```

Khởi động FastAPI reference contract cho SE:

```powershell
python AI\scripts\serve_se_reference_api.py --host 127.0.0.1 --port 8000
```

Swagger/OpenAPI nằm tại `http://127.0.0.1:8000/docs`. Endpoint nhận event:

```text
POST /api/v1/alerts
Idempotency-Key: <khớp idempotency_key trong payload>
```

Gửi lại một file JSONL để contract-test:

```powershell
python AI\scripts\send_decision_events.py `
  --events AI\artifacts\decision_events\T01-Sample.events.jsonl `
  --endpoint http://127.0.0.1:8000/api/v1/alerts
```

Client đọc optional secrets từ `FPTU_SE_API_KEY` hoặc
`FPTU_SE_BEARER_TOKEN`. Không truyền secret qua CLI và không commit `.env`.

## 12. Roadmap triển khai

### Phase 0 — Chốt contract và safety policy

- đóng băng input/output schema;
- chốt severity, CarSky alert UX và timeout/cooldown;
- viết hazard analysis và các case TTC, microsleep, degraded signal;
- bàn giao canonical event schema cho SE;
- xác nhận Fleet API và CarSky ingestion/auth contract.

**Done khi:** replay một snapshot giả có thể tạo deterministic event JSON.

### Phase 1 — Decision Engine baseline ở shadow mode

- viết schemas, quality gate, state machine và config;
- nối read-only vào unified pipeline sau Challenge 3;
- ghi canonical event local, chưa gọi Fleet hoặc CarSky;
- replay trip để kiểm tra event, duplicate và timestamp.

**Done khi:** bật/tắt engine cho CSV Challenge 1–3 giống hệt nhau.

### Phase 2 — Bàn giao integration contract cho SE

- AI cung cấp fixture event cho từng severity/audience/lifecycle;
- SE triển khai FastAPI/Fleet adapter và CarSky adapter;
- hai team chạy contract test với event `open`, `update`, `resolved`;
- SE mô phỏng timeout, mất mạng, retry, duplicate và token expiry.

**Done khi:** cả hai giao diện nhận đúng event và lỗi kết nối không làm giảm
FPS hoặc thay đổi kết quả inference.

### Phase 3 — Vigilance-lapse dataset

- bổ sung logging cho gaze/lane/steering/HMI nếu được chọn;
- chạy protocol simulator/closed track;
- xây label guideline và kiểm tra độ đồng thuận annotator.

**Done khi:** có dataset versioned và test set theo driver.

### Phase 4 — Model nghiên cứu

- đo rule baseline;
- thử model time-series/anomaly;
- calibrate probability và ablation từng nguồn;
- chạy shadow mode trên dữ liệu chưa thấy.

**Done khi:** model vượt baseline về event recall mà vẫn đạt giới hạn false
alerts/hour đã chốt.

### Phase 5 — Pilot có kiểm soát

- bật HMI verification trước, Fleet alert sau;
- rollout theo feature flag;
- theo dõi alert load, acknowledgment và sensor availability;
- có kill switch và rollback về deterministic policy.

## 13. Đánh giá và acceptance gates

Metrics chính:

- event recall/precision, không chỉ frame accuracy;
- false alerts per driving hour;
- time-to-alert từ lúc event bắt đầu;
- critical-event miss rate;
- duplicate event rate;
- alert acknowledgment và response latency;
- phần trăm thời gian monitoring khả dụng;
- p95 latency của engine và API delivery success rate;
- kết quả theo từng driver và điều kiện ánh sáng.

Không được bật production alert nếu chưa đạt các gate:

1. Challenge 1–3 và CSV không thay đổi khi bật Decision Engine.
2. Fleet/CarSky outage không chặn inference.
3. Một episode chỉ có một `event_id`; retry không tạo bản ghi trùng.
4. `sensor_degraded` không bị biến thành lỗi của tài xế.
5. White-sleep/vigilance-lapse feature mặc định ở shadow mode cho đến khi có
   ground truth và false-alert gate.
6. Dashboard luôn hiển thị “suspected” và evidence, không đưa kết luận y khoa.
7. Không gửi dữ liệu sinh trắc học hoặc raw frame ngoài policy đã duyệt.

Numerical gates cho deterministic Decision Engine v1:

| Metric | Gate tối thiểu |
|---|---:|
| critical event recall | `>=95%` trên labeled replay set |
| warning event recall | `>=90%` |
| false critical alerts | `<=0.02 / driver-hour` |
| false warning alerts | `<=0.20 / driver-hour` |
| duplicate event | `0` |
| p95 Decision Engine processing | `<=10 ms/snapshot` trên target hardware |
| CSV difference khi engine bật/tắt | `0 row` |

Gate riêng trước khi bật `suspected_vigilance_lapse` ra network:

- test set tách theo driver và chưa từng dùng để tune threshold;
- event recall `>=85%`;
- false warning `<=0.10/driver-hour`;
- false critical `<=0.01/driver-hour`;
- probability đã được calibration và báo cáo reliability curve;
- có xác nhận HMI không làm tăng distraction;
- có kill switch và ít nhất một pilot shadow hoàn chỉnh.

## 14. Các câu hỏi team phải chốt trước khi code

1. Fleet Dashboard cung cấp endpoint nào, auth gì và ai sở hữu backend?
2. Cảnh báo nào đi CarSky, cảnh báo nào đi Fleet, cảnh báo nào đi cả hai?
3. Fleet có cần acknowledgment từ manager và lifecycle `resolved` không?
4. Xe có steering angle, lane offset hoặc yaw-rate thật không?
5. HMI verification dùng nút, giọng nói hay thao tác vô-lăng?
6. Event/evidence được lưu bao lâu và ai có quyền xem?
7. CarSky cung cấp ingestion endpoint/protocol nào ngoài trang OIDC login?

## 15. Tài liệu tham khảo nghiên cứu

- [EU Driver Drowsiness and Attention Warning regulation](https://eur-lex.europa.eu/eli/reg_del/2021/1341/oj/eng):
  dùng KSS 8 làm mức phải cảnh báo và yêu cầu validation với người tham gia;
  không có ánh xạ trực tiếp từ KSS sang Random-Forest confidence.
- [EU Advanced Driver Distraction Warning regulation](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32023R2590):
  trigger off-road gaze 3.5 giây từ 50 km/h và 6 giây từ 20 km/h; đây là cơ
  sở cho Mục 5.5, nhưng head-pose proxy hiện tại chưa đủ để tuyên bố compliance.
- [NHTSA human-factors guidance for collision warning timing](https://rosap.ntl.bts.gov/view/dot/2613/dot_2613_DS1.pdf):
  mô tả cautionary TTC trong vùng 3–5 giây và imminent TTC khoảng 1.5–2 giây.
- [NHTSA assessment of vehicle-based drowsy-driver detection](https://www.nhtsa.gov/sites/nhtsa.dot.gov/files/811886-assess_veh-based_sensors_4_drowsy-driving_detection.pdf):
  tổng hợp ocular, vehicle-performance và driver-based approaches.
- [Naturalistic study of ocular measures and behavioral microsleeps](https://pubmed.ncbi.nlm.nih.gov/31805427/):
  dùng blink trên 500 ms làm behavioral microsleep và cho thấy ocular measures
  có giá trị nhưng không phải phép đo field tuyệt đối.
- [Review/table of reported PERCLOS operating thresholds](https://pmc.ncbi.nlm.nih.gov/articles/PMC7435375/):
  cho thấy threshold thay đổi theo window/FPS; hỗ trợ dùng nhiều tier và bắt
  buộc validation thay vì coi một số là chuẩn phổ quát.
- [PVT lapses differ with eyes open, closed, or looking away](https://pubmed.ncbi.nlm.nih.gov/20175403/):
  bằng chứng rằng response lapse không phải lúc nào cũng đi kèm nhắm mắt.
- [Detecting and Quantifying Mind Wandering during Simulated Driving](https://pmc.ncbi.nlm.nih.gov/articles/PMC5550411/):
  nghiên cứu simulator kết hợp self-report, driving behavior và EEG.
- [NHTSA drowsy-driving guidance](https://www.nhtsa.gov/risky-driving/drowsy-driving):
  bối cảnh an toàn và mức nguy hiểm của microsleep khi lái xe.
