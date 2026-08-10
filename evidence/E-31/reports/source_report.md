# E-31 — Customer / Buyer Hypotheses
## Báo cáo Giả thuyết Khách hàng và Kế hoạch Xác thực

**Bối cảnh:** Dự án đang trong giai đoạn hoàn thiện giải pháp và thiết lập demo. Tài liệu này trình bày khung giả thuyết về khách hàng mục tiêu, được chuẩn bị sẵn cho giai đoạn xác thực sau khi có pilot và đối tác fleet. Đây là thực hành đúng đắn ở giai đoạn hiện tại — xây dựng khung phân tích trước để triển khai ngay khi điều kiện sẵn sàng.

**Trạng thái:**
- Hypothesis / Persona: **COMPLETE** — được xây dựng dựa trên phân tích thị trường đã có trong báo cáo chính (mục 24.1).
- Phỏng vấn thực tế (transcript / ghi chú / consent): **NOT STARTED — được lên kế hoạch cho giai đoạn sau khi có pilot hoặc đối tác.**

---

## 1. Bảng Persona Giả thuyết
*(Chưa được xác thực qua phỏng vấn thực tế)*

| Persona | Pain point giả thuyết | Vai trò trong quyết định mua | Điều kiện phù hợp để tham gia pilot |
|---|---|---|---|
| Fleet manager (logistics / vận tải) | Tình trạng mệt mỏi và mất tập trung của tài xế không được phát hiện kịp thời; quy trình coaching phân tán, tốn nhiều thời gian tổng hợp báo cáo thủ công | Người mua và người dùng chính | Đã có hệ thống camera hoặc telemetry, có nhân sự phụ trách an toàn |
| Đội xe nội bộ doanh nghiệp | Thiếu quy trình phân tích an toàn chuẩn hóa | Người mua (bộ phận Operations / HSE) | Quy mô trung bình, tuyến đường và ca vận hành lặp lại |
| OEM / Tier-1 (dài hạn) | Cần prototype tích hợp HMI và vehicle API để đánh giá khả năng thương mại hóa | Người mua (bộ phận R&D / Product) | Có môi trường sandbox HMI / vehicle API để thử nghiệm |

**Lưu ý quan trọng:** Bảng persona trên được suy luận từ đặc điểm cấu trúc ngành, không phải kết quả tổng hợp từ phỏng vấn trực tiếp. Tình trạng này khác với nội dung hiện đang được trình bày tại mục 25 và 27 của báo cáo chính — xem mục 3 bên dưới để biết chi tiết.

---

## 2. Kế hoạch Xác thực Giả thuyết
*(Các bước cần thực hiện — yêu cầu hành động trực tiếp từ nhóm dự án)*

Kế hoạch dưới đây được thiết kế để triển khai song song với giai đoạn chuẩn bị pilot (E-32), cụ thể là trước hoặc trong tuần 1 (Offline replay), để kết quả phỏng vấn có thể dùng điều chỉnh threshold và ưu tiên tính năng trước khi bước vào Shadow mode.

1. Xác định 5–8 đối tượng phỏng vấn có liên quan thực tế trong ngành logistics và vận tải.
2. Chuẩn bị bộ câu hỏi thống nhất để đảm bảo tính nhất quán và khả năng so sánh giữa các cuộc phỏng vấn.
3. Thu thập sự đồng ý ghi âm hoặc ghi chú từ người tham gia trước khi tiến hành phỏng vấn.
4. Tổng hợp cả quan điểm ủng hộ và phản bác giả thuyết — không chọn lọc kết quả theo chiều có lợi.

### Bộ câu hỏi đề xuất *(đã chuẩn bị, chưa được sử dụng)*

| STT | Câu hỏi | Mục tiêu |
|---|---|---|
| 1 | Quy trình quản lý an toàn đội xe hiện tại được thực hiện như thế nào? Ước tính thời gian xử lý mỗi tuần? | Đo lường mức độ nặng nề của pain point |
| 2 | Đã từng xảy ra sự cố liên quan đến tài xế buồn ngủ hoặc mất tập trung chưa? Cách xử lý? | Xác thực mức độ nghiêm trọng của vấn đề |
| 3 | Nếu có hệ thống cảnh báo thời gian thực kết hợp báo cáo tự động, khả năng chấp nhận dùng thử ở mức nào? Ngưỡng chi phí chấp nhận được? | Đánh giá mức sẵn sàng mua |
| 4 | Điều gì có thể khiến tổ chức không sử dụng sản phẩm dạng này? | Thu thập disconfirming insight |

---