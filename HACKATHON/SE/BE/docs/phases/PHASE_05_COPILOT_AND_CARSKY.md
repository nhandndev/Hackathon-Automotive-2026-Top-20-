# Phase 05 — AI Copilot và CarSky HMI

Hướng dẫn thao tác end-to-end để đưa signal lên màn hình thật: [Phase 05.1 — CarSky HMI Runbook](PHASE_05_1_CARSKY_HMI_RUNBOOK.md).

Checklist chỉ gồm thao tác và lệnh thực hiện: [Phase 05.2 — CarSky HMI từ đầu đến cuối](PHASE_05_2_CARSKY_HMI_ACTION_CHECKLIST.md).

## Mục tiêu

Cung cấp trợ lý tiếng Việt dựa trên dữ liệu fleet và truyền critical alert xuống CarSky HMI, đồng thời bảo đảm demo vẫn chạy khi mất mạng hoặc thiếu credential.

Lưu ý: API LLM/Copilot ở phase này khác với API mô hình AI tạo `ego/driver/TTC/risk`. API mô hình AI được tích hợp tại Phase 02.

## A. AI Copilot

### Quyết định provider

- MVP mặc định `LLM_PROVIDER=none`: deterministic fallback luôn hoạt động và là đường demo bắt buộc.
- Tích hợp online dùng `LLM_PROVIDER=openai_compatible`, gọi `{LLM_BASE_URL}/chat/completions` với Bearer key.
- Model lấy từ `LLM_MODEL`; temperature `0.2`, `max_tokens=800`, timeout 2,5 giây.
- Mỗi request độc lập, không lưu conversation history hoặc dữ liệu cá nhân.
- LLM chỉ nhận aggregate/evidence cần thiết, không nhận toàn bộ 1.800 frame.
- Yêu cầu output JSON `{answer,action_buttons}`; parse lỗi chuyển fallback.
- Action IDs whitelist: `view_trip`, `compare_trip`, `view_events`, `recommend_break`; action khác bị loại.

### Endpoint

`POST /api/v1/coaching/chat`

Request:

```json
{"query":"Tài xế nào có rủi ro cao nhất?", "trip_id":null}
```

Response:

```json
{
  "answer":"T01d có Safe Score thấp nhất...",
  "source":"fallback|llm",
  "action_buttons":[{"label":"Xem chuyến T01d","action_id":"view_trip","payload":{"trip_id":"T01d"}}],
  "response_time_ms":42
}
```

### Công việc

- [ ] Thay request hiện tại bằng query contract; giữ `/api/coaching/generate` làm alias deprecated đến hết hackathon.
- [ ] Tạo intent fallback cho: tài xế rủi ro nhất, vi ngủ nhiều nhất, so sánh hai trip, tóm tắt trip và khuyến nghị nghỉ.
- [ ] Context chỉ lấy từ output AI đã cache (`metadata`, `ego`, `driver`, TTC/headway, flags, risk), không cho LLM tự tạo hoặc sửa số liệu.
- [ ] Khi có API key, gọi provider thật bằng async client, timeout dưới 2,5 giây.
- [ ] Validate/truncate output và không log secret.
- [ ] Khi provider lỗi/timeout, trả fallback ngay và `source=fallback`.
- [ ] Không dùng mutable default cho action buttons/top violations.

Fallback intent precedence: compare → specific trip summary → most risky → most microsleep → break recommendation → generic help. Query không match trả danh sách câu hỏi được hỗ trợ, không bịa dữ liệu.

## B. Risk reasoning

- [ ] Template deterministic cho normal, warning và critical.
- [ ] Reasoning nêu evidence: state, TTC, speed, accel và event liên quan.
- [ ] Recommended action theo severity.
- [ ] LLM chỉ cải thiện cách diễn đạt; evidence và `risk.final_risk_score` luôn lấy nguyên gốc từ AI. `reasoning.severity` là nhãn hiển thị do Backend dẫn xuất và phải nằm trong enrichment.

## C. CarSky adapter

Nguồn kỹ thuật chính thức của phase: `carsky/carsky-guideline-web 3/index.html`, các mục **AI Integration & Device Control**, **REST API Endpoint Reference**, **Credentials**, **Signals**, **Nydus/Blueprint**, **KUKSA/VSS Script Node**, **Screen Widget**, **Signal Watch**, **GPIO Panel** và **Text-to-Speech Widget**.

### Kết luận bắt buộc rút ra từ CarSky guide

CarSky cung cấp hạ tầng để deploy node, truyền signal và quan sát/điều khiển VM; guide **không cung cấp sẵn một Driver Safety HMI hoàn chỉnh**. Phase này phải tách bốn trách nhiệm:

