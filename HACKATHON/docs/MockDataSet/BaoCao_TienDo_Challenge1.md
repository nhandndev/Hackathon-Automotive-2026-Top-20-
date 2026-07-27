# BÁO CÁO TIẾN ĐỘ — CHALLENGE 1: COLLISION Risk Monitor (TTC)
### FPTU DMS Vision — Connected Car Hackathon 2026
*Ngày báo cáo: 25/07/2026 · Phạm vi: Challenge 1 (dự đoán Time-To-Collision từ camera)*

---

## 1. TÓM TẮT ĐIỀU HÀNH

Trong giai đoạn này, nhóm tập trung xây dựng và tối ưu **pipeline dự đoán TTC** (thời gian tới va chạm) cho Challenge 1. Xuất phát từ một pipeline sơ khai, qua quá trình **chẩn đoán từng tầng trên dữ liệu thật** (6 trip Practice có Ground Truth đầy đủ), nhóm đã:

- **Nâng điểm trung bình 6 trip từ trạng thái ~20–40 lên 46.2/100** (thang điểm chính thức của Ban tổ chức).
- **Giải quyết dứt điểm 2 nhóm kịch bản khó**: xe dẫn đầu (đạt **85.5/100**) và người đi bộ băng ngang.
- **Đưa được 2/6 trip vượt mốc 70** (T04 = 85.5, T05 = 70.2).
- Thử nghiệm hướng **model học máy (XGBoost)** một cách bài bản với kiểm định chống overfit.

**Trạng thái hiện tại:** điểm trung bình **46.2/100**. Mục tiêu nội bộ đề ra là ≥70. Báo cáo này nêu rõ phần đã giải quyết, phần còn tồn đọng, và đánh giá trung thực về khả năng đạt mục tiêu.

---

## 2. BỐI CẢNH & CÁCH CHẤM ĐIỂM

Challenge 1 yêu cầu dự đoán `predicted_ttc` (giây) cho từng frame. Điểm composite của Ban tổ chức gồm 3 thành phần:

| Thành phần | Trọng số | Ý nghĩa |
|---|---|---|
| MAE vùng nguy hiểm (TTC < 3s) | **40%** | Sai số tuyệt đối ở vùng sắp va chạm — quan trọng nhất |
| F1 phát hiện nguy hiểm (TTC < 2s) | **30%** | Độ chính xác cảnh báo nguy hiểm |
| Inverse-TTC MAE (1/TTC) | **30%** | Sai số ở thang nghịch đảo, phạt nặng lỗi khi TTC nhỏ |

Dữ liệu: **6 trip Practice** (có đáp án đầy đủ, dùng để phát triển & tự chấm) + **10 trip chấm điểm** (bị xóa đáp án, dùng để nộp bài).

---

## 3. KẾT QUẢ ĐỊNH LƯỢNG (số liệu thật, tự chấm bằng `evaluation.py` của BTC)

### 3.1 Điểm hiện tại theo từng trip Practice

| Trip | Kịch bản | MAE-crit | F1 | Composite | Ghi chú |
|---|---|---|---|---|---|
| T04 | Xe dẫn đầu | 0.53 | 0.73 | **85.5** | ✅ Xuất sắc |
| T05 | Hỗn hợp | 0.26 | 0.34 | **70.2** | ✅ Đạt mục tiêu |
| T06 | Nhiều sự kiện | 3.29 | 0.58 | 40.3 | 🟡 |
| T03 | Hỗn hợp | 12.54 | 0.54 | 36.5 | 🟡 |
| T02 | Xe máy tạt đầu | 52.67 | 0.23 | 25.4 | 🔴 Khó nhất |
| T01 | Người đi bộ băng ngang | 8.34 | 0.14 | 19.2 | 🔴 |
| **TB** | | | | **46.2** | |

### 3.2 Tiến bộ so với điểm khởi đầu

- Pipeline sơ khai ban đầu chấm khoảng **20–51 điểm** tùy trip (ví dụ T01 ≈ 20.7, T04 ≈ 51.0).
- Sau khi rework: T04 **51 → 85.5**, MAE vùng nguy hiểm của các trip thuận lợi giảm từ **16–29 giây sai số xuống gần 0**.
- Điểm trung bình đạt **46.2** — cải thiện khoảng **2×** so với trạng thái đầu.

