# PHÂN TÍCH SÂU BÀI TOÁN TRƯỚC KHI XÂY DỰNG CORE
### FPTU DMS Vision — Connected Car Hackathon 2026
*(Bước "very firstly" — chốt nhận thức & toàn bộ case/edge-case trước khi viết 1 dòng code lõi)*

---

## 0. Nguyên tắc nền tảng

Trước khi build, cả team phải thống nhất 3 câu hỏi gốc:

1. **Cái gì quyết định `driver_state`?** (đầu ra Challenge 2)
2. **Cái gì quyết định `risk_score`?** (đầu ra Challenge 3)
3. **Những tình huống nào phá vỡ giả định của ta?** (edge-case → quyết định điểm sống còn)

Triết lý xuyên suốt: **Trạng thái tức thời (1 frame) không đủ để kết luận. Phải xét ngữ cảnh thời gian (temporal) + ngữ cảnh vận hành (motion/traffic).** Đây là gốc rễ của mọi false alarm.

---

## 1. ĐIỀU GÌ TÁC ĐỘNG VÀO `driver_state`?

`driver_state ∈ {alert, drowsy, yawning, distracted, microsleep}` được quyết định bởi **3 tín hiệu sơ cấp (primitive)** + **1 lớp thời gian (temporal)** + **1 lớp ngữ cảnh (context/confounder)**.

### 1.1 Ba trục tín hiệu sơ cấp (từ Face Cam / MediaPipe)

| Trục | Primitive feature | Domain feature suy ra | Trạng thái nó "tố cáo" |
|------|-------------------|------------------------|------------------------|
| **Mắt (Eye)** | 6–12 landmark quanh mắt | `EAR`, eye_closure_duration, blink_rate, **PERCLOS(60s)** | drowsy, microsleep |
| **Miệng (Mouth)** | landmark quanh môi | `MAR`, yawn_duration, yawn_count | yawning, (drowsy) |
| **Đầu (Head)** | pose 3 trục | `head_yaw`, `head_pitch`, nodding | distracted (yaw/pitch lớn), drowsy (gật gù) |

### 1.2 Bản đồ nhân–quả: đặc trưng → trạng thái

| State | EAR | PERCLOS | MAR | Head pose | Dấu hiệu đặc trưng nhất |
|-------|-----|---------|-----|-----------|--------------------------|
| **alert** | bình thường (~0.25–0.30) | thấp (<15%) | bình thường | hướng trước | Mắt mở, đầu thẳng, chớp mắt đều |
| **drowsy** | giảm dần, chớp chậm | **tăng cao (>15%)** | có thể tăng | có thể gật gù | Nhắm mắt kéo dài 0.5–2s lặp lại, chớp mắt chậm |
| **yawning** | có thể nheo khi ngáp | — | **cao & kéo dài (~4–6s)** | hơi ngửa | Miệng mở to **liên tục**, chậm (phân biệt với nói/hát) |
| **distracted** | mở bình thường | thấp | — | **yaw/pitch lệch lớn** (side/down) | Mắt rời đường: nhìn nghiêng, cúi xuống, dùng điện thoại |
| **microsleep** | ≈ 0 (nhắm hẳn) | tăng đột biến | — | thường gục nhẹ | **Nhắm mắt liên tục ≥ 0.5s** (tối đa ~10s), mất phản xạ |

### 1.3 Lớp thời gian (temporal) — thứ quyết định độ chính xác

Một frame nhắm mắt **không** = microsleep. Phải nhìn cửa sổ thời gian:

- **PERCLOS** = % frame mà mắt nhắm >80% trong cửa sổ trượt **60s**.
- **Chuỗi liên tục** (consecutive-closed-frames), không phải frame đơn lẻ.
- **Xu hướng mệt tích lũy** (`fatigue_score`, `microsleep_count`, `longest_drowsy_episode_sec`) — càng về cuối trip càng dễ drowsy.

### 1.4 Lớp ngữ cảnh (confounder) — nguồn gốc false alarm