| Thành phần | Trách nhiệm đúng | Không được hiểu nhầm |
|---|---|---|
| Backend REST adapter | Gửi giá trị signal vào đúng Room/Signal node | Không trực tiếp vẽ UI hoặc phát âm thanh trên màn hình |
| KUKSA/Signal + Script Node | Nhận signal, subscribe, map/chuẩn hóa lifecycle cảnh báo | Không phải màn hình dành cho tài xế |
| Skycraft Android app hoặc custom HMI app | Render Normal/Warning/Critical, phát tone và xử lý recovery | Không được CarSky tự sinh chỉ từ signal payload |
| Workbench Widgets | Quan sát, debug và thao tác trong lúc tích hợp | Không thay thế production HMI |

Vai trò widget theo guide:

- **Signal Watch** chỉ đọc/quan sát VSS hoặc CAN signals đã khai báo; dùng để xác minh, không dùng làm Driver HMI.
- **GPIO Panel** ghi giá trị vào source signal để giả lập sensor/input; không phải đầu ra cảnh báo.
- **Screen Widget** hiển thị màn hình của VM/app đang chạy; muốn có UI cảnh báo thì team vẫn phải cài/chạy HMI app trong Skycraft Android VM.
- **Text-to-Speech Widget** tổng hợp giọng nói theo yêu cầu và phát qua part `a8/audio-play`. Nếu Blueprint không có audio playback part thì nút Play bị vô hiệu. Guide hiện chỉ xác nhận các voice Trung (Đài Loan) và Anh (Mỹ), vì vậy không được cam kết TTS tiếng Việt bằng widget này.
- Các REST route VM như `/text`, `/tap`, `/key`, `/shell` là công cụ điều khiển/debug Android, không phải signal bus và không phải kiến trúc cảnh báo chính.

### Kiến trúc kết nối đã chọn

```text
AI frame đã validate/cache
        ↓
Backend phát hiện critical episode bắt đầu/kết thúc
        ↓
CarSky background queue + async adapter
        ↓
POST /api/v1/signals/{roomId}/{nodeKey}/actuate
        ↓
KUKSA/Signal node trong CarSky Room
        ↓
Script Node subscribe/map signal (nếu Blueprint cần bridge)
        ↓
Skycraft Android/custom HMI app nhận trạng thái
        ↓
Hiển thị cảnh báo đỏ + thông tin TTC/risk + âm thanh
```

Backend sử dụng **REST Signals API** làm kênh dữ liệu chính. Các endpoint VM `/text`, `/tap`, `/key` và `/shell` chỉ phục vụ kiểm tra/điều khiển Android, không được dùng thay cho signal bus của HMI.

### Configuration

- `CARSKY_ENABLED`
- `CARSKY_MODE=external|offline`
- `CARSKY_BASE_URL`, ví dụ `https://carsky.io`
- `CARSKY_API_KEY`
- `CARSKY_ROOM_ID`
- `CARSKY_NODE_KEY`
- `CARSKY_TIMEOUT_SEC`
- `CARSKY_AUTH_MODE=x-api-key|bearer`

Không commit credential. Header tương ứng:

```http
X-API-Key: <carsky_api_key>
```

hoặc:

```http
Authorization: Bearer <carsky_api_key>
```

### Chuẩn bị trên CarSky Workbench

- [ ] Đăng nhập Rework UI, mở **Settings → Credentials → New credential**, sao chép key vì key chỉ hiển thị một lần.
- [ ] Trong Nydus, tạo/import Blueprint tối thiểu có KUKSA Broker/Signal node, Script Node khi cần mapper/bridge và Skycraft Android/custom HMI consumer.
- [ ] Với Script Node, dùng KUKSA pin (`pins.kuksa`); Zenoh chỉ được inject qua Ethernet Bridge khi có edge Ethernet tương ứng, **không tạo một pin loại Zenoh**.
- [ ] Nối pin/edge theo đúng pin contract của từng node để Script/HMI consumer nhận được signal; không suy đoán tên pin nếu Blueprint thật chưa xác nhận.
- [ ] Khai báo các VSS path dự án dùng cho driver state, alertness, TTC, risk và critical alert; path phải tồn tại trong artifact/schema VSS trước khi actuate.
- [ ] Deploy Blueprint và chờ Room cùng các node ở trạng thái Running.
- [ ] Lấy `roomId` là ID của device/room đã deploy.
- [ ] Lấy `nodeKey` là ID node nguồn signal trong Blueprint, không mặc định dùng node màn hình Android.

Luồng triển khai Blueprint được chốt:

```text
KUKSA Broker/Signal Node
        ↕ KUKSA pin/edge
Script Node (subscribe + map lifecycle, tùy kiến trúc)
        ↕ integration edge do HMI app hỗ trợ
Skycraft Android/custom HMI runtime
        ↓
Screen Widget chỉ phản chiếu UI để demo/kiểm tra
```

Nếu HMI app có thể subscribe KUKSA trực tiếp thì Script Node có thể bỏ. Nếu app không thể subscribe trực tiếp, Script Node/container bridge là bắt buộc. Quyết định này cần HMI team xác nhận bằng pin contract và runtime thật; AI Agent không được tự bịa giao thức giữa Script Node và app.

