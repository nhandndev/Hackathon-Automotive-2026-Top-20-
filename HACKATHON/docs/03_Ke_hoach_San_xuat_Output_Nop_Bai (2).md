# KẾ HOẠCH SẢN XUẤT OUTPUT NỘP BÀI (5 PHẦN)
### FPTU DMS Vision — Connected Car Hackathon 2026
*Tư duy ngược: xuất phát từ 5 thứ phải nộp → suy ngược ra việc phải làm mỗi ngày. Không lạc sang việc "hay" nhưng không ra output.*

---

## 0. NGUYÊN TẮC SẢN XUẤT OUTPUT

1. **Làm ngược từ vạch đích.** 5 phần nộp bài là **định nghĩa duy nhất của "xong"**. Bất kỳ việc gì không dẫn tới 1 trong 5 phần này đều là việc phụ, làm sau.
2. **Luôn có bản nộp được từ rất sớm (Day 2)** — dù là baseline yếu — rồi mới nâng chất lượng. Không bao giờ để ở trạng thái "chưa nộp được gì".
3. **4 phần (Repo/Demo/Notes/Usage) có thể viết ngay cả khi model còn yếu** — chúng mô tả *quá trình*, không phải *kết quả cuối*. Bắt đầu viết từ Day 1, cập nhật dần, không dồn vào ngày cuối.
4. **Tự chấm trước khi nộp thật** — `evaluation.py` của BTC là nguồn sự thật duy nhất, chạy nó sau mỗi lần cải tiến, không đoán điểm.
5. **1 người là "Submission Owner"** — chịu trách nhiệm duy nhất đảm bảo 5 phần luôn ở trạng thái nộp được, không phải chờ "cả team xong mới ráp" (thường gán cho Lead).

---

## 1. MA TRẬN 5 OUTPUT → VIỆC PHẢI LÀM → NGƯỜI SỞ HỮU

| # | Output nộp bài | Việc cụ thể để tạo ra nó | Người | Bắt đầu | Deadline nội bộ |
|---|------------------|---------------------------|-------|---------|------------------|
| 01 | `predictions/FPTU_DMS_Vision/T01d.csv`…`T10d.csv` | Chạy `run_baseline.py` → sau đó `run_inference.py` với model thật, ghi đúng path & cột | AI-Road, AI-Driver, BE | Day 2 (baseline) | Day 12 (bản cuối) |
| 02 | GitHub Repo (`README.md` + code + `requirements.txt`) | Dựng repo, viết README dần theo tiến độ, `.gitignore` dataset gốc | Lead | Day 1 | Day 13 |
| 03 | Demo (video HOẶC dashboard) | Chọn 1 hình thức ngay Day 3; dựng khung sớm, đổ nội dung dần | FE | Day 3 (chọn) | Day 13 |
| 04 | `IMPLEMENTATION_NOTES.md` | Ghi ngay sau mỗi milestone model — không hồi tưởng cuối kỳ | AI-Road, AI-Driver, BE (Lead tổng hợp) | Day 1 (khung), cập nhật liên tục | Day 13 |
| 05 | `USAGE.md` | Viết song song lúc code chạy được, test lại bằng máy sạch | Lead | Day 2 (khung), cập nhật liên tục | Day 13 |

> **Chìa khóa:** Output #02, #04, #05 là **tài liệu sống** — viết từ ngày đầu, không phải task "làm sau cùng". Chỉ #01 (CSV) và #03 (Demo) cần chờ model chín.

---

## 2. LỊCH SẢN XUẤT THEO NGÀY (bám roadmap kỹ thuật, nhưng nhìn qua lăng kính "ra output")

### 📍 Day 1 — Khởi động & khung tài liệu sống

- [ ] Lead: tạo repo GitHub, cấu trúc thư mục (theo file 05 Mục 3.2: `core/`, `scripts/`, `demo/`, `extensions/`), `.gitignore` (loại dataset gốc, cache, model weight lớn).
- [ ] Lead: viết khung `README.md` (mục lục rỗng: Approach, Setup, Run, Demo link, Team).
- [ ] Lead: viết khung `IMPLEMENTATION_NOTES.md` với 3 mục trống: Challenge 1 / 2 / 3 — mỗi mục có sẵn khung "Kiến trúc – Thuật toán – Dữ liệu train thêm – Known issues – Compute time".
- [ ] Lead: viết khung `USAGE.md` (Setup – Run step-by-step – External model/data & license).
- [ ] AI-Road/AI-Driver: lấy script `baseline_ttc_predictor.py` của BTC chạy thử trên 6 trip Practice.