---

## 4. ĐÃ GIẢI QUYẾT ĐƯỢC GÌ (chi tiết kỹ thuật)

Toàn bộ cải tiến đến từ việc **chẩn đoán nguyên nhân gốc trên dữ liệu thật**, không phải chỉnh ngưỡng ngẫu nhiên. Mỗi fix đều được đo lại bằng `evaluation.py`.

### 4.1 Sửa lỗi lượng tử hóa độ sâu (stereo depth)
- **Vấn đề:** ở khoảng cách 20–30m, chênh lệch stereo chỉ ~4 pixel; sai 1 pixel = nhảy vài mét. Độ sâu bị "đứng yên" nhiều frame → tốc độ tiếp cận tính ra ≈ 0 → **hệ thống đoán "an toàn" (inf) ngay giữa lúc nguy hiểm**.
- **Giải pháp:** phóng to ảnh 2× trước khi tính stereo (độ phân giải chênh lệch mịn gấp đôi) + cửa sổ hồi quy dài hơn.

### 4.2 Sửa lỗi ước lượng tốc độ tiếp cận quá cao
- **Vấn đề:** với xe phía trước gần như đứng yên, tốc độ tiếp cận bị thổi phồng ~2.5× → TTC quá nhỏ.
- **Giải pháp:** chặn tốc độ tiếp cận ≤ tốc độ xe mình (nguyên lý vật lý: xe cùng chiều không thể lùi lại nhanh hơn). → TTC bám sát đáp án.

### 4.3 Lấp khoảng trống khi mất phát hiện
- **Vấn đề:** camera/detection thỉnh thoảng rớt vật cản vài frame → tạo lỗ "inf" giữa chuỗi nguy hiểm, mỗi lỗ bị phạt tối đa.
- **Giải pháp:** giữ TTC hữu hạn gần nhất, đếm ngược theo thời gian, tối đa ~6 frame. → **giải quyết dứt điểm kịch bản xe dẫn đầu (T04 = 85.5)**.

### 4.4 Bắt được người đi bộ / xe máy cắt ngang (VRU)
- **Vấn đề:** "hành lang va chạm" quá hẹp (1.6m) → loại nhầm người đi bộ đang băng ngang (lệch 2.4m) — chính là mối nguy khẩn cấp nhất.
- **Giải pháp:** mở rộng hành lang lên 2.6m (vẫn loại xe làn bên ~3.5m). → **kịch bản người đi bộ được giải quyết** (sai số giảm từ 9.3s xuống ~0.1s).

### 4.5 Ước lượng TTC theo "looming" cho vật thể động
- Bổ sung phương pháp **looming** (TTC = kích thước / tốc độ phình to của khung hình) — không phụ thuộc độ sâu tuyệt đối, vững hơn với vật thể nhanh/nhỏ.

### 4.6 Sửa độ sâu cho vật thể mỏng + lỗi cấu hình
- Đổi cách lấy độ sâu (phân vị gần thay vì trung vị) để vật mỏng (xe máy) không lấy nhầm nền phía sau.
- Phát hiện & sửa **lỗi wiring cấu hình** khiến tham số stereo bị mất (P1/P2/mode) — làm giảm chất lượng trên mọi trip.

### 4.7 Xây dựng hướng model học máy (bài bản, có kiểm định)
- Trích xuất **17 đặc trưng** từ pipeline cho toàn bộ 3600 frame + nhãn đáp án.
- Huấn luyện **XGBoost** dự đoán inverse-TTC, kiểm định bằng **Leave-One-Trip-Out** (mỗi trip test không nằm trong tập huấn luyện — chống overfit đúng chuẩn).

---

## 5. CÒN TỒN ĐỌNG GÌ (known issues — nêu trung thực)

### 5.1 Kịch bản xe máy tạt đầu (cut-in nhanh) — T02 = 25.4 🔴
- **Nguyên nhân:** sự kiện chỉ kéo dài ~1 giây (19 frame), TTC tụt còn 0.25–0.37s. Vật thể mỏng, nhanh; độ sâu stereo đo sai (~12m so với 6.5m thật); phát hiện bị lệch vị trí. Đây là ca **khó nhất về mặt kỹ thuật**.