Script Node API được guide xác nhận:

```lua
pins.kuksa:subscribe({
  "Vehicle.Driver.State",
  "Vehicle.ADAS.MinTTC",
  "Vehicle.ADAS.CriticalAlert"
})

pins.kuksa:on_change(function(ev)
  print(ev.path, ev.value)
  -- Map signal thành HMI state hoặc chuyển tiếp cho HMI consumer.
end)
```

Guide còn hỗ trợ `publish`, `actuate`, `get` và dot-tree API. Backend v1 vẫn dùng public REST `/actuate`; trước demo phải kiểm tra hành vi thực tế bằng OpenAPI/runtime. Nếu KUKSA artifact xem dữ liệu AI là sensor value cần `publish`, dùng Script Node làm bridge `on_actuate → publish` thay vì đổi giao thức theo phỏng đoán.

### Khám phá `roomId` và `nodeKey`

Khi `CARSKY_ROOM_ID` hoặc `CARSKY_NODE_KEY` thiếu, startup validation dùng các endpoint sau để discovery:

```http
GET /api/v1/devices
GET /api/v1/deployments/find?device=<device_name>
GET /api/v1/deployments/{roomId}/nodes
GET /api/v1/signals/{roomId}
GET /api/v1/signals/{roomId}/{nodeKey}
```

Backend chỉ tự điền khi discovery trả đúng một room và đúng một signal node có đủ năm VSS paths. Nếu có 0 hoặc nhiều kết quả, readiness `carsky=degraded` và yêu cầu cấu hình ID rõ ràng; không tự chọn phần tử đầu tiên.

### Endpoint ghi và đọc signal

Gửi giá trị:

```http
POST /api/v1/signals/{roomId}/{nodeKey}/actuate
Content-Type: application/json
X-API-Key: <key>
```

Đọc lại để xác minh:

```http
POST /api/v1/signals/{roomId}/{nodeKey}/values
```

Theo dõi thay đổi bằng SSE:

```http
GET /api/v1/signals/{roomId}/{nodeKey}/subscribe
```

Payload actuate:

```json
{
  "signals": [
    {"path": "Vehicle.Driver.State", "value": "microsleep"},
    {"path": "Vehicle.Driver.AlertnessScore", "value": 0.15},
    {"path": "Vehicle.ADAS.MinTTC", "value": 1.0},
    {"path": "Vehicle.ADAS.FinalRiskScore", "value": 88.0},
    {"path": "Vehicle.ADAS.CriticalAlert", "value": true}
  ]
}
```

Tên VSS path trên là contract đề xuất của dự án; phải được đưa vào VSS artifact/Blueprint và kiểm tra bằng API liệt kê signal trước khi sử dụng.

Trước khi viết client cố định, mở OpenAPI của đúng environment để xác nhận schema và status code:

```text
https://<carsky-domain>/api/v1/openapi.json
https://<carsky-domain>/api/v1/docs
```

### Vòng đời cảnh báo

- Khi critical episode bắt đầu: actuate evidence mới nhất và `CriticalAlert=true` đúng một lần.
- Trong episode: không gửi lặp ở 20 FPS; chỉ cập nhật nếu HMI cần telemetry định kỳ với rate được cấu hình riêng.
- Khi episode kết thúc: actuate `CriticalAlert=false` để HMI tắt đèn/còi; cập nhật driver state/TTC/risk cuối.
- Deduplicate bằng `trip_id + episode_id + transition(start|end)`.
- Backend reasoning dài không đẩy trực tiếp qua signal nếu schema VSS không hỗ trợ chuỗi; HMI tự map signal sang câu cảnh báo, hoặc dùng một application-level channel đã được Blueprint định nghĩa.

CarSky implementation decision v1:

- Backend integration bắt buộc dừng ở Signals API; Agent không tự động tạo/xóa Blueprint hoặc Deployment.
- Blueprint prerequisite được team tạo trên Workbench: một KUKSA/signal source node và một HMI consumer node.
- Năm VSS paths trong payload là contract v1 và phải được thêm vào VSS artifact trước demo.
- HMI consumer chịu trách nhiệm map `CriticalAlert=true` thành viền đỏ/còi; Backend không gọi `/shell` để giả lập UI.
- Queue size 100, một worker, request timeout 1,5 giây, tối đa 2 retry (250/500 ms) cho 429/5xx/network error.
- Queue đầy: loại telemetry update cũ nhất trước; transition `start/end` không bao giờ bị drop. Nếu queue chỉ còn transition, producer chờ tối đa 100 ms rồi đánh dấu delivery degraded.

### Công việc