**Output cuối ngày:** repo tồn tại, 3 file tài liệu có khung (chưa đầy nội dung — không sao).

### 📍 Day 2 — Bản nộp CSV đầu tiên (an toàn tối thiểu)

- [ ] Chạy baseline BTC trên 10 trip redacted → xuất `predictions/FPTU_DMS_Vision/T0Xd.csv` **thật**, đúng path/cột/số dòng (1,800 dòng + header).
- [ ] Lead: viết `self_check_eval.py` gọi `evaluation.py` của BTC → xác nhận CSV baseline chạy được, không lỗi format.
- [ ] Ghi kết quả điểm baseline vào `IMPLEMENTATION_NOTES.md` (mốc so sánh sau này).
- [ ] BE: dựng mock `predict_ttc()`/`predict_driver_state()` để không ai bị chặn.

**✅ Chốt an toàn Day 2:** Nếu mọi thứ đứng yên từ đây, **đội vẫn có 1 bản nộp hợp lệ** (điểm thấp nhưng không phải 0/lỗi format).

### 📍 Day 3–4 — Chọn hình thức Demo + bắt đầu code lõi thật

- [ ] FE: **quyết định ngay** Demo là Streamlit/Gradio dashboard hay video — không để "cả hai" lãng phí thời gian. Khuyến nghị: **Streamlit đơn giản** (đọc CSV đã nộp, vẽ lại risk timeline + driver state) — vừa là demo vừa reuse cho Fleet Dashboard.
- [ ] FE: dựng khung `demo/app_streamlit.py` chạy được (dù dữ liệu là mock) — commit sớm để không rớt deadline vì "chưa kịp làm demo".
- [ ] AI-Road: bắt đầu detector + TTC thật.
- [ ] AI-Driver: bắt đầu MediaPipe + Grid Search ngưỡng EAR/MAR/PERCLOS trên GT Practice.

**Output cuối Day 4:** demo chạy được (dù dữ liệu giả), pipeline AI thật đã bắt đầu có kết quả sơ bộ.

### 📍 Day 5–8 — Core AI/Fusion thật + cập nhật tài liệu liên tục

- [ ] AI-Road/AI-Driver/BE: hoàn thiện `predict_ttc()` (ByteTrack + collision cone), `predict_driver_state()` (Focal Loss + class-aware sampler, bảo vệ lớp hiếm), `frame_risk_engine`, `trip_aggregator` — chiến thuật chi tiết theo trọng số từng Challenge xem file 04 Mục 1.
- [ ] **Sau mỗi lần model cải thiện:** chạy lại `run_inference.py` → `self_check_eval.py` → cập nhật điểm số & mô tả vào `IMPLEMENTATION_NOTES.md` ngay (không dồn cuối).
- [ ] Lead: cập nhật `README.md` phần Approach khi kiến trúc đã rõ ràng (không chờ code xong 100%).
- [ ] FE: đổ dữ liệu thật vào demo Streamlit thay cho mock.

**✅ Chốt an toàn Day 8:** CSV nộp bài đã dùng model thật (không còn baseline thuần), điểm local > baseline rõ rệt; demo chạy trên dữ liệu thật.

### 📍 Day 9–11 — Tối ưu điểm + hoàn thiện 4 tài liệu song song

- [ ] Cả team AI: tối ưu ngưỡng, calibration (hold-out 4 trip calib/2 trip validate), 22 edge-case đã liệt kê ở file 01 Mục 4.4 → mỗi lần cải thiện → re-run `self_check_eval.py`.
- [ ] Lead: hoàn thiện `README.md` đầy đủ (Approach chi tiết, hướng dẫn chạy lại từ đầu, link demo).
- [ ] Lead: hoàn thiện `USAGE.md` — **test thực tế trên máy sạch** (venv mới, clone repo mới, làm đúng theo hướng dẫn) để đảm bảo BTC làm theo không bị lỗi.
- [ ] Team: hoàn thiện `IMPLEMENTATION_NOTES.md` — ghi rõ known issues còn tồn (đừng giấu), thời gian train/GPU đã dùng.
- [ ] Nếu có pretrained model / data ngoài → ghi rõ nguồn + license ngay trong `USAGE.md`.