- **Ánh sáng / chói nắng** → tài xế nheo mắt nhưng KHÔNG buồn ngủ.
- **Kính / kính râm** → landmark mắt sai → EAR nhiễu.
- **Che khuất / mất tín hiệu camera** → không suy được state.
- **Người ngồi cạnh** → nhầm mặt hành khách thành tài xế.
- **`alertness_score`** còn bị ảnh hưởng bởi context (tốc độ, thời điểm trong trip), không chỉ khuôn mặt.

> **Kết luận Mục 1:** `driver_state = f(Eye, Mouth, Head) × Temporal_window × Context_filter`. Bỏ 2 lớp sau = tụt Macro-F1 vì nhầm lớp hiếm.

---

## 2. "LIỆU NHEO MẮT CÓ NGUY HIỂM? NHEO BAO LÂU LÀ ỔN?"

Đây là câu hỏi cốt tử vì nó tách 3 thứ **rất giống nhau về hình ảnh** nhưng **khác nhau hoàn toàn về rủi ro**: chớp mắt bình thường ↔ nheo do chói ↔ drowsy/microsleep.

### 2.1 Phổ đóng mắt theo thời gian (ngưỡng đã kiểm chứng)

| Hiện tượng | Thời lượng nhắm | EAR | Nguy hiểm? | Xử lý |
|------------|------------------|-----|-----------|-------|
| **Chớp mắt bình thường** | 0.1–0.4s (100–400ms), 15–20 lần/phút | dip nhanh về ~0 rồi mở lại | KHÔNG | Bỏ qua |
| **Nheo mắt do chói nắng** | kéo dài nhưng **mắt vẫn hé & dõi đường** | giảm một phần (không về 0) | KHÔNG (nếu đầu vẫn hướng đường) | **Suy giảm bằng context ánh sáng** (sun_altitude, brightness), không gán drowsy |
| **Chớp chậm / drowsy sớm** | 0.5–2s, lặp lại, mở mắt chậm | giảm rõ, PERCLOS leo thang | CÓ (cảnh báo sớm) | Gán `drowsy` khi PERCLOS(60s) > 15% |
| **Microsleep** | **≥ 0.5s nhắm hẳn** (tới ~10s) | ≈ 0 | RẤT CAO | Gán `microsleep`, ưu tiên cảnh báo tối đa |

### 2.2 Trả lời trực tiếp

- **Nheo/chớp < ~0.4s:** bình thường, **an toàn**, tuyệt đối không báo động.
- **Nhắm liên tục ≥ 0.5s:** vượt lằn ranh **microsleep** → nguy hiểm nhất → phải bắt được (nếu bỏ sót, Recall lớp microsleep = 0 → Macro-F1 sập).
- **Nheo một phần kéo dài:** phải **phân biệt nguồn gốc**:
  - Nếu `sun_altitude` cao / ảnh sáng chói / đầu vẫn hướng đường → **chói nắng, an toàn**.
  - Nếu PERCLOS(60s) tăng dần + chớp chậm + về cuối trip → **drowsy sớm, nguy hiểm**.

### 2.3 Ngưỡng đề xuất chốt bằng Grid Search trên 6 trip Practice

- `EAR_closed_threshold ≈ 0.22–0.25` (chốt lại theo phân phối GT từng subject).
- `PERCLOS_drowsy > 0.15` trên cửa sổ 60s (chuẩn NHTSA).
- `microsleep: eye_closure ≥ 0.5s` liên tục (≈ 10 frame ở 20 FPS).
- **Per-driver calibration:** cơ địa mỗi người khác nhau (mắt to/nhỏ) → nên chuẩn hóa EAR theo baseline vài giây đầu trip khi tài xế còn `alert`.

> **Cạm bẫy điểm số:** nhầm nheo-chói thành drowsy → **False Positive** (giảm Precision). Bỏ sót microsleep nửa-mở-mắt → **False Negative** (giảm Recall → sập Macro-F1). Cả hai đều phải chặn.

---

## 3. ĐIỀU GÌ TÁC ĐỘNG VÀO `risk_score`?

`risk_score` **không cộng tuyến tính** — nó là **tích hợp đa nguồn có hệ số nhân**. Theo chính schema BTC: `final_risk_score = base_risk × driver_factor`.