- [ ] Tạo async `carsky_adapter.py` với REST Signals client và payload mapper riêng.
- [ ] Tạo `CarSkySignalMap` cấu hình AI field → VSS path; không hard-code rải rác.
- [ ] Thêm startup validation: credential, room, node và danh sách VSS path cần thiết.
- [ ] Chỉ enqueue alert khi critical episode bắt đầu.
- [ ] Enqueue reset khi critical episode kết thúc.
- [ ] Gửi qua background task/queue; replay không chờ HTTP response.
- [ ] Timeout ngắn, retry giới hạn và không retry lỗi 4xx vô hạn.
- [ ] Có offline/mock adapter trả delivery status để demo không cần mạng.
- [ ] Deduplicate theo `trip_id + episode_id`.
- [ ] Log status code/duration nhưng che API key.
- [ ] Phân loại lỗi: 401/403 credential/quyền, 404 room/node/path, 422 payload, 429 rate limit, 5xx/transient.
- [ ] Bổ sung readiness component `carsky` với `ready|degraded|offline`.

### API kiểm tra Android HMI

Sau khi gửi signal, checklist demo bắt buộc gọi screenshot; accessibility là kiểm tra bổ sung:

```http
GET /api/v1/vms/{roomId}/{androidNodeKey}/screenshot
GET /api/v1/vms/{roomId}/{androidNodeKey}/accessibility
```

Touch routes `/tap` và `/swipe` chỉ hoạt động khi hệ thống CarSky có `COOLGATE_URL_SERVER`. Demo cảnh báo không được phụ thuộc vào touch route.

### Trình tự tích hợp thật và tiêu chí qua cổng

1. Tạo credential và lưu secret ngoài Git.
2. Import VSS artifact chứa toàn bộ custom path và đúng data type.
3. Tạo Blueprint, nối KUKSA/Script/HMI/audio parts theo pin contract thật.
4. Deploy Blueprint, đợi Room và node ở trạng thái Running.
5. Discover `roomId`, signal `nodeKey`, Android `nodeKey`; lưu tách biệt.
6. Gọi API list signals; thiếu bất kỳ path bắt buộc nào thì dừng integration và báo `degraded`.
7. Actuate một fixture Warning/Critical/Reset, đọc lại qua `/values` hoặc SSE.
8. Mở Signal Watch để đối chiếu giá trị; đây chỉ là bước debug.
9. Mở Screen Widget hoặc gọi screenshot để xác minh HMI app thực sự đổi trạng thái.
10. Nếu dùng TTS/audio, kiểm tra có `a8/audio-play`; nếu thiếu thì dùng tone do HMI app phát hoặc chạy demo không giọng nói.

Một scenario chỉ được coi là pass khi cả **signal value** và **UI output** đúng. HTTP 2xx đơn lẻ chưa chứng minh HMI đã hiển thị.

## D. Thiết kế CarSky HMI dành cho tài xế

### Mục tiêu trải nghiệm

CarSky HMI là màn hình dành cho **người đang lái xe**, không phải Fleet Dashboard thu nhỏ. Tài xế phải hiểu tình huống và hành động cần làm trong tối đa khoảng 2 giây nhìn lướt. HMI ưu tiên:

1. **Tôi có đang an toàn không?**
2. **Nguy hiểm gì đang xảy ra?**
3. **Tôi cần làm gì ngay bây giờ?**

Các phân tích dài, leaderboard, biểu đồ, tên tài xế khác, SHAP/risk breakdown và lịch sử chi tiết chỉ dành cho Fleet Manager; không hiển thị khi xe đang chạy.

### Phân cấp dữ liệu hiển thị

| Dữ liệu nguồn | Có hiển thị cho tài xế? | Cách hiển thị | Khi nào |
|---|---|---|---|
| `ego.speed_kmh` | Có, luôn | Số lớn `km/h` | Normal/Warning/Critical |
| `metadata.speed_limit_kmh` | Có, luôn | Biển giới hạn nhỏ cạnh tốc độ | Luôn |
| `driver.state` | Có chọn lọc | Icon + nhãn ngắn: Tỉnh táo/Buồn ngủ/Mất tập trung/Vi ngủ | Chỉ nổi bật khi khác `alert` |
| `driver.alertness_score` | Không hiện số thập phân | Thanh năng lượng/tỉnh táo 0–100% | Normal hiển thị nhẹ; warning nổi bật |
| `min_ttc` | Có điều kiện | `TTC 1.2s` hoặc vòng countdown | Chỉ khi TTC hữu hạn và ≤ 3 giây |
| `headway_sec` | Có điều kiện | Khoảng cách theo xe: Tốt/Gần/Quá gần | Warning khi ≤ 2 giây |
| `behavior_flags.speeding` | Có | Icon biển tốc độ + “Giảm tốc” | Khi true |
| `behavior_flags.tailgating` | Có | Icon hai xe + “Tăng khoảng cách” | Khi true |
| `harsh_brake/accel/corner` | Có nhưng không chen cảnh báo chính | Chip nhỏ hoặc coaching sau sự kiện | Sau khi tình huống ổn định |
| `risk.final_risk_score` | Không hiện số 0–100 khi đang lái | Chuyển thành màu/trạng thái tổng hợp | Luôn, nhưng số chi tiết chỉ ở màn hình dừng xe |
| `base_risk`, `driver_factor` | Không | Chỉ dùng Fleet Dashboard | Không hiển thị trên HMI |
| `nthu_subject_id` | Không | Dữ liệu nội bộ | Không hiển thị |
| GPS lat/lon/alt | Không ở HUD cảnh báo | Chỉ dùng navigation/map nếu có | Không chen vào cảnh báo |