**✅ Chốt an toàn Day 11:** cả 5 phần đã có nội dung đầy đủ (không còn khung rỗng), dù chưa polish.

### 📍 Day 12 — CSV cuối cùng + Freeze code

- [ ] Chạy `run_inference.py` **bản cuối** trên 10 trip redacted → CSV final.
- [ ] Chạy `self_check_eval.py` lần cuối, ghi điểm local vào Notes.
- [ ] Kiểm tra CSV: đúng 1,800 dòng/trip + header, đúng 5 cột, **không điền số 0 giả** cho challenge chưa làm.
- [ ] Freeze code — không sửa logic core nữa, chỉ sửa tài liệu/demo.
- [ ] Xóa dataset gốc khỏi repo (nếu lỡ commit), chỉ giữ `data/sample/` vài file mẫu.

### 📍 Day 13 — Dry-run nộp bài đầy đủ (diễn tập như BTC sẽ làm)

- [ ] **Submission Owner (Lead)** đóng vai BTC: clone repo mới tinh vào máy sạch → làm đúng theo `USAGE.md` từ A–Z → xác nhận ra đúng CSV đã nộp.
- [ ] Mở demo (Streamlit link hoặc video) → xác nhận chạy được/xem được.
- [ ] Đọc lại `README.md` + `IMPLEMENTATION_NOTES.md` như người ngoài lần đầu đọc — sửa chỗ khó hiểu.
- [ ] Chạy checklist G.6 (bên dưới) — tick đủ 10 mục.

### 📍 Day 14 — Buffer + Nộp

- [ ] Buffer cho phát sinh (link demo die, repo private thiếu invite, v.v.).
- [ ] Nộp chính thức + chuẩn bị pitch (nếu vòng 2 có thuyết trình).

---

## 3. TEMPLATE NỘI DUNG CHO 3 FILE TÀI LIỆU (viết ngay, không phải nghĩ từ đầu)

### `README.md`

```markdown
# FPTU DMS Vision — Connected Car Hackathon 2026

## 1. Approach
[Tóm tắt kiến trúc pipeline: primitive → fusion(1) → fusion(2) → decision.
Mỗi Challenge làm gì, dùng model/thuật toán gì — 3-5 dòng mỗi challenge]

## 2. Cấu trúc Repo
[Sơ đồ cây thư mục ngắn gọn, trỏ tới file 05 Mục 3.2 nếu cần chi tiết]

## 3. Cách chạy lại (Quick Start)
Xem chi tiết đầy đủ tại `USAGE.md`. Tóm tắt:
​```bash
pip install -r requirements.txt
python scripts/run_inference.py --trips redacted --out predictions/FPTU_DMS_Vision/
python scripts/self_check_eval.py
​```

## 4. Demo
- Link dashboard: [...] hoặc
- Video demo: [...]

## 5. Team
[Tên team, thành viên, vai trò]
```

### `IMPLEMENTATION_NOTES.md`

```markdown
# Implementation Notes

## Challenge 1 — Collision Risk Monitor (TTC)
- Kiến trúc: YOLOv8-nano (detection) + [monocular/stereo] depth + ByteTrack
- Thuật toán TTC: [công thức, min_ttc trong collision cone]
- Train thêm dữ liệu ngoài: [có/không, nguồn nếu có]
- Known issues: [vd: domain shift CARLA→thực tế làm giảm độ chính xác khi ánh sáng yếu]
- Compute/training time: [vd: 3h trên GPU T4]

## Challenge 2 — Driver Intelligence (DMS)
- Kiến trúc: MediaPipe Face Mesh + [MobileNetV3/ResNet18] + Focal Loss
- Ngưỡng: EAR=..., MAR=..., PERCLOS window=...s (chốt bằng Grid Search trên Practice)
- Known issues: [vd: lớp microsleep vẫn có Recall thấp do dữ liệu hiếm]
- Compute/training time: [...]

## Challenge 3 — Fleet Safe Driving Score
- Công thức fusion: base_risk × driver_factor, penalty theo barem BTC
- Calibration: hold-out 4 trip calib / 2 trip validate
- Known issues: [vd: chưa xử lý triệt để double-count khi rule chồng lấn]
- Compute time: [...]

## Điểm local (self-check qua evaluation.py BTC)
| Challenge | Điểm baseline | Điểm hiện tại |
|-----------|---------------|----------------|
| 1 | 19.7 | ... |
| 2 | 13.9 | ... |
| 3 | 100 | ... |
```

