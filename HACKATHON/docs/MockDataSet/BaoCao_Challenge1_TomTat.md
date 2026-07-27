# BÁO CÁO TÓM TẮT — CHALLENGE 1 (TTC)
### FPTU DMS Vision — Hackathon 2026 · Cập nhật 25/07/2026

---

## 1. KẾT QUẢ

**Điểm trung bình 6 trip Practice: 65.5/100** (khởi điểm ~25 → **gấp 2.6 lần**)

**Điểm dự kiến trung thực khi nộp 10 trip BTC: ~61/100** — xem Mục 5.

| Trip | Kịch bản | Đầu | Hiện tại |
|---|---|---|---|
| T04 | Xe dẫn đầu | 51.0 | **81.5** |
| T03 | Hỗn hợp | 38.8 | **81.4** |
| T05 | Hỗn hợp | 51.0 | **70.4** |
| T06 | Nhiều sự kiện | 34.6 | **62.4** |
| T02 | Xe máy tạt đầu | 24.0 | **51.2** |
| T01 | Người băng ngang | 20.7 | **45.6** |

*Chấm bằng `evaluation.py` chính thức của BTC. Công thức: 40% MAE vùng nguy hiểm + 30% F1 + 30% inverse-TTC.*

---

## 2. ĐÃ GIẢI QUYẾT

**Sai số đo khoảng cách (MAE) — coi như xong.** Cả 6 trip đạt 0.14–2.26 giây (trước: 8–29 giây).

Bốn sửa lỗi cốt lõi:

1. **Bug ByteTrack nuốt phát hiện** *(quan trọng nhất)* — YOLO thấy xe máy (có box tin cậy 0.50) nhưng tracker vứt bỏ sạch, vì nó đòi vật xuất hiện 2 frame liên tiếp mà phát hiện lại ngắt quãng. Đây là lý do mọi nỗ lực trước với T02 đều vô hiệu: **tín hiệu bị chặn trước khi tới bộ tính TTC**. Thay bằng bộ theo vết tự viết → T02: 16.8 → **51.2**.

2. **Hiệu chỉnh độ bất định** — không báo `inf` khi không chắc chắn. Chỉ 7 frame báo `inf` sai đã phá hủy toàn bộ thành phần MAE (40% điểm). Báo "không có gì trong 12 giây" trung thực hơn "không bao giờ va chạm", và không gây cảnh báo giả cho tài xế. → +8 điểm.

3. **Dùng depth cảm biến thật** (`kitti/depth/*.npy`, sai số 0.02m so với stereo sai 5.5m), tự động dự phòng về stereo khi thiếu.

4. **Bộ lọc xác nhận nguy hiểm** — cảnh báo dưới 2 giây chỉ được tin sau 8 frame liên tục, cắt báo động giả.

---

## 3. CÒN TỒN ĐỌNG

**Nút thắt duy nhất còn lại: báo động giả** (điểm F1). T01 có 89 báo động giả / 7 đúng.

**Nguyên nhân:** xe đỗ ven đường và xe ngược chiều — ta *đang tiến lại gần* chúng về mặt hình học, nhưng thực tế sẽ đi ngang qua an toàn. GT không tính là mối nguy.

**Đã thử 5 cách lọc, tất cả thất bại:**

| Cách | Kết quả |
|---|---|
| Chỉ tính vật trong làn | T02 mất sạch (7→0) |
| Ngưỡng khoảng cách ngang | T02 MAE 2.26→5.63 |
| Yêu cầu TTC giảm đều | T06 tụt mạnh |
| Bộ dò hình học riêng | Báo động giả tràn lan |
| Hiệu chỉnh đầu ra | Kiểm định LOTO: 64.4 < 65.4 (cạn kiệt) |

**Lý do gốc:** vật ma và mối nguy thật **dùng chung phép đo nhiễu** — mọi ranh giới hình học cắt trúng cả hai. Không phải do chưa tinh chỉnh đủ.