### Ba trạng thái màn hình

#### 1. NORMAL — “Calm Mode”

- Nền tối, ít chuyển động để không gây xao nhãng.
- Tốc độ là phần tử lớn nhất; speed limit nằm kế bên.
- Một vòng **Safety Halo** xanh bao quanh tốc độ, thể hiện trạng thái tổng hợp.
- Driver state mặc định chỉ là icon nhỏ “Tỉnh táo”.
- Không hiển thị TTC nếu là Infinity; không hiển thị risk score.
- Coaching không tự bật pop-up khi xe đang chạy bình thường.

#### 2. WARNING — “Nudge Mode”

- Safety Halo chuyển vàng/cam, pulse chậm đúng 2 lần rồi đứng yên.
- Chỉ hiện **một nguyên nhân ưu tiên cao nhất** và một hành động:
  - `drowsy` → “Bạn đang buồn ngủ” / “Tìm điểm dừng nghỉ”.
  - `distracted` → “Tập trung phía trước”.
  - `tailgating` → “Tăng khoảng cách”.
  - `speeding` → “Giảm về 80 km/h”.
  - TTC ≤ 2,5s → “Xe phía trước quá gần”.
- Âm thanh nhẹ một lần; không còi lặp liên tục.
- Các warning khác xếp vào hàng chip nhỏ để tránh nhiều pop-up chồng nhau.

#### 3. CRITICAL — “Act Now Mode”

- Toàn màn hình có viền đỏ và Safety Halo đỏ; không che tốc độ hiện tại.
- Nội dung tối đa hai dòng:

```text
NGUY CƠ VA CHẠM — TTC 1.2s
PHANH AN TOÀN • GIỮ THẲNG LÁI
```

- Vi ngủ:

```text
PHÁT HIỆN VI NGỦ
GIẢM TỐC • DỪNG NGHỈ AN TOÀN
```

- Phát alarm theo pattern ngắn do HMI/audio team duyệt; ví dụ 200ms bật/200ms tắt × 3, không phát vô hạn. Tần số và âm lượng không hard-code trước khi test trên thiết bị thật.
- Cảnh báo giữ đến khi Backend gửi `CriticalAlert=false`, sau đó chuyển sang recovery thay vì tắt đột ngột.

Âm thanh critical phải do HMI app hoặc audio consumer trong Blueprint phát từ reason/severity signal. Built-in Text-to-Speech Widget chỉ là lựa chọn demo bổ sung khi có `a8/audio-play`; không nằm trên critical path, không được giả định có tiếng Việt và không được để lỗi TTS ngăn cảnh báo hình ảnh.

### AI status và trợ lý giọng nói

Góc trên HMI hiển thị một status chip duy nhất:

```text
● AI ONLINE      🔊 VOICE ON
```

Ý nghĩa status:

- `AI ONLINE`: frame AI hợp lệ vẫn đang cập nhật trong freshness threshold.
- `AI DEGRADED`: AI/API ngoài lỗi nhưng Backend đang dùng dữ liệu cache hoặc safety rules dự phòng.
- `AI OFFLINE`: không còn dữ liệu AI đủ mới; HMI không được trình bày dữ liệu cũ như dữ liệu live.

`AI ONLINE` không đồng nghĩa LLM hoặc TTS đang online. Backend dẫn xuất status từ trạng thái AI source và tuổi của frame; HMI chỉ render enum, không tự suy đoán từ kết nối mạng.

Voice flow được chốt:

```text
AI frame → deterministic reason/action code → phrase catalog trong HMI
→ Android TTS tiếng Việt hoặc pre-recorded audio → loa
```

- Không gọi LLM để sinh câu nói trong critical path.
- Không gửi từng frame sang TTS; chỉ phát theo episode transition.
- `VOICE OFF/MUTED` tắt lời nói warning/coaching, nhưng critical vẫn giữ visual alert và một safety tone ngắn.
- Warning đọc một lần rồi cooldown 10–15 giây; chỉ đọc lại nếu reason/severity thay đổi hoặc nguy cơ xấu hơn.
- Critical ngắt warning đang đọc và có quyền vượt cooldown.
- Recovery chỉ đọc một lần: “Đã trở lại vùng an toàn”.
- TTS lỗi/timeout chuyển sang pre-recorded audio hoặc tone; không chặn state transition của HMI.
- LLM voice tự do chỉ được dùng cho coaching khi xe đã dừng.