### `USAGE.md`

```markdown
# Usage Notes

## 1. Environment
- Python: 3.10+
- Cài đặt:
​```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
​```

## 2. Chạy để ra file CSV dự đoán
​```bash
# Bước 1: trích xuất feature
python scripts/extract_features.py --input data/redacted --out data/interim

# Bước 2: chạy inference, xuất CSV nộp bài
python scripts/run_inference.py --out predictions/FPTU_DMS_Vision/

# Bước 3: tự chấm để kiểm tra (dùng evaluation.py của BTC)
python scripts/self_check_eval.py --pred predictions/FPTU_DMS_Vision/
```

## 3. Pretrained model / dữ liệu ngoài
- [Tên model] — nguồn: [link] — license: [MIT/Apache/...]
- (Nếu không dùng gì ngoài dataset hackathon, ghi rõ "Không sử dụng pretrained/data ngoài".)
```

---

## 4. CHECKLIST TRƯỚC KHI BẤM NỘP (dry-run Day 13)

| # | Việc kiểm tra | Người kiểm | Đạt? |
|---|-----------------|--------------|------|
| 1 | 10 file CSV đúng path `predictions/FPTU_DMS_Vision/T0Xd.csv`, đúng 1,800 dòng+header | Lead | ☐ |
| 2 | CSV không có số 0 giả cho challenge không làm (nếu có) | Lead | ☐ |
| 3 | `self_check_eval.py` chạy evaluation.py BTC không lỗi | Lead | ☐ |
| 4 | Clone repo mới + làm theo `USAGE.md` ra đúng CSV | 1 người ngoài team AI | ☐ |
| 5 | `requirements.txt`/`environment.yml` cài đủ, không thiếu lib | Người test | ☐ |
| 6 | Dataset gốc KHÔNG có trong repo (`git log --stat` kiểm tra) | Lead | ☐ |
| 7 | Demo mở được (link sống hoặc video phát được) | FE | ☐ |
| 8 | `README.md` đọc hiểu được trong 2 phút | Người ngoài team | ☐ |
| 9 | `IMPLEMENTATION_NOTES.md` có known issues thật, không giấu | Lead | ☐ |
| 10 | Nguồn/license pretrained model (nếu có) đã ghi rõ | Lead | ☐ |

---

## 5. NẾU TRỄ TIẾN ĐỘ — THỨ TỰ HY SINH

Khi thời gian cạn, cắt theo thứ tự này (không cắt ngược):

1. Cắt trước: polish UI Demo → chuyển sang **video quay nhanh 2 phút** thay vì dashboard hoàn chỉnh.
2. Cắt tiếp: edge-case hiếm gặp trong AI (giữ lại core rule an toàn nhất — không bỏ sót microsleep).
3. Cắt tiếp: GenAI coaching live → dùng **rule-based fallback** làm chính, ghi rõ trong Notes.
4. **KHÔNG BAO GIỜ cắt:** CSV đúng format, README, USAGE, self-check bằng evaluation.py. Đây là 4 thứ quyết định có bị loại vì lỗi kỹ thuật hay không.

---

*Tài liệu này biến kiến trúc (file 05) thành lịch hành động ngày-qua-ngày. Dùng song song: file 01 (phân tích bài toán) → file 05 (kiến trúc output-driven) → file 03 (kế hoạch sản xuất output, tài liệu này) → file 04 (chiến lược tối đa hóa điểm).*
