# CHIẾN LƯỢC TỐI ĐA HÓA ĐIỂM SỐ — 5 OUTPUT NỘP BÀI
### FPTU DMS Vision — Connected Car Hackathon 2026
*Khác với file 03 (lịch sản xuất "ra được output"), tài liệu này trả lời: với cùng lượng thời gian, làm gì để MỖI output đạt điểm/ấn tượng cao nhất — không chỉ "đạt", mà "hơn đối thủ".*

---

## 0. PHÂN BIỆT 2 LOẠI ĐIỂM — chiến lược phải tách bạch

| Loại điểm | Đến từ đâu | Có thể tối ưu bằng gì |
|-----------|------------|------------------------|
| **Điểm cứng** | `evaluation.py` chấm tự động trên CSV (Output #01) | Toán học, calibration, ngưỡng — khách quan, đo được |
| **Điểm mềm** | Giám khảo đọc Repo/Demo/Notes (Output #02–05) | Ấn tượng chuyên nghiệp, tính minh bạch, product mindset, dễ tái tạo |

**Sai lầm phổ biến:** đổ 100% lực vào điểm cứng (CSV) mà bỏ bê điểm mềm — trong khi điểm mềm là thứ **rẻ để tối ưu** (không cần train lại model) nhưng **ảnh hưởng trực tiếp đến việc lọt vòng trong** (thường có tiêu chí đánh giá riêng ngoài barem CSV). Chiến lược ở đây là tối ưu **cả hai song song**, ưu tiên theo ROI (Mục 6).

---

## 1. OUTPUT #01 — TỐI ĐA ĐIỂM CỨNG CỦA FILE CSV

Đây là output duy nhất có công thức toán học rõ ràng — tối ưu theo đúng trọng số, không dàn trải đều.

### 1.1 Challenge 1 (TTC) — phân bổ lực theo đúng trọng số 40/30/30

| Thành phần | Trọng số | Chiến thuật tối đa hóa |
|------------|----------|--------------------------|
| **Critical Region MAE** | 40% | **Đây là nơi đầu tư nhiều nhất.** Xây riêng 1 tập validation chỉ gồm frame có `TTC_gt ≤ 3s` (vùng nguy hiểm), tối ưu model/threshold **riêng** cho vùng này thay vì tối ưu MAE trung bình toàn bộ. Tuyệt đối cấm model đoán `inf` khi GT ở vùng nguy hiểm — thà đoán một số TTC lớn sai còn hơn đoán `inf` (bị phạt tối đa). |
| **Collision Threat Score (Precision/Recall nhị phân)** | 30% | Test nhiều threshold phân loại "có nguy cơ" trên tập Practice, chọn điểm cân bằng Precision/Recall (không chọn theo cảm tính). Ưu tiên **Recall cao hơn Precision một chút** — bỏ sót nguy hiểm (FN) thường bị phạt nặng hơn báo động giả (FP) trong bài toán an toàn. |
| **Inverse-TTC MAE (1/TTC)** | 30% | Vì công thức nghịch đảo phạt nặng sai số ở TTC nhỏ, **không được làm tròn/clip TTC nhỏ về một giá trị an toàn** — phải cố dự đoán chính xác đến từng 0.1s khi TTC < 2s. Đầu tư thêm Kalman filter/temporal smoothing ở vùng TTC nhỏ để giảm nhiễu giật cục giữa các frame liên tiếp. |

**Chiến thuật xuyên suốt Ch1:** dùng `min_ttc` trong **collision cone thực sự** (không lấy TTC của target ở làn khác) — đây là lỗi rẻ tiền nhất nhưng gây mất điểm nhiều nhất nếu làm sai.

### 1.2 Challenge 2 (Driver State) — trọng tâm là bẫy Macro-F1, không phải Accuracy

| Thành phần | Trọng số | Chiến thuật tối đa hóa |
|------------|----------|--------------------------|
| **Accuracy** | 50% | Tự nhiên cao nếu model tốt ở lớp `alert` (chiếm đa số) — **không cần đầu tư thêm**, đây không phải chỗ tạo khác biệt điểm số. |
| **Macro-F1 (5 lớp, không trọng số)** | 50% | **Đây là nơi quyết định thắng-thua.** Chiến thuật cụ thể: <br>1. **Class-aware sampler** ép tỉ lệ 5 lớp cân bằng trong mini-batch khi train.<br>2. **Focal Loss** (γ=2) thay Cross-Entropy thường, gán trọng số cao hơn cho `microsleep`/`drowsy`.<br>3. Sau khi train, **kiểm tra riêng Confusion Matrix của 2 lớp hiếm** — nếu Recall(microsleep) = 0 thì dù Accuracy 95% vẫn tụt điểm nặng. Đây là chỉ số PHẢI theo dõi, không phải Accuracy tổng.<br>4. Augmentation nhân bản dữ liệu 2 lớp hiếm (crop, color jitter) để tăng số mẫu train. |

**Chiến thuật xuyên suốt Ch2:** báo cáo **Macro-F1 riêng từng lớp** trong quá trình dev (không chỉ số tổng) — đây là cách duy nhất phát hiện sớm model đang "học vẹt" thiên về `alert`.

### 1.3 Challenge 3 (Safe Score) — độ mịn calibration quyết định tất cả

Công thức: mỗi 1 điểm sai lệch so với GT = trừ trực tiếp 1 điểm trên thang 100. **Đây là challenge nhạy nhất với calibration, không nhạy với độ phức tạp model.**

**Chiến thuật tối đa hóa:**
1. **Hold-out nghiêm ngặt:** chia 6 trip Practice thành 4 trip calib / 2 trip validate — tinh chỉnh trọng số phạt (5.0/3.0/2.0/2.0/0.15/0.10) trên 4 trip, rồi **chỉ khóa số khi MAE trên 2 trip validate ổn định**. Không tinh chỉnh trực tiếp trên nhìn kết quả 10 trip thi (dễ overfit, sập điểm thi thật).
2. **Test độ nhạy (sensitivity analysis):** thử lệch mỗi trọng số ±20% xem Safe Score dao động bao nhiêu — trọng số nào gây dao động lớn thì đầu tư calib kỹ hơn cho input tương ứng (vd nếu `harsh_brake_count` nhạy nhất, đầu tư thêm cho detection harsh brake chính xác hơn là cho near_miss).
3. **Chống double-count (rủi ro D19 trong file 01):** viết test case cụ thể tình huống chồng lấn (vừa phanh gấp vừa gần vật cản) để đảm bảo không trừ điểm 2 lần cho cùng 1 nguyên nhân — sai ở đây gây lệch điểm hệ thống, không phải lệch ngẫu nhiên.
4. **An toàn hơn là "chính xác tuyệt đối":** vì phạt tuyến tính theo |error|, nên nếu không chắc, **thiên về đoán gần trung bình lịch sử** (tránh outlier cực đoan) thay vì đoán liều một hướng — giảm rủi ro sai lớn.

### 1.4 Chiến thuật chung cho toàn bộ Output #01

- **Ensemble nhẹ nếu có thời gian:** trung bình 2-3 checkpoint model khác nhau cho Ch2 thường tăng Macro-F1 ổn định hơn 1 model đơn.
- **Temporal smoothing hậu xử lý:** dự đoán frame-by-frame xong, làm mượt qua cửa sổ 3-5 frame (majority vote cho driver_state, moving average cho TTC) để giảm nhiễu giật — thường tăng điểm miễn phí không cần train lại.
- **Tự chấm sau MỌI thay đổi:** chạy `evaluation.py` sau mỗi lần chỉnh — không đoán, không "cảm thấy chắc là tốt hơn".

---

## 2. OUTPUT #02 — TỐI ĐA ẤN TƯỢNG TỪ GITHUB REPOSITORY

Giám khảo đọc repo trong **vài phút**, không phải vài giờ. Tối ưu cho tốc độ hiểu và tốc độ chạy thử.

**Chiến thuật:**
1. **README mở đầu bằng kết quả, không phải giới thiệu dài dòng** — 3 dòng đầu tiên: bài toán, kết quả điểm local, 1 câu định vị sản phẩm ("không chỉ CSV mà là nền tảng Fleet Risk Intelligence"). Giám khảo quyết định ấn tượng trong 10 giây đầu.
2. **1 lệnh duy nhất chạy được** (`make submit` hoặc `python run_all.py`) thay vì nhiều bước rời rạc — giảm khả năng BTC gặp lỗi giữa chừng và đánh giá thấp vì "không chạy được".
3. **Sơ đồ kiến trúc trong README** (dùng lại sơ đồ Core Engine → 5 Output từ file 05 Mục 1) — giám khảo kỹ thuật đánh giá cao khi thấy tư duy hệ thống rõ ràng, không chỉ là script rời rạc.
4. **Commit history sạch, có ý nghĩa** — tránh 1 commit "final final v2 thật sự", nên có lịch sử cho thấy quá trình lặp (calibration, fix bug) — tạo tín hiệu đáng tin cậy về quá trình làm việc thật.
5. **Badge/status nhỏ** (Python version, license) — chi tiết rẻ tiền nhưng tạo cảm giác chuyên nghiệp.
6. Tách rõ `configs/*.yaml` khỏi code — giám khảo kỹ thuật nhìn thấy ngay đây là hệ thống **có thể mở rộng**, không phải hard-code cho riêng 10 trip thi (tín hiệu chống overfit).

---

## 3. OUTPUT #03 — TỐI ĐA "WOW FACTOR" TỪ DEMO

Đây là output **duy nhất** cho phép thể hiện tầm nhìn sản phẩm (Mục 2 trong tài liệu gốc: Driver/Fleet Manager/Bảo hiểm) — điểm khác biệt lớn nhất so với đội chỉ nộp CSV thuần.

**Chiến thuật:**
1. **Kể chuyện theo 3 đối tượng hưởng lợi**, không chỉ demo tính năng rời rạc: mở đầu bằng HUD cảnh báo tài xế (visual/audio) → chuyển sang Fleet Dashboard (map, ranking, timeline) → kết bằng Coaching Report GenAI cho bảo hiểm/OEM. Đây đúng cấu trúc "Product Mindset" đã nêu trong Mục I.2 của Master Plan — tận dụng lại, đừng bỏ phí.
2. **Dùng đúng dữ liệu đã nộp CSV** trong demo (không dùng số liệu giả) — chứng minh demo và CSV nộp bài là **cùng một hệ thống thật**, tăng độ tin cậy.
5. **Nếu chọn video:** 2-5 phút chia rõ 3 phân đoạn theo 3 đối tượng ở trên, có giọng nói giải thích ngắn gọn "tại sao" chứ không chỉ "cái gì" (vd: "Nhóm phát hiện tài xế vi ngủ tại giây 450, phanh gấp theo sau — hệ thống tự động cảnh báo trước 1.2s").
4. **Nếu chọn dashboard:** ưu tiên Streamlit đơn giản chạy mượt hơn là dashboard đẹp nhưng dễ lỗi khi BTC tự bấm thử — **độ ổn định quan trọng hơn thẩm mỹ** vì BTC tự trải nghiệm, không phải xem trình diễn.
5. **1 tính năng "đắt tiền" duy nhất làm điểm nhấn** thay vì dàn trải: ví dụ SHAP breakdown giải thích tại sao trip bị trừ điểm (đã có sẵn schema trong Master Plan Mục VI.3) — đây là chi tiết ít đội nghĩ tới, tạo khác biệt rõ.

---

## 4. OUTPUT #04 — TỐI ĐA CHIỀU SÂU KỸ THUẬT TRONG IMPLEMENTATION NOTES

Giám khảo dùng file này để phân biệt "đội hiểu bài toán" và "đội chỉ chạy được code mẫu".

**Chiến thuật:**
1. **Định lượng, không mô tả chung chung.** Thay vì "chúng em dùng Focal Loss để cải thiện", viết: "Focal Loss (γ=2) tăng Recall lớp `microsleep` từ 0.31 → 0.68, kéo Macro-F1 từ 0.54 → 0.71". Con số cụ thể luôn thuyết phục hơn tính từ.
2. **Ghi rõ known issues thật** (yêu cầu chính thức của BTC) — nghịch lý là **thừa nhận hạn chế đúng cách lại tăng điểm mềm**, vì nó chứng minh nhóm hiểu sâu, không phải "giấu dốt". Ví dụ: "Model Ch1 giảm ~8% mAP trong điều kiện sương mù do domain shift CARLA↔thực tế, chưa kịp augment đủ dữ liệu sương mù trước hạn nộp."
3. **Trình bày phương pháp luận calibration** (hold-out 4/2, sensitivity analysis) — đây là tín hiệu mạnh cho thấy nhóm hiểu rủi ro overfitting, một trong 11 hạn chế kỹ thuật đã tự nhận diện trong Master Plan Mục VII.10.
4. **Liên kết ngược về công thức chấm điểm BTC** — ví dụ ghi rõ "chúng em ưu tiên Recall hơn Precision ở Ch1 vì hiểu rằng bỏ sót vùng nguy hiểm (Critical Region) bị phạt nặng hơn theo barem BTC" — cho thấy chiến thuật có chủ đích, không phải ngẫu nhiên.

---

## 5. OUTPUT #05 — TỐI ĐA ĐỘ TIN CẬY TỪ USAGE NOTES

Ít "hào nhoáng" nhất nhưng **rủi ro mất điểm oan nếu sai** cao nhất — vì nếu BTC làm theo mà lỗi, ấn tượng xấu lan sang toàn bộ đánh giá.

**Chiến thuật:**
1. **Test trên máy hoàn toàn sạch** (venv mới/máy ảo mới) ít nhất 2 lần trước khi nộp — không tự tin rằng "chạy được trên máy tôi".
2. **Không dùng đường dẫn tuyệt đối cá nhân** trong code/config (dấu hiệu thường thấy khiến script BTC chạy bị lỗi ngay).
3. **Ghi rõ thời gian chạy dự kiến** mỗi bước (vd "bước inference mất ~15 phút trên GPU T4, ~40 phút trên CPU") — giúp BTC không tưởng nhầm là treo máy.
4. **Với license pretrained model:** liệt kê minh bạch dù nhỏ (kể cả model nhẹ như YOLOv8n) — thiếu sót này dễ bị đánh giá là không chuyên nghiệp dù không cố ý.

---

## 6. MA TRẬN ƯU TIÊN ROI (đầu tư thời gian vào đâu trước)

| Hạng mục | Effort cần | Tác động điểm | Ưu tiên |
|----------|-------------|------------------|---------|
| Macro-F1 lớp hiếm (Ch2: Focal Loss + sampler) | Trung bình | Rất cao (50% trọng số Ch2, dễ bằng 0 nếu sai) | 🔴 1 |
| Calibration Ch3 (hold-out + sensitivity) | Thấp–Trung bình | Rất cao (1 điểm MAE = 1 điểm trực tiếp) | 🔴 1 |
| Critical Region MAE Ch1 (không đoán inf sai) | Trung bình | Cao (40% trọng số Ch1) | 🔴 1 |
| Temporal smoothing hậu xử lý (cả 3 challenge) | Thấp | Trung bình–Cao (gần như miễn phí) | 🟠 2 |
| README mở đầu bằng kết quả + 1-lệnh-chạy | Rất thấp | Cao (ấn tượng đầu, điểm mềm) | 🟠 2 |
| Demo kể chuyện 3 đối tượng + SHAP breakdown | Trung bình | Cao (khác biệt sản phẩm, điểm mềm) | 🟠 2 |
| Implementation Notes định lượng + known issues thật | Thấp | Trung bình (điểm mềm, rẻ để làm tốt) | 🟡 3 |
| Usage Notes test máy sạch | Thấp | Trung bình (chống mất điểm oan) | 🟡 3 |
| Ensemble nhiều checkpoint | Cao | Trung bình (lợi ích giảm dần) | 🟢 4 (làm nếu còn dư thời gian) |
| Polish thẩm mỹ dashboard | Cao | Thấp (BTC quan tâm chạy được hơn đẹp) | 🟢 4 |

**Quy tắc phân bổ:** dồn 60% effort vào nhóm 🔴 (quyết định điểm cứng), 30% vào nhóm 🟠 (rẻ nhưng tác động lớn tới điểm mềm), 10% còn lại cho 🟡/🟢.

---

## 7. CHECKLIST CHỐNG MẤT ĐIỂM OAN (rẻ tiền nhưng hay bị bỏ sót)

| Rủi ro | Hậu quả | Cách chặn |
|--------|---------|-----------|
| Điền số 0 giả cho challenge không làm | Bị chấm nhầm là dự đoán sai, trừ điểm oan | Bỏ hẳn cột, không điền 0 |
| `min_ttc` lấy nhầm target ngoài collision cone | Sai điểm Ch1 hệ thống | Lọc `in_collision_cone=true` trước khi lấy min |
| Model đoán `inf` ở vùng nguy hiểm thật | Phạt tối đa Critical Region MAE | Review riêng các frame TTC_gt<3s trước khi nộp |
| Double-count risk (vừa phanh vừa gần vật cản) | Risk score lệch hệ thống | Test case chồng lấn rule (D19, file 01) |
| Overfit trọng số Ch3 trên 10 trip thi | Sập điểm khi BTC test tập ẩn | Hold-out nghiêm ngặt, không nhìn kết quả 10 trip khi tinh chỉnh |
| Repo chứa đường dẫn cá nhân / thiếu dependency | BTC không chạy được → ấn tượng xấu | Test máy sạch 2 lần |
| Dataset gốc lỡ commit lên repo | Vi phạm điều khoản, có thể bị loại | Kiểm `git log --stat`, xóa lịch sử nếu dính |
| Giấu known issues trong Notes | Giám khảo tự phát hiện → mất điểm minh bạch | Chủ động ghi rõ, đúng yêu cầu BTC |

---

*Tài liệu này bổ sung "chiều sâu chất lượng" cho lịch sản xuất (file 03). Thứ tự dùng: file 03 quyết định LÀM GÌ NGÀY NÀO → file 04 (tài liệu này) quyết định LÀM ĐẾN MỨC NÀO LÀ ĐỦ TỐT ở từng việc.*