Phrase catalog v1:

| Reason/action | Câu tiếng Việt |
|---|---|
| `TTC_CRITICAL/BRAKE_SAFE` | “Nguy cơ va chạm. Hãy phanh an toàn.” |
| `MICROSLEEP/STOP_AND_REST` | “Phát hiện dấu hiệu vi ngủ. Hãy giảm tốc và dừng nghỉ an toàn.” |
| `DROWSY/STOP_AND_REST` | “Bạn đang buồn ngủ. Hãy tìm điểm dừng nghỉ.” |
| `DISTRACTED/FOCUS_FORWARD` | “Hãy tập trung nhìn về phía trước.” |
| `TAILGATING/INCREASE_DISTANCE` | “Hãy tăng khoảng cách với xe phía trước.” |
| `SPEEDING/REDUCE_SPEED` | “Bạn đang vượt giới hạn tốc độ. Hãy giảm tốc.” |
| `RECOVERY/NONE` | “Đã trở lại vùng an toàn.” |

Không đưa ảnh cabin, driver identity, raw JSON hoặc reasoning của LLM sang voice service.

### Quy tắc ưu tiên khi nhiều nguy cơ cùng lúc

HMI chỉ có một primary alert. Thứ tự:

```text
collision/TTC critical
→ microsleep
→ drowsy hoặc distracted
→ tailgating
→ speeding
→ harsh brake/corner/accel
```

Primary alert chứa hành động. Các nguy cơ còn lại hiển thị tối đa hai icon phụ. Backend gửi `AlertReasonCode` để HMI không phải tự đoán bằng text.

### Recovery và coaching sau sự kiện

Sau khi critical episode kết thúc:

- Chuyển đỏ → vàng → xanh trong 2 giây.
- Hiển thị “Đã trở lại vùng an toàn” trong 2 giây.
- Không đưa báo cáo dài ngay lập tức.
- Khi tốc độ dưới 5 km/h hoặc xe dừng, mở **Post-Event Coaching Card**:
  - Điều gì vừa xảy ra.
  - Evidence ngắn: TTC thấp nhất, driver state, tốc độ.
  - Một hành động cải thiện.
  - Nút “Đã hiểu”; không yêu cầu nhập text khi xe chạy.

### Signal contract mở rộng cho HMI

Năm signal cốt lõi giữ nguyên. Bổ sung các signal đề xuất để HMI deterministic và không phải parse câu tự do:

```json
{
  "signals": [
    {"path": "Vehicle.Speed", "value": 65.0},
    {"path": "Vehicle.SpeedLimit", "value": 80.0},
    {"path": "Vehicle.ADAS.Headway", "value": 0.9},
    {"path": "Vehicle.ADAS.DisplaySeverity", "value": "CRITICAL"},
    {"path": "Vehicle.ADAS.AlertReasonCode", "value": "TTC_CRITICAL"},
    {"path": "Vehicle.ADAS.RecommendedActionCode", "value": "BRAKE_SAFE"},
    {"path": "Vehicle.ADAS.EventTransition", "value": "START"},
    {"path": "Vehicle.ADAS.AIStatus", "value": "ONLINE"},
    {"path": "Vehicle.ADAS.DataAgeMs", "value": 40}
  ]
}
```

Enum đề xuất:

```text
DisplaySeverity: SAFE | WARNING | CRITICAL | RECOVERY
AlertReasonCode: NONE | TTC_WARNING | TTC_CRITICAL | MICROSLEEP |
                 DROWSY | DISTRACTED | TAILGATING | SPEEDING |
                 HARSH_BRAKE | HARSH_CORNER | HARSH_ACCEL
RecommendedActionCode: NONE | FOCUS_FORWARD | INCREASE_DISTANCE |
                       REDUCE_SPEED | BRAKE_SAFE | STOP_AND_REST
EventTransition: NONE | START | UPDATE | END
AIStatus: ONLINE | DEGRADED | OFFLINE
```

`VoiceEnabled` là local preference của HMI và được lưu trên Android, không cần Backend ghi lại mỗi frame. `DataAgeMs` dùng để phát hiện stale state; threshold mặc định: `ONLINE ≤ 1000ms`, `DEGRADED 1001–3000ms`, `OFFLINE > 3000ms`, có thể cấu hình theo AI source thực tế.

Các path mở rộng phải được thêm vào VSS artifact trước demo. Nếu chưa có, HMI có thể suy ra bản MVP từ năm signal cốt lõi nhưng không được parse LLM text để điều khiển alarm.

### Ý tưởng sáng tạo cho demo

#### Safety Halo

Một vòng sáng quanh speedometer thay đổi xanh → cam → đỏ theo severity. Đây là tín hiệu ngoại vi dễ nhận biết mà không cần đọc số risk.

#### “Why Now?” một dòng