### 3.1 Bốn nhóm yếu tố đầu vào

| Nhóm | Nguồn | Feature chính | Cách tác động |
|------|-------|----------------|----------------|
| **1. Rủi ro va chạm** | Road cam (Ch1) | `min_ttc`, `closing_speed`, `in_collision_cone`, near_miss (TTC≤1.5s) | TTC càng nhỏ → base_risk càng cao (phi tuyến, dùng 1/TTC) |
| **2. Động lực học xe** | Telemetry | harsh_brake/accel/corner, speeding, jerk | Mỗi hành vi gắt cộng điểm phạt |
| **3. Năng lực tài xế** | Cabin cam (Ch2) | `driver_state`, `alertness_score` | **Hệ số nhân** `driver_factor` (vd 2.2) — khuếch đại base_risk |
| **4. Ngữ cảnh môi trường** | Metadata | fog, rain, night, weather | Nhân thêm rủi ro nền |

### 3.2 Yếu tố khuếch đại: RỦI RO KÉP (Compound Risk)

Đây là điểm "ăn tiền": rủi ro thật = **tương tác đồng thời**, không phải tổng rời rạc.

- Tài xế `microsleep` **VÀ** tốc độ > 50km/h → nguy hiểm gấp bội (không phải "một chút buồn ngủ + một chút nhanh").
- Tài xế `distracted` **VÀ** TTC thấp (có vật cản phía trước) → mù trước hiểm họa.
- `driver_factor` chính là toán tử nhân mô hình hóa việc này.

### 3.3 Quy về điểm Trip (Safe Driving Score, thang 100)

`Safe_Score = 100 − Σ penalties`, với barem BTC:

| Sự kiện | Phạt | Đơn vị |
|---------|------|--------|
| Near-miss (TTC ≤ 1.5s) | **5.0** | /lần |
| Harsh brake | 3.0 | /lần |
| Harsh accel | 2.0 | /lần |
| Harsh corner | 2.0 | /lần |
| Speeding | 0.15 | /1% thời gian |
| Tailgating | 0.10 | /1% thời gian |

### 3.4 Ba lưu ý sống còn khi tính risk_score