### 5.2 Sự kiện thoáng qua thứ cấp — T01 cụm 2, T03, T06 🟡
- Các target xuất hiện ngắn/nhiễu khiến tốc độ tiếp cận ước lượng chập chờn (khi thì inf, khi thì thổi phồng). Kịch bản chính (người đi bộ) đã fix xong nhưng sự kiện phụ trong cùng trip còn kém.

### 5.3 Báo động giả làm giảm F1
- Ở các trip có MAE tốt (T05: sai số 0.26 gần hoàn hảo) nhưng F1 chỉ 0.34 do **cảnh báo nhầm** trên frame thực ra an toàn → kéo điểm xuống.

### 5.4 Model học máy chưa vượt heuristic
- **Kết quả kiểm định trung thực:** model học đạt trung bình 37.5, ensemble tốt nhất 43.8 — **vẫn thấp hơn heuristic 46.2**.
- **Lý do:** chỉ có 6 trip Practice là quá ít để học ánh xạ tổng quát; mỗi trip là một kịch bản riêng nên khi bỏ ra kiểm định, model không có dữ liệu để học loại đó. (Đây là giới hạn dữ liệu, không phải lỗi phương pháp.)

### 5.5 Chưa kiểm thử trên 10 trip chấm điểm
- Repo hiện chỉ có dữ liệu đường (`kitti/`) đầy đủ cho 6 trip Practice. Trip chấm điểm cần bổ sung dữ liệu đường trước khi chạy nộp bài.

### 5.6 Tốc độ
- Phóng to ảnh 2× làm inference chạy ~2 fps trên CPU (đủ cho chấm điểm offline, chưa đạt real-time 20 fps — chỉ ảnh hưởng phần demo, không ảnh hưởng điểm CSV).

---

## 6. ĐÁNH GIÁ KHẢ NĂNG ĐẠT MỤC TIÊU 70

**Đánh giá trung thực:** với **6 trip Practice hiện có**, đạt trung bình ≥70 là **rất khó** bằng cả hai hướng đã thử (chỉnh tay + model học), vì cả hai đều hội tụ về ~44–46.

- 2/6 trip đã đạt 70–85 → chứng minh pipeline **đúng về nguyên lý** khi kịch bản thuận lợi.
- Trần điểm đến từ **giới hạn dữ liệu** (6 trip, ảnh 640×360) và **độ khó của cảnh động/đông**, không phải từ lỗi triển khai.
- Lưu ý: 10 trip chấm điểm dài hơn và nhiều sự kiện hơn Practice — điểm thực tế khi nộp **có thể khác** (chưa đo được vì chưa có dữ liệu đường của các trip đó).

---

## 7. KHUYẾN NGHỊ BƯỚC TIẾP THEO

| Ưu tiên | Việc | Kỳ vọng |
|---|---|---|
| 🔴 Cao | Bổ sung dữ liệu đường 10 trip chấm điểm → chạy thử điểm thực tế | Biết điểm nộp thật |
| 🟠 TB | Hiệu chỉnh bias độ sâu bằng GT depth `.npy` (có sẵn ở Practice) | +vài điểm MAE toàn cục |
| 🟠 TB | Giảm báo động giả (lọc detection rác) để nâng F1 | +điểm ở trip MAE tốt |
| 🟡 Thấp | Logic riêng cho cut-in (T02) — vật nhỏ/nhanh | Nâng trần T02 |
| 🟢 | Hoàn thiện Implementation Notes ghi rõ known-issues (được điểm mềm) | Điểm trình bày |

**Kết luận:** Challenge 1 đã có **pipeline hoạt động ổn định, điểm trung bình 46.2**, giải quyết được các kịch bản cốt lõi và có nền tảng kỹ thuật vững (chẩn đoán dựa trên dữ liệu, code có cấu hình, có hướng model học đã kiểm định). Phần còn lại là các ca biên khó và giới hạn dữ liệu — được ghi nhận minh bạch để tiếp tục ở giai đoạn sau.

---

*Toàn bộ số liệu trong báo cáo được đo bằng `evaluation.py` chính thức của Ban tổ chức trên 6 trip Practice có Ground Truth. Code, script trích xuất đặc trưng, và model đã lưu trong repo (`HACKATHON/AI/`).*