Ngay dưới alert hiển thị đúng một evidence có ích nhất, ví dụ `TTC giảm còn 1.2s` hoặc `Mắt nhắm liên tục`. Điều này tăng độ tin cậy mà không biến HMI thành báo cáo kỹ thuật.

#### Adaptive Alert Budget

Mỗi loại warning có cooldown, ví dụ 10 giây; không phát lại nếu tình trạng không xấu hơn. Critical luôn được phép ngắt cooldown. Mục tiêu là chống “alert fatigue”.

#### Context-aware action

- Xe đang chạy nhanh + microsleep → “Giảm tốc, tìm điểm dừng”.
- Xe gần dừng + microsleep → “Dừng nghỉ 15 phút”.
- Tailgating nhưng TTC đang cải thiện → giữ icon, không phát âm thanh lại.

#### Trust Strip

Một dải nhỏ ghi `AI ONLINE`, `AI DEGRADED` hoặc `AI OFFLINE`, cạnh trạng thái `VOICE ON/MUTED`. Không hiển thị lỗi kỹ thuật dài; khi OFFLINE đổi halo sang xám và ẩn TTC/risk cũ.

#### Voice Control

Một nút lớn, dễ chạm khi xe dừng: `🔊 VOICE ON` hoặc `🔇 MUTED`. Khi xe chạy, nút chỉ đổi lời nói warning/coaching; safety tone critical vẫn hoạt động. Có nút “Phát lại hướng dẫn” chỉ khi xe dưới 5 km/h.

#### Evidence Freeze Card khi đã dừng

Khi xe dừng, HMI có thể hiển thị snapshot sự kiện: TTC thấp nhất, tốc độ, driver state và hành động đã khuyến nghị. Không phát video/snapshot gây xao nhãng khi xe đang chạy.

#### Privacy-first Cabin Indicator

Hiển thị “Cabin AI active” thay vì ảnh khuôn mặt. Không đưa `nthu_subject_id`, ảnh cabin hoặc nhận dạng cá nhân lên HMI tài xế nếu không thật sự cần.

### Những thứ tuyệt đối không hiển thị khi xe đang chạy

- Leaderboard và điểm của tài xế khác.
- Biểu đồ radar/donut/timeline.
- Raw JSON, base risk, driver factor hoặc SHAP.
- Đoạn reasoning dài do LLM sinh.
- Nhiều nút bấm, bàn phím hoặc chat box.
- Camera cabin live chiếm màn hình.
- Màu/animation liên tục khi không có nguy hiểm.

### Công việc bổ sung cho AI Agent

- [ ] Tạo HMI view-model mapper từ AI frame + Backend enrichment.
- [ ] Implement primary-alert priority và reason/action enums.
- [ ] Implement warning cooldown và critical override.
- [ ] Implement start/update/end/recovery lifecycle.
- [ ] Implement `AIStatus`, data freshness và stale-data suppression.
- [ ] Implement phrase catalog tiếng Việt, voice queue, interrupt, cooldown và fallback tone.
- [ ] Lưu local preference `VoiceEnabled`; không đồng bộ raw cabin/identity ra voice service.
- [ ] Tạo signal map mở rộng và fallback về năm signal cốt lõi.
- [ ] Viết fixture cho Normal, Warning, Critical compound-risk và Recovery.
- [ ] Tạo mock HMI state output để FE/CarSky team phát triển song song khi chưa có Room.

### Phần bắt buộc con người/HMI team

- [ ] Chọn typography, kích thước và contrast thực tế trên màn hình CarSky.
- [ ] Xác nhận alarm pattern/âm lượng không gây giật mình quá mức.
- [ ] Chọn kiến trúc HMI thật: Android app subscribe KUKSA trực tiếp hay Script/container bridge; cung cấp pin contract tương ứng.
- [ ] Implement/cài HMI consumer trên Skycraft Android hoặc custom runtime; CarSky guide không sinh app này tự động.
- [ ] Import/duyệt custom VSS artifact và data type cho toàn bộ path dự án.
- [ ] Cấu hình `a8/audio-play` nếu dùng TTS; chọn voice có thật trên environment hoặc cung cấp giải pháp audio tiếng Việt riêng.
- [ ] Usability test: đọc đúng primary alert trong khoảng 2 giây.
- [ ] Test ngoài màn hình thật: ánh sáng, kích thước, âm thanh và reset behavior.
- [ ] Review privacy đối với cabin data/driver identity.

### Phân chia việc AI Agent và con người