1. **Ngữ cảnh vận hành (Motion State) lọc trước:** distracted lúc xe **đang dừng đèn đỏ (v=0)** ≈ rủi ro thấp; distracted lúc **60km/h** = rủi ro cao. Không lọc motion → tính điểm sai.
2. **Chống trừ điểm trùng (double-count):** 1 nguyên nhân không được phạt nhiều lần bởi nhiều rule chồng lấn (đây là Hạn chế #11 còn bỏ ngỏ).
3. **Calibration cực mịn:** Ch3 chấm trừ ~1 điểm/1 điểm MAE. Lệch 10 điểm → mất 10 điểm Composite. → Phải hold-out validate, không "học vẹt" trên 10 trip thi.

---

## 4. TOÀN BỘ CASE & EDGE-CASE (chốt trước khi build core)

Chia theo **4 chiều độc lập**. Mỗi tổ hợp = 1 test-case cần có kỳ vọng đầu ra rõ ràng.

### 4.1 Chiều A — Trạng thái tài xế (Driver)

| # | Case | Kỳ vọng | Bẫy |
|---|------|---------|-----|
| A1 | Tỉnh táo lái bình thường | alert | — |
| A2 | Ngáp 1 lần | yawning (trong lúc ngáp) | Phân biệt nói/hát (MAR cao nhưng ngắn/nhịp) |
| A3 | Ngáp lặp lại nhiều lần | yawning + nâng fatigue → dễ chuyển drowsy | — |
| A4 | Buồn ngủ tăng dần | drowsy | Chớp chậm ≠ chớp thường |
| A5 | Vi ngủ (microsleep) | microsleep | **Không được bỏ sót** (Recall) |
| A6 | Nhìn điện thoại | distracted | Cần YOLO detect phone |
| A7 | Ngoái đầu / nhìn gương | distracted (nếu kéo dài) vs bình thường (liếc gương < ~1s) | Liếc gương là an toàn, đừng phạt |
| A8 | Cúi chỉnh điều hòa/radio | distracted ngắn | Ngưỡng thời lượng |

### 4.2 Chiều B — Trạng thái vận hành xe (Motion State)

| # | Case | Ảnh hưởng |
|---|------|-----------|
| B1 | Driving (v > 10 km/h) | Áp dụng đầy đủ mọi rule rủi ro |
| B2 | Low-speed/parking (v ≤ 10) | Nới ngưỡng harsh, giảm trọng số va chạm |
| B3 | Stopped (v ≈ 0, đèn đỏ/tắc đường) | **Tắt near-miss & tailgating**; distracted → rủi ro thấp |
| B4 | Reversing (gear = R) | **Đảo logic TTC**; ngưỡng gia tốc khác |

### 4.3 Chiều C — Sự kiện giao thông (Traffic Event)

| # | Case (theo README) | Xử lý |
|---|--------------------|-------|
| C1 | `pedestrian_jaywalk` | Người băng ngang → TTC gấp, near-miss |
| C2 | `motorcycle_cut_in` | Xe máy tạt đầu → closing_speed đột biến |
| C3 | `lead_brake` | Xe trước phanh gấp → TTC sụt nhanh |
| C4 | `stopped_vehicle_ahead` | Vật cản đứng yên trên làn |
| C5 | Đường trống, không target | predicted_ttc = `inf`, risk thấp |

### 4.4 Chiều D — EDGE CASES (nơi quyết định thắng/thua)

**D-Cabin (Driver-facing):**

| # | Edge case | Rủi ro nếu không xử lý | Giải pháp |
|---|-----------|------------------------|-----------|
| D1 | Nheo mắt do **chói nắng** | Nhầm drowsy (FP) | Suy giảm bằng context ánh sáng + head hướng đường |
| D2 | Đeo **kính/kính râm** | EAR sai | Fallback sang head_pose + telemetry; hạ tin cậy EAR |
| D3 | **Dùng điện thoại** | Bỏ sót distracted | YOLOv8-nano detect phone / tay áp tai → ép `distracted` |
| D4 | **Nhiều người trong cabin** | Nhầm hành khách | Chọn bbox mặt lớn nhất ở `driver_anchor_box` |
| D5 | **Đổi ca / đổi tài xế** | Baseline nhảy | Reset per-driver baseline khi phát hiện đổi subject |
| D6 | **Mất tín hiệu / tối / che camera** | Crash hoặc đoán bừa | **Degraded Mode**: giữ `alert`, tính risk chỉ từ telemetry |
| D7 | **Nói chuyện / hát** | MAR cao → nhầm yawning | Ngáp = mở to **chậm & kéo dài ~4–6s**; nói = nhịp ngắn |
| D8 | **Uống nước / ăn / đeo khẩu trang** | MAR & landmark miệng vô dụng | Vô hiệu hóa MAR, dựa vào mắt + head |
| D9 | **Microsleep nửa-mở-mắt** | Bỏ sót (FN) | Không chỉ dựa EAR≈0; xét mất phản xạ + head drop |
| D10 | **Dụi mắt / tay che mặt** | Nhầm nhắm mắt | Detect tay che → tạm hoãn phán đoán mắt |

**D-Road (Road-facing & Fusion):**

| # | Edge case | Rủi ro | Giải pháp |
|---|-----------|--------|-----------|
| D11 | **Nhiều target/frame** (như JSON mẫu: cả chục xe TTC=inf) | Báo động giả | Chỉ lấy `min_ttc` **trong collision cone**; lọc target ngang/xa |
| D12 | **Xe cắt ngang (lateral)** không trên đường đi | FP near-miss | `in_collision_cone = false` → bỏ |
| D13 | **Stop-and-go / tắc đường** | Headway sát nhưng v thấp → nhầm tailgating | Gắn tailgating với motion state B1 |
| D14 | **Domain shift** CARLA→DMD (đường render vs cabin thật) | Depth/detect sai | Augmentation (noise, fog, contrast) + histogram equalization |
| D15 | **Mưa/sương/ngược sáng trên road cam** | Depth sai → TTC sai | Augmentation môi trường + hạ tin cậy khi ảnh xấu |
| D16 | **Lệch pha timestamp** 3 luồng | Ghép sai thời điểm | `SynchronizedDataLoader` + nearest-neighbor + `assert |t_road−t_driver|<0.01s` |

**D-Risk (Logic nghiệp vụ & chấm điểm):**

| # | Edge case | Rủi ro | Giải pháp |
|---|-----------|--------|-----------|
| D17 | **Distracted lúc xe đứng yên** (đèn đỏ) | Phạt oan | Lọc bằng Motion State B3 |
| D18 | **Cua có xi-nhan / chuyển làn chủ động** | Nhầm harsh_corner | `|steering|>15°` + lane_offset → suppress cảnh báo cua giả |
| D19 | **Xung đột rule / trừ điểm trùng** (vừa lùi vừa ngáp…) | Sai `risk_score` | Test suite tự động + ưu tiên rule, cấm cộng trùng nguyên nhân |
| D20 | **Cơ địa sinh học khác nhau** | Baseline sai | Per-driver EAR/MAR calibration |
| D21 | **Overfit trên 10 trip thi** | Sụt điểm chính thức | Hold-out: 4 trip calib / 2 trip validate, khóa trọng số khi ổn định |
| D22 | **API LLM timeout khi demo** | Dashboard lỗi 500 | Rule-based fallback + pre-render 10 báo cáo |

---

## 5. CHECKLIST TRƯỚC KHI VIẾT CODE LÕI

- [ ] Chốt định nghĩa toán học từng state (bảng Mục 1.2) — cả team đồng thuận.
- [ ] Grid Search chốt ngưỡng EAR/MAR/PERCLOS trên 6 trip Practice (Mục 2.3).
- [ ] Vẽ phân phối EAR/MAR theo từng nhãn GT để kiểm chứng ngưỡng.
- [ ] Định nghĩa Motion State filter (B1–B4) làm lớp lọc **đầu tiên** của Fusion.
- [ ] Liệt kê 22 edge-case (Mục 4.4) thành **test-case có expected output**.
- [ ] Thống nhất công thức chống double-count (D19) — giải quyết Hạn chế #11.
- [ ] Chốt kế hoạch hold-out validation (D21) để không overfit.
- [ ] Xác định collision-cone logic cho `min_ttc` (D11–D12).

---

## 6. CÂU HỎI CẦN CHỐT (nội bộ team / hỏi BTC)

1. Ngưỡng `harsh_*` và `near_miss` BTC dùng có **khớp** ngưỡng ta tự đặt không? → nên bám GT của Practice để reverse-engineer.
2. `driver_factor` (hệ số nhân) BTC tính từ state như thế nào? → dò từ cột GT `driver_factor` vs `driver_state` trong 6 trip Practice.
3. Cửa sổ PERCLOS BTC dùng là 60s hay khác? → kiểm bằng cách so `microsleep_count`/`longest_drowsy_episode_sec` trong summary.
4. Có giới hạn loại model không (được dùng VLM/pretrained không)? → hỏi BTC.

---

---

## 7. TRẢ LỜI CÁC CÂU HỎI CẦN CHỐT (Mục 6)

> Phân loại nguồn trả lời: 🟢 = suy luận/lấy được ngay từ tài liệu & dataset · 🟡 = phải chạy script trên Ground Truth 6 trip Practice · 🔴 = bắt buộc hỏi BTC.

### Q1 — Ngưỡng `harsh_*` và `near_miss` của BTC có khớp ngưỡng ta tự đặt không? 🟢🟡

**Trả lời: KHÔNG cần đoán — ngưỡng của BTC là cố định và ĐÃ lộ ra trong dữ liệu Practice.**

- Trong mỗi frame JSON của 6 trip Practice, BTC **đã cung cấp sẵn** `behavior_flags { harsh_brake, harsh_accel, harsh_corner, speeding, tailgating }` (True/False) như một phần **Ground Truth**. Đây chính là "đáp án" ngưỡng của BTC.
- Ngưỡng ta ghi trong tài liệu (harsh_brake `aₓ < -0.40g`, harsh_accel `> +0.35g`, harsh_corner `|a_y| > 0.30g`, near_miss `TTC ≤ 1.5s`) hiện là **giả thuyết** — cần đối chiếu với flag GT để xác nhận đúng con số.
- **Điểm mấu chốt:** trong 10 trip thi thật (redacted), các flag này **bị xóa**. Ta **buộc phải tự tái tạo** chúng bằng ngưỡng của mình → ngưỡng đó phải **trùng khít** ngưỡng BTC, nếu lệch sẽ đếm sai `harsh_*_count` / `near_miss_count` → sai thẳng Safe Score.

**Cách xác nhận chính xác (reverse-engineering trên Practice):**
1. Với mỗi frame: lấy cặp `(longitudinal_accel, harsh_brake_flag)`. Vẽ scatter/histogram → **ranh giới** giữa vùng True và False chính là ngưỡng thật của BTC (làm tương tự cho accel, corner với `lateral_accel`).
2. `near_miss`: đối chiếu frame có `min_ttc ≤ ?` với `near_miss_count` trong `trip_aggregate` → dò đúng ngưỡng (dự kiến 1.5s, cần kiểm).
3. `speeding`: so `speed_kmh` với `speed_limit_kmh` (trong metadata) để tìm biên (dự kiến +5 km/h).
4. Khóa các ngưỡng này lại, dùng chung cho 10 trip thi.

> Kết luận: câu này **tự trả lời được 100%** bằng script phân tích trên GT Practice, **không cần hỏi BTC**.

### Q2 — `driver_factor` (hệ số nhân) BTC tính từ state như thế nào? 🟢🟡

**Trả lời: `driver_factor` là hệ số nhân theo `driver_state`, và cũng nằm sẵn trong GT Practice để dò công thức.**

- Theo schema: `final_risk_score = base_risk × driver_factor`. Trong frame mẫu: `state = distracted`, `alertness_score = 0.45` → `driver_factor = 2.2` (nhưng `final_risk = 0.0` vì `base_risk = 0.0`, tức không có mối nguy va chạm/hành vi gắt nào để khuếch đại).
- Suy ra bản chất: **`driver_factor` ≈ 1.0 khi tài xế `alert`, và tăng dần theo mức suy giảm năng lực** (yawning < distracted < drowsy < microsleep). Nó là "van khuếch đại": tài xế càng kém tỉnh táo, cùng một mối nguy ngoài đường sẽ bị nhân điểm rủi ro lên.

**Cách dò công thức chính xác (trên GT Practice):**
1. Lập pivot: nhóm toàn bộ frame theo `driver_state` → xem **phân phối giá trị `driver_factor`** của từng nhóm.
2. Nếu mỗi state cho **một hằng số** → đó là **bảng tra cứu** (lookup table), ví dụ giả định cần kiểm: `alert=1.0, yawning≈1.5, distracted≈2.2, drowsy≈2.5–3, microsleep≈3+`.
3. Nếu `driver_factor` **biến thiên trong cùng một state** → nó phụ thuộc `alertness_score` → hồi quy `driver_factor` theo `alertness_score` (dạng nghi ngờ: `driver_factor = 1 + k·(1 − alertness_score)`).
4. Kiểm chứng lại bằng cách nhân thử `base_risk × driver_factor` và so với `final_risk_score` GT trên các frame có base_risk > 0.

> Kết luận: **tự trả lời được** bằng phân tích GT; chỉ cần 1 script pivot + hồi quy.

### Q3 — Cửa sổ PERCLOS BTC dùng là 60s hay khác? 🟢🟡 (kèm chỉnh nhận thức)

**Trả lời: Cần tách 2 chuyện — PERCLOS là feature CỦA TA, còn nhãn `driver_state` là do dataset gán, không suy từ PERCLOS.**

- `driver_state` Ground Truth đến từ **bộ DMD/NTHU** (có `nthu_subject_id`), tức là **nhãn do con người/dataset gán**, KHÔNG phải BTC tính bằng công thức PERCLOS. Vì vậy không có "cửa sổ PERCLOS của BTC" cho việc gán state để mà khớp.
- ⇒ **Cửa sổ PERCLOS là lựa chọn thiết kế của TA** để dự đoán state. Chuẩn NHTSA là **60s**, nhưng lưu ý xung đột thực tế: **trip Practice chỉ dài 30s**, trip thi 90s → cửa sổ 60s **không thể đầy** trên trip 30s.
  - **Đề xuất:** dùng **cửa sổ thích ứng** `window = min(thời_gian_đã_trôi, 60s)`, hoặc chọn cửa sổ ngắn hơn (15–30s) rồi Grid Search chọn cửa sổ cho Macro-F1 cao nhất trên Practice.
- **Chỗ THỰC SỰ khớp được với BTC:** hai đại lượng trong `driver_summary` do BTC tính là `microsleep_count` và `longest_drowsy_episode_sec`. Ta **hiệu chỉnh ngưỡng thời lượng nhắm mắt** của mình sao cho khi chạy trên Practice, số microsleep/độ dài drowsy ta đếm được **trùng** với summary BTC → đó là cách "chốt ngưỡng theo BTC" đúng nghĩa.

> Kết luận: 60s là mặc định theo chuẩn ngành, nhưng **phải dùng cửa sổ thích ứng vì trip ngắn**, và **calibrate ngưỡng nhắm-mắt bằng `microsleep_count`/`longest_drowsy_episode_sec` trong summary**. Không cần hỏi BTC.

### Q4 — Có bị giới hạn loại model không? Được dùng VLM (Alpamayo/Cosmos) không? 🔴

**Trả lời: Câu này BẮT BUỘC hỏi BTC — không tự chốt được. Nhưng có khuyến nghị kiến trúc bất kể câu trả lời.**

- **Phải hỏi BTC** rõ: (a) có whitelist/blacklist model không, (b) có được dùng pretrained/model ngoài không, (c) VLM/LLM có được tính vào phần chấm không. (Đúng như note trong tài liệu gốc: nếu BTC hỏi model cụ thể thì trả lời "nhóm em đang đi tìm model".)
- **Khuyến nghị kiến trúc (đúng dù BTC trả lời thế nào):**
  - **Lõi real-time 20 FPS** (Ch1/Ch2) **không dùng VLM nặng** — Alpamayo/Cosmos không chạy nổi 20 FPS trên thiết bị demo. Dùng model nhẹ: **YOLOv8n/s + MobileNetV3/ResNet18**, xuất ONNX/TensorRT FP16-INT8.
  - **VLM/LLM để ở tầng GenAI Coaching** (event-driven, mỗi trip 1 lần) — diễn giải rủi ro, sinh báo cáo, KHÔNG chạy per-frame. Ở tầng này VLM là điểm cộng "ăn tiền", không ảnh hưởng latency lõi.
  - ⇒ Kể cả khi BTC cho dùng VLM, vẫn nên đặt nó ở tầng coaching, không thay lõi real-time.

---

## 8. NHỮNG CÂU HỎI CẦN GỬI BTC (gom lại)

Ngoài Q4 ở trên, các câu chỉ BTC mới trả lời được (từ mục "Hỏi ban tổ chức" trong tài liệu gốc):

1. **Trọng số & barem vòng 2:** điểm chia thế nào giữa file `.csv` (chấm tự động) và Fleet Dashboard / pitching? Tỷ trọng mỗi Challenge?
2. **Tiêu chí vào vòng trong** là gì (điểm số thuần hay có chấm ý tưởng/demo)?
3. **Vòng 2 "tìm ý tưởng Connected Car"** BTC kỳ vọng những hạng mục gì?
4. **Giới hạn model / VLM** (Q4).

> Q1–Q3 (Mục 7) **KHÔNG cần hỏi BTC** — trả lời được bằng script phân tích Ground Truth trên 6 trip Practice. Đây nên là việc làm ngay khi có dataset.

---

*Tài liệu này là bước phân tích nền (Mục 1 trong "Các bước nhóm cần làm"). Sau khi chốt, mới sang bước 2 (xây core Road/Face) và bước 3 (Fusion + Decision Engine).*