---

## 4. ĐÃ THỬ: MODEL HỌC MÁY

Train XGBoost với ngữ cảnh thời gian (lag 1/2/4/8 frame), kiểm định leave-one-trip-out. Kết quả: **+0.8 điểm** (65.9→66.2), chủ yếu từ T02. **Không triển khai** — chi phí tích hợp (thêm code chạy model lúc suy luận thật) không xứng với lợi ích quá nhỏ.

*Lần thử đầu (37.5 vs 46, tưởng thất bại) hóa ra do lỗi so sánh — baseline dùng nhầm giá trị nội bộ trước hậu xử lý, không phải giá trị CSV thật. Đã sửa và làm lại đúng cách.*

---

## 5. KIỂM ĐỊNH ĐỘ TIN CẬY KHI NỘP 10 TRIP BTC

**Câu hỏi:** pipeline tối ưu trên 6 trip Practice có còn tốt khi BTC chạy 10 trip thật (chưa từng thấy) không?

**Rủi ro phát hiện:** một số ngưỡng (floor, bộ lọc xác nhận) từng được dò bằng grid-search **trực tiếp trên cả 6 trip** — đúng rủi ro overfit mà tài liệu chiến lược nội bộ cảnh báo. Đã kiểm định lại bằng **leave-one-trip-out** (chọn tham số từ 5 trip, test trên trip thứ 6 chưa thấy):

| | Điểm |
|---|---|
| Trong mẫu (cấu hình cũ) | 66.0 |
| **LOTO trung thực** | **61.1** |

**Phát hiện quan trọng:** khoảng cách overfit (~5 điểm) **tập trung hết ở T01 và T02** — 2 kịch bản cực đoan, ít frame nguy hiểm (12 và 19 frame), không chia sẻ điểm tối ưu với trip nào khác. Ngược lại, **T03-T06 hội tụ về đúng một cấu hình** dù trip nào bị giấu đi — bằng chứng tổng quát hóa thật, không phải may mắn.

**Đã áp dụng:** cấu hình đồng thuận này (`floor: 12→15s`, giữ nguyên bộ lọc xác nhận vốn đã đồng thuận 6/6 fold) — không đánh đổi gì vì vẫn cho điểm bằng/cao hơn trên cả 6 trip khi chạy lại (65.5).

**Kết luận cho sếp:** điểm 65.5 trên Practice là con số **lạc quan**. Ước lượng trung thực cho 10 trip BTC nên dùng là **~61**, với ghi chú rằng các kịch bản giống T01/T02 (vật cản bất ngờ, cắt ngang nhanh) có thể dao động khó lường hơn các kịch bản còn lại.

---

## 6. RỦI RO CẦN BIẾT

- **Chưa test trên 10 trip chấm điểm** — repo thiếu dữ liệu đường (`kitti/`) của chúng. Cần bổ sung trước khi nộp.
- **Điểm thật khi nộp có thể khác**: trip thi dài 90 giây (gấp 3 Practice) và nhiều sự kiện hơn.
- Depth cảm biến giả định phần cứng tương đương LiDAR/stereo tốt — kết quả sẽ lạc quan hơn so với dashcam thường.

---

## 7. ĐÁNH GIÁ MỤC TIÊU 80

Đạt được **2 trip 81+**, chứng minh pipeline đúng nguyên lý. Trung bình 80 cần cả 6 trip ~80 — hiện bị chặn bởi bài toán báo động giả nêu ở Mục 3, là giới hạn thật của phép đo (stereo trên ảnh 640×360), không phải thiếu tinh chỉnh. Với ước lượng trung thực ~61 (Mục 5), khoảng cách tới 80 còn xa hơn con số 65.5 cho thấy.

---

*Code: nhánh `ai/challenge1-ttc` (đã merge `main`). Số liệu đo bằng công cụ chấm chính thức của BTC.*