| Hạng mục | AI Agent có thể làm | Cần con người nhúng tay |
|---|---|---|
| REST adapter, queue, retry, mapper, mock/test | Có thể implement đầy đủ từ contract | Cấp API key và cho phép truy cập environment thật |
| Discovery room/node/path | Có thể implement logic và validation | Chọn đúng device/deployment nếu có nhiều kết quả |
| VSS artifact | Có thể đề xuất file/path/data type | CarSky/HMI owner import, duyệt compatibility |
| Script Node mapper | Có thể viết từ KUKSA API trong guide | Xác nhận edge/pin contract và deploy Blueprint |
| Driver HMI app | Có thể sinh view-model, state machine và source code nếu có project/spec | HMI team build, ký/cài app và test màn hình thật |
| Signal Watch/GPIO test | Có thể viết checklist/fixture | Người có quyền Workbench thao tác và đối chiếu |
| Audio/TTS | Có thể implement fallback và event mapping | Cấu hình playback part, chọn voice, duyệt âm lượng |
| Usability/safety/privacy | Có thể tạo checklist | Bắt buộc human sign-off |

### Acceptance scenarios cho HMI

1. Normal + TTC Infinity: chỉ speed, limit và halo xanh; không có TTC/risk number.
2. Speeding: warning cam, “Giảm về X km/h”, một âm nhẹ.
3. Tailgating + TTC 2.2s: primary “Tăng khoảng cách”; TTC xuất hiện.
4. Microsleep + TTC Infinity: critical vi ngủ; action dừng nghỉ.
5. TTC 1.2s + microsleep: collision là primary, microsleep là icon phụ; alarm chỉ một pattern.
6. Episode kết thúc: reset signal, recovery 2 giây, không tắt cảnh báo đột ngột.
7. Xe dừng: post-event coaching được phép hiển thị; khi xe chạy lại card tự đóng.
8. CarSky/API offline: Trust Strip báo offline rules; HMI không hiển thị dữ liệu cũ như dữ liệu live.
9. Voice warning được đọc một lần; cùng reason trong cooldown không đọc lại.
10. Critical ngắt voice warning, visual vẫn hoạt động khi TTS lỗi hoặc Voice bị mute.
11. AI frame quá freshness threshold: status chuyển DEGRADED/OFFLINE, halo xám và ẩn TTC cũ.

## File dự kiến ảnh hưởng

- `app/modules/coaching/*`
- Reasoning service mới trong coaching hoặc risk module
- `app/adapters/carsky_adapter.py`
- Replay/background delivery integration
- Configuration và `.env.example`

## Kiểm thử

- Copilot trả đúng câu hỏi fleet phổ biến từ cache.
- Không có API key vẫn trả lời thành công.
- Provider timeout chuyển fallback dưới 3 giây.
- LLM không thay đổi số liệu hoặc `risk.final_risk_score` nguồn AI.
- CarSky chỉ nhận một request cho một critical episode.
- CarSky nhận request reset khi episode kết thúc.
- Discovery tìm đúng room/signal node và reject node không có các VSS path bắt buộc.
- Signal Watch quan sát đúng fixture nhưng không được dùng làm bằng chứng duy nhất cho Driver HMI.
- Payload actuate khớp `{signals:[{path,value}]}` và giữ nguyên số liệu AI.
- Đọc lại `/values` là acceptance bắt buộc. SSE integration test chạy khi deployment bật subscribe endpoint và không chặn offline CI.
- HTTP 500 được retry giới hạn; HTTP 401 không retry vòng lặp.
- 401/403/404/422/429 được map thành delivery result rõ ràng.
- Offline adapter không gọi network và replay vẫn tiếp tục.

## Definition of Done

- [ ] Copilot response schema thống nhất với Frontend.
- [ ] Năm intent demo hoạt động không cần internet.
- [ ] Online LLM có timeout và fallback an toàn.
- [ ] CarSky adapter có online/offline mode và test mock HTTP.
- [ ] Blueprint/VSS prerequisites và cách lấy credential/room/node được ghi rõ.
- [ ] Pin/edge contract giữa KUKSA, Script và HMI đã được xác nhận từ Blueprint thật; không còn giao thức giả định.
- [ ] Critical episode kích hoạt đúng một `CriticalAlert=true` và kết thúc bằng `CriticalAlert=false`.
- [ ] Signal values được xác minh qua API hoặc SSE; Android HMI được kiểm tra bằng screenshot.
- [ ] HMI app/custom runtime tồn tại và đang chạy; Screen Widget chỉ được dùng để quan sát app đó.
- [ ] Nếu dùng audio/TTS, `a8/audio-play` đã hoạt động; thiếu TTS không làm hỏng visual critical alert.
- [ ] AI status phản ánh data freshness, không phản ánh riêng kết nối LLM/TTS.
- [ ] Phrase catalog tiếng Việt deterministic, voice cooldown/interrupt/mute/fallback đều pass.
- [ ] HMI chỉ hiển thị dữ liệu phù hợp với tài xế; Fleet analytics/raw AI fields không xuất hiện khi xe chạy.
- [ ] Mười một acceptance scenarios HMI đều pass, gồm compound alert, recovery, stopped coaching, voice lifecycle và offline state.
- [ ] Primary alert đọc hiểu được trong khoảng 2 giây và đã có human usability sign-off.
- [ ] Lỗi external service không làm hỏng API hoặc WebSocket.
