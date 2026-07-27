# KIẾN TRÚC HỆ THỐNG THIẾT KẾ NGƯỢC TỪ 5 OUTPUT (OUTPUT-DRIVEN ARCHITECTURE)
### FPTU DMS Vision — Connected Car Hackathon 2026
*Tài liệu này là bản kiến trúc duy nhất còn hiệu lực (bản kiến trúc "sản phẩm hoàn chỉnh" ban đầu — edge box, dashboard, GenAI... — đã được gộp toàn bộ vào Mục 6 bên dưới). Thiết kế theo tư duy ngược — bắt đầu từ 5 thứ phải nộp, suy ra kiến trúc tối thiểu-đủ để tạo ra chúng với chất lượng cao nhất, rồi mới xếp phần "sản phẩm" vào đúng chỗ của nó (làm giàu cho Output #03, không phải xương sống bắt buộc).*

---

## 0. NGUYÊN TẮC THIẾT KẾ NGƯỢC (Output-First Design)

Câu hỏi gốc không phải "hệ thống DMS hoàn chỉnh trông như thế nào?" mà là:

> **"Cấu trúc code nào sinh ra 5 output với ít công sức trùng lặp nhất, và mỗi output đạt chất lượng cao nhất?"**

Ba hệ quả kiến trúc trực tiếp từ câu hỏi này:

1. **Single Source of Truth (SSOT).** CSV nộp bài và Demo **phải dùng chung một Core Engine** — không viết 2 bộ logic (một để xuất CSV, một để chạy demo). Nếu tách rời, sửa 1 nơi quên nơi kia → Demo và CSV lệch nhau → mất điểm minh bạch (Output #04 yêu cầu nhất quán).
2. **Tách "Bắt buộc" khỏi "Làm giàu".** Kiến trúc edge box, offline-first queue, API gateway (chi tiết ở Mục 6) là tư duy sản phẩm hay, nhưng **không output nào trong 5 output yêu cầu chúng phải chạy thật trên xe**. Chúng chỉ cần **kể được câu chuyện** trong Demo/Video/Notes. → Đưa xuống lớp "Extension" tùy chọn, không phải xương sống.
3. **Tài liệu là sản phẩm phụ tự động, không phải việc viết tay riêng.** Implementation Notes cần số liệu (Macro-F1, MAE...) — nếu kiến trúc tự động ghi log số liệu này ra file mỗi lần train/eval, việc "viết Notes" chỉ còn là dán số vào template, không phải nhớ lại từ đầu.

---

## 1. SƠ ĐỒ TỔNG: CORE ENGINE TỎA RA 5 NHÁNH OUTPUT

```
                              ┌───────────────────────────────┐
                              │      RAW DATA (BTC cấp)       │
                              │  Road cam · Cabin cam ·       │
                              │  Telemetry JSON · Metadata    │
                              └───────────────┬───────────────┘
                                              ▼
                    ╔═════════════════════════════════════════════╗
                    ║            CORE ENGINE (lõi duy nhất)        ║
                    ║  ─────────────────────────────────────────  ║
                    ║  1. Feature Extraction (primitive→domain)    ║
                    ║  2. Fusion(1): predict_ttc() + predict_state()║
                    ║  3. Motion Filter + Fusion(2): risk_score     ║
                    ║  4. Trip Aggregator: safe_driving_score       ║
                    ║  5. Metrics Logger: tự ghi số liệu mỗi lần    ║
                    ║     train/eval ra metrics_log.json (SSOT)     ║
                    ╚═══════════════════╦═══════════════════════════╝
                                        │  (mọi nhánh dưới đây ĐỀU gọi
                                        │   lại đúng Core Engine này —
                                        │   không viết logic riêng)
        ┌───────────────┬───────────────┼───────────────┬───────────────┐
        ▼               ▼               ▼               ▼               ▼
  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
  │ OUTPUT #01│   │ OUTPUT #02│   │ OUTPUT #03│   │ OUTPUT #04│   │ OUTPUT #05│
  │    CSV    │   │   REPO    │   │   DEMO    │   │  IMPL.    │   │  USAGE    │
  │predictions│   │ (container│   │(Streamlit │   │  NOTES    │   │  NOTES    │
  │/T0Xd.csv  │   │ chứa toàn │   │đọc lại CSV│   │(auto-fill │   │(sinh từ   │
  │           │   │ bộ Core + │   │+ Core lo- │   │ từ metrics│   │ CLI thật  │
  │run_inference│  │ configs + │   │ trực tiếp)│   │_log.json) │   │ của script)│
  │   .py     │   │ docs)     │   │           │   │           │   │           │
  └───────────┘   └───────────┘   └───────────┘   └───────────┘   └───────────┘
                                        │
                                        ▼ (mở rộng KHÔNG bắt buộc — làm giàu Demo/pitch)
                              ┌───────────────────────────┐
                              │   EXTENSION LAYER (bonus)  │
                              │  Edge DMS box · API GW ·   │
                              │  Fleet Dashboard đầy đủ ·  │
                              │  GenAI Coaching real-time  │
                              │  (xem chi tiết ở Mục 6)    │
                              └───────────────────────────┘
```

**Đọc sơ đồ:** mọi mũi tên từ Core Engine ra 5 Output đều là **lời gọi hàm vào cùng 1 bộ code**, không phải 5 hệ thống riêng biệt. Extension Layer là nhánh phụ, chỉ phục vụ kể chuyện ở Output #03, không ảnh hưởng Output #01/#02/#04/#05.

---

## 2. CORE ENGINE — THIẾT KẾ TỐI GIẢN-ĐỦ (must-have)

So với kiến trúc sản phẩm đầy đủ (Mục 6), Core Engine ở đây **bỏ hết phần vận hành thời gian thực** (queue, gateway, edge box) — vì các output không cần chạy trên xe thật, chỉ cần **chạy đúng và tái tạo được** trên máy BTC.

```
core/
├── schemas.py              # FEATURE_VECTOR_SCHEMA + 2 interface chuẩn (dùng ở MỌI nhánh)
├── sync_loader.py          # đồng bộ timestamp 3 luồng
│
├── challenge1_road/
│   └── predict_ttc.py      # ⚡ Interface gọi bởi: run_inference.py VÀ demo/app.py
├── challenge2_driver/
│   └── predict_state.py    # ⚡ Interface gọi bởi: run_inference.py VÀ demo/app.py
├── challenge3_fusion/
│   ├── motion_filter.py
│   ├── frame_risk_engine.py
│   └── trip_aggregator.py
│
└── metrics_logger.py        # ⚡ ghi log tự động mọi kết quả eval
                              #    → metrics_log.json là input trực tiếp cho Output #04
```

**Nguyên tắc bắt buộc:** `run_inference.py` (sinh Output #01) và `demo/app.py` (sinh Output #03) **PHẢI import cùng 1 module** `core/`, tuyệt đối không copy-paste logic. Đây là cách rẻ nhất đảm bảo Demo và CSV không bao giờ lệch nhau.

---

## 3. NHÁNH → OUTPUT: THIẾT KẾ CHI TIẾT TỪNG NHÁNH

### 3.1 Nhánh Output #01 — CSV

```
scripts/run_inference.py
  1. Load data/redacted/T0Xd/
  2. Gọi core.challenge1.predict_ttc() + core.challenge2.predict_state() mỗi frame
  3. Gọi core.challenge3.* để tính risk/safe_score
  4. Ghi predictions/FPTU_DMS_Vision/T0Xd.csv (đúng path, đúng cột, không điền 0 giả)

scripts/self_check_eval.py
  1. Gọi evaluation.py của BTC trên CSV vừa xuất
  2. Ghi kết quả vào core/metrics_log.json  ← nuôi thẳng Output #04
```

Không có gì khác ngoài Core Engine + 2 script mỏng. Đây là nhánh **quan trọng nhất, đơn giản nhất, không được phép có thêm tầng trừu tượng nào khác** — càng đơn giản càng ít lỗi khi BTC chạy lại.

### 3.2 Nhánh Output #02 — Repo (chính là "cái hộp" chứa mọi nhánh khác)

Repo không phải một output tách biệt về mặt kỹ thuật — nó là **container vật lý** của toàn bộ 4 nhánh còn lại. Vai trò kiến trúc của nó là **đường biên rõ ràng giữa "phải có" và "làm giàu"**:

```
fptu-dms-vision/
├── core/                    # BẮT BUỘC — xương sống, dùng chung mọi nhánh
├── scripts/                 # BẮT BUỘC — sinh Output #01
├── demo/                    # BẮT BUỘC (chọn 1: app.py hoặc video link) — Output #03
├── predictions/              # BẮT BUỘC — chính là Output #01
├── configs/                 # BẮT BUỘC — minh chứng chống hard-code/overfit
├── data/sample/             # BẮT BUỘC — vài file mẫu, KHÔNG full dataset
├── README.md                # = Output #02
├── IMPLEMENTATION_NOTES.md  # = Output #04
├── USAGE.md                 # = Output #05
├── requirements.txt         # BẮT BUỘC
│
└── extensions/               # 🟢 TÙY CHỌN — chỉ làm nếu còn thời gian dư
    ├── edge_box/             #   (nội dung chi tiết: xem Mục 6 bên dưới)
    ├── fleet_dashboard/      #   demo/app.py có thể là bản rút gọn của cái này
    └── genai_coaching_live/
```

**Quyết định kiến trúc quan trọng nhất của tài liệu này:** mọi thứ trong `extensions/` là **optional, cô lập, không được import bởi `core/`** — nếu hết thời gian, xóa cả thư mục `extensions/` mà 4/5 output vẫn nguyên vẹn.

### 3.3 Nhánh Output #03 — Demo (tái dùng Core, không viết lại)

```
demo/app_streamlit.py
  1. Đọc predictions/FPTU_DMS_Vision/T0Xd.csv đã nộp (KHÔNG chạy lại model — đọc kết quả có sẵn)
     → đảm bảo Demo và CSV nộp bài là MỘT, không thể lệch nhau
  2. Trực quan hóa: risk timeline, driver state theo thời gian, TTC/near-miss marker
  3. (Nếu còn thời gian) Gọi trực tiếp core.challenge2.predict_state() trên 1 clip mẫu
     để demo "live" — dùng lại y nguyên hàm đã dùng cho Output #01
```

**Bậc thang mở rộng Demo (tùy thời gian còn lại, làm tới đâu dừng đó):**
1. *Tối thiểu:* Streamlit đọc CSV đã nộp, vẽ lại biểu đồ. (Đủ đạt Output #03)
2. *Khá:* thêm HUD giả lập cảnh báo (visual/audio) phát lại theo timestamp.
3. *Tốt:* thêm SHAP breakdown / Coaching Report (đã có schema JSON sẵn trong Master Plan gốc).
4. *Xuất sắc (dùng `extensions/fleet_dashboard/`):* map trực tuyến, driver ranking — chỉ làm nếu Pha 0–2 đã xong sớm.

### 3.4 Nhánh Output #04 — Implementation Notes (bán tự động)

```
core/metrics_logger.py ghi mỗi lần eval:
{
  "challenge_1": {"critical_region_mae": 1.8, "collision_f1": 0.71, ...},
  "challenge_2": {"accuracy": 0.89, "macro_f1": 0.71, "recall_microsleep": 0.68, ...},
  "challenge_3": {"mae_safe_score": 3.2, ...},
  "timestamp": "...", "git_commit": "..."
}
      ↓
scripts/generate_notes_draft.py
  → đọc metrics_log.json (bản mới nhất + lịch sử) → tự điền bảng số liệu
    vào IMPLEMENTATION_NOTES.md (phần "Điểm local"), người chỉ viết phần
    diễn giải định tính (kiến trúc, known issues) — không phải gõ tay số liệu
```

**Lợi ích kiến trúc:** số liệu trong Notes **luôn khớp với model mới nhất** vì được sinh từ log thật, không phải trí nhớ của người viết — tránh tình huống Notes ghi điểm cũ trong khi CSV nộp là bản mới hơn.

### 3.5 Nhánh Output #05 — Usage Notes (kiểm chứng bằng CLI thật)

```
USAGE.md không viết "tưởng tượng" các bước — mà được viết BẰNG CÁCH
copy chính xác lệnh đã chạy thành công từ scripts/run_inference.py
và scripts/self_check_eval.py, kèm output mẫu thực tế đã chạy.
```

Nguyên tắc kiến trúc: **Usage Notes = bản ghi lại (transcript) của một lần chạy thật trên máy sạch**, không phải văn bản hướng dẫn suy diễn — điều này tự động đảm bảo tính đúng đắn.

---

## 4. NGUYÊN TẮC "PRODUCT-FIRST" ĐÃ ĐƯỢC TÁI CẤU TRÚC NHƯ THẾ NÀO

| | Cách tiếp cận "sản phẩm hoàn chỉnh" (kiến trúc ban đầu) | Cách tiếp cận Output-Driven (file này) |
|---|---|---|
| Điểm xuất phát | "Hệ thống DMS hoàn chỉnh trông như thế nào" | "5 output cần gì để đạt điểm cao nhất" |
| Vai trò Edge box/API Gateway | Xương sống bắt buộc | Chuyển xuống `extensions/` (Mục 6), tùy chọn, chỉ phục vụ kể chuyện Demo |
| CSV và Demo | Không nói rõ có dùng chung code không | Bắt buộc dùng chung Core Engine (SSOT) — tránh lệch nhau |
| Implementation Notes | Việc viết tay riêng ở cuối kỳ | Bán tự động từ `metrics_logger.py`, cập nhật liên tục |
| Usage Notes | Hướng dẫn viết tay | Transcript từ lần chạy thật, kiểm chứng bằng CLI |
| Khi hết thời gian | Không rõ cắt gì trước (xem file 03 Mục 5) | Xóa cả `extensions/` — 4/5 output vẫn nguyên vẹn ngay lập tức |

> Toàn bộ tầm nhìn sản phẩm (edge box, dashboard, GenAI real-time) **không mất đi**, chỉ được **xếp đúng lớp ưu tiên** và nội dung chi tiết được gộp vào Mục 6 ngay dưới đây, để tài liệu này tự đứng độc lập.

---

## 5. QUY TẮC LÀM VIỆC THEO KIẾN TRÚC MỚI (áp dụng ngay cho team)

1. **Không ai được viết logic predict/risk ở 2 nơi khác nhau.** Nếu Demo cần hiển thị gì mà Core Engine chưa có, thêm hàm vào `core/`, rồi gọi từ cả `scripts/` lẫn `demo/` — không viết riêng cho Demo.
2. **Mọi lần chạy eval đều phải qua `metrics_logger.py`.** Không chạy notebook rời rạc rồi chép tay số liệu — dữ liệu cho Output #04 phải có nguồn gốc từ log tự động.
3. **`extensions/` là thư mục "hy sinh được".** Bất kỳ lúc nào áp lực thời gian tăng, việc đầu tiên bị cắt là các thứ trong đây, không đụng đến `core/`.
4. **README trỏ rõ ràng cho giám khảo biết đâu là bắt buộc, đâu là mở rộng** — ví dụ 1 dòng: "Phần `extensions/` là mở rộng minh họa tầm nhìn sản phẩm, không cần thiết để tái tạo file CSV đã nộp."

---

## 6. CHI TIẾT EXTENSION LAYER (tùy chọn — làm giàu Demo khi còn dư thời gian)

*Đây là toàn bộ thiết kế "sản phẩm hoàn chỉnh" — vẫn giá trị cho việc kể chuyện ở Output #03 và pitch, nhưng KHÔNG bắt buộc cho 5 output nộp bài.*

```
┌─────────────────────── ON-VEHICLE: DMS BOX (Edge) ───────────────────────┐
│  Road cam ─┐                                                              │
│  Face cam ─┼─► Core AI (ONNX/TensorRT FP16-INT8, 20 FPS)                  │
│  Telemetry┘   ├─ predict_ttc()  ├─ predict_driver_state()                 │
│               ▼                                                           │
│           Risk Fusion + Decision Engine                                   │
│               ├─► LOCAL WARNING (HUD visual + audio) ◄── real-time        │
│               └─► OFFLINE-FIRST QUEUE (buffer khi mất mạng)               │
└────────────────────────────────┬─────────────────────────────────────────┘
                                  │  sync khi có mạng (batch)
                                  ▼
┌─────────────────────── CENTRAL: BACKEND SERVICE ─────────────────────────┐
│  API Gateway (FastAPI: versioning, rate-limit, auth)                      │
│  ├─ Trip ingestion + storage (trip aggregate, risk timeline)             │
│  ├─ WebSocket stream → dashboard realtime                                 │
│  └─ GenAI Coaching (event-driven, per-trip) + rule fallback + cache       │
└────────────────────────────────┬─────────────────────────────────────────┘
                                  ▼
┌─────────────────────── FLEET DASHBOARD (Web/FE) ─────────────────────────┐
│  Live map · Driver ranking · Risk heatmap · Event timeline                │
│  Trip replay · Safe Driving Score 0–100 · Coaching Report (UBI/OEM)       │
└───────────────────────────────────────────────────────────────────────────┘
```

- **`extensions/edge_box/`** — mô phỏng vòng lặp Edge: đọc frame → gọi `core/` → hiển thị HUD giả lập (cửa sổ video có overlay cảnh báo) + hàng đợi offline-first (buffer JSON khi "mất mạng" giả lập). Không cần phần cứng thật, chỉ cần script minh họa đúng luồng.
- **`extensions/fleet_dashboard/`** — bản đầy đủ của `demo/app_streamlit.py`: thêm live map (dùng geolocation có sẵn trong dataset), driver ranking, risk heatmap.
- **`extensions/genai_coaching_live/`** — gọi LLM thật theo `coaching_agent.py` (event-driven, per-trip) thay vì dùng bản pre-render tĩnh; có `rule_fallback.py` khi API timeout.
- **Nguyên tắc "ăn tiền" của lớp này:** Edge làm việc gấp (cảnh báo tài xế tức thời), trung tâm làm việc nặng (phân tích batch, GenAI) — đúng tinh thần 3 nhóm đối tượng hưởng lợi (Tài xế / Fleet Manager / Bảo hiểm-OEM) đã nêu trong Master Plan gốc.
- **VLM (Alpamayo/Cosmos) nếu BTC cho phép dùng:** chỉ đặt ở `genai_coaching_live/`, không đưa vào `core/` — lõi real-time luôn dùng model nhẹ (YOLOv8n/MobileNetV3).

---

*Thứ tự dùng 4 tài liệu hiện có: file 01 (phân tích bài toán) → file 05 (tài liệu này, quyết định tổ chức code + toàn bộ thiết kế mở rộng ở Mục 6) → file 03 (lịch làm theo ngày) → file 04 (làm tới mức nào là đủ tốt).*
