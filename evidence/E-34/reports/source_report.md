# E-34 — Safety / Privacy Gates
## Báo cáo Dự thảo Chính sách An toàn và Bảo vệ Dữ liệu

**Bối cảnh:** Dự án đang trong giai đoạn hoàn thiện giải pháp và thiết lập demo, chưa có pilot, chưa có đối tác fleet thực tế. Tài liệu này trình bày **dự thảo chính sách** được chuẩn bị sẵn cho giai đoạn pilot, nhằm rút ngắn thời gian khi có đối tác — chỉ cần review và ký duyệt thay vì soạn thảo từ đầu. Đây là thực hành đúng đắn ở giai đoạn hiện tại.

**Trạng thái:**
- Dự thảo chính sách: **COMPLETE** — soạn thảo dựa trên Nghị định 13/2023/NĐ-CP (bảo vệ dữ liệu cá nhân Việt Nam) và các nguyên tắc tại mục 28, 28.1 của báo cáo chính.
- Tabletop review và phê duyệt chính thức: **NOT STARTED — được lên kế hoạch cho giai đoạn ngay trước khi pilot bắt đầu.**

---

## 1. Quyền riêng tư và Quản trị Dữ liệu *(Dự thảo)*

| Nội dung | Đề xuất dự thảo | Câu hỏi cần người có thẩm quyền quyết định |
|---|---|---|
| **Data minimization** | Ưu tiên truyền metadata và event contract (risk score, trạng thái tài xế, timestamp) thay vì raw video khi có thể. Raw video chỉ lưu cục bộ (on-device) hoặc truyền khi xảy ra sự kiện (event-based recording). | Có chấp thuận nguyên tắc "event-based" hay cần lưu video liên tục cho mục đích kiểm toán? |
| **Consent** | Tài xế phải được thông báo và đồng ý bằng văn bản trước khi kích hoạt driver camera — hình thức: ký văn bản hoặc xác nhận trên app / HMI trước lần sử dụng đầu tiên. | Ai chịu trách nhiệm soạn nội dung consent form cuối cùng — bộ phận pháp lý hay đội sản phẩm? |
| **Retention (lưu trữ)** | Đề xuất tạm thời: metadata lưu 90 ngày; raw video (nếu có) lưu 30 ngày, ngoại trừ trường hợp liên quan đến sự cố đang điều tra thì giữ đến khi vụ việc được đóng lại. | Cần xác nhận con số cụ thể theo yêu cầu của đối tác pilot và tư vấn pháp lý — chưa chốt. |
| **Access control** | Phân quyền tối thiểu theo vai trò: Tài xế chỉ xem dữ liệu của cá nhân; Fleet Manager xem dữ liệu đội xe phụ trách; Admin xem toàn bộ. Lưu ý: RBAC chưa được triển khai trong hệ thống thực tế (đã ghi nhận là backlog tại mục 14.3.5 báo cáo chính). | Thời điểm triển khai RBAC thực tế: trước hay sau pilot đầu tiên? |
| **Legal scope** | Áp dụng Nghị định 13/2023/NĐ-CP (Việt Nam). Nếu có đối tác nước ngoài hoặc dữ liệu được xử lý qua AWS (cross-border), cần tham vấn thêm quy định liên quan. | Cần chuyên gia pháp lý xác nhận chính xác nghĩa vụ — tài liệu này không tự kết luận phạm vi áp dụng pháp lý. |

---

## 2. Ranh giới An toàn Hệ thống *(Dự thảo)*

- Hệ thống hoạt động ở chế độ **cảnh báo tham khảo (advisory warning)** — không điều khiển xe và không can thiệp vật lý (phanh tự động, v.v.). Cần nêu rõ giới hạn này trong mọi tài liệu kỹ thuật và tài liệu trình bày để tránh nhầm lẫn với hệ thống ADAS có khả năng can thiệp vật lý.
- Nếu dự án tiến đến giai đoạn pilot thực địa, đề xuất tham vấn chuyên gia về mức độ Hazard Analysis phù hợp. Tài liệu này không tự nhận đạt chuẩn ISO 26262 / ASIL bất kỳ — phạm vi áp dụng cần được chuyên gia xác nhận.

---

## 3. Human Factors *(Dự thảo)*

- Đề xuất review ngưỡng cảnh báo HMI (âm thanh, tần suất, độ sáng màn hình) để tránh gây thêm phân tâm cho tài xế hoặc dẫn đến tình trạng "alert fatigue". Hiện **chưa có kết quả kiểm thử human-factors thực tế** (nhất quán với E-39 trong báo cáo chính: NOT EXECUTED).
- Đề xuất bổ sung cooldown policy và repetition control để tránh lặp cảnh báo liên tục cho cùng một sự kiện kéo dài.

---

## 4. Danh sách Gap chưa Giải quyết

Bảng dưới đây liệt kê các điểm còn thiếu cần được xử lý trước khi chính sách này có hiệu lực:

| STT | Gap | Tác động nếu không giải quyết |
|---|---|---|
| 1 | Chưa có người được chỉ định làm approver cho chính sách này | Chính sách không có hiệu lực pháp lý nội bộ |
| 2 | Chưa tổ chức buổi họp tabletop review chính thức | Các điểm bất đồng hoặc khoảng trống chưa được phát hiện |
| 3 | Chưa chốt thời hạn lưu trữ cụ thể (mới ở mức đề xuất tham khảo) | Rủi ro không tuân thủ Nghị định 13/2023/NĐ-CP |
| 4 | RBAC chưa được triển khai trong hệ thống thực tế | Kiểm soát truy cập dữ liệu chưa được thực thi kỹ thuật |
| 5 | Chưa có consent form hoàn chỉnh (mới có nguyên tắc, chưa có văn bản cụ thể) | Không thể thu thập dữ liệu tài xế hợp lệ trong pilot |
| 6 | Chưa có xác nhận pháp lý chuyên môn về phạm vi áp dụng | Rủi ro pháp lý, đặc biệt nếu có xử lý dữ liệu cross-border qua AWS |
