# E-32 — Pilot Protocol
## Báo cáo Giao thức Pilot Pre-registered

**Trạng thái:** DRAFT PROTOCOL — Tài liệu này được soạn thảo **trước khi có pilot thực tế**, theo đúng nguyên tắc pre-registration trong nghiên cứu ứng dụng. Chưa có kết quả thực địa đi kèm. Dự án hiện đang ở giai đoạn hoàn thiện giải pháp và thiết lập demo, chưa có đối tác fleet để triển khai.

---

## 1. Mục tiêu của Pilot

Pilot được thiết kế để đo lường ba chỉ số cốt lõi nhằm xác thực tính khả thi của hệ thống trong điều kiện vận hành thực tế:

**(a)** Tỷ lệ cảnh báo sai (false alert rate) trong điều kiện vận hành thực tế;
**(b)** Mức độ chấp nhận của tài xế đối với hệ thống cảnh báo;
**(c)** Thời gian phản hồi và can thiệp của fleet manager khi nhận cảnh báo.

Kết quả đo lường từ ba chỉ số trên sẽ thay thế các số liệu ước lượng hiện đang được sử dụng làm đầu vào cho mô hình ROI (E-33).

---

## 2. Khung Pilot Đề xuất
*(Theo cấu trúc mục 25 của báo cáo chính)*

| Giai đoạn | Thời lượng | Quy mô | Mục tiêu |
|---|---|---|---|
| **Offline replay** | 1 tuần | Dữ liệu lịch sử / dataset có sẵn | Hiệu chỉnh ngưỡng phát hiện (threshold tuning) trước khi triển khai trực tiếp |
| **Shadow mode** | 2 tuần | 5–10 xe | Hệ thống ghi nhận sự kiện nhưng không can thiệp; đo precision / recall / FAR so với nhãn của người quan sát |
| **Assisted pilot** | 4 tuần | Cùng 5–10 xe | Cảnh báo và coaching được gửi sau khi có xác nhận của con người trước khi chuyển đến tài xế |
| **Đánh giá và quyết định** | 1 tuần | — | Tổng hợp KPI, đưa ra quyết định mở rộng / điều chỉnh / dừng |

**Tổng thời lượng đề xuất: khoảng 8 tuần**, có thể điều chỉnh tùy theo điều kiện thực tế của đối tác pilot.

---

## 3. KPI Pre-defined
*(Được xác định trước khi chạy pilot — theo nguyên tắc pre-registration)*

| KPI | Phương pháp đo | Ngưỡng thành công đề xuất | Căn cứ |
|---|---|---|---|
| False alert rate | Số cảnh báo không hợp lệ / tổng giờ lái | ≤ 2 lần/giờ | Mục 20 báo cáo chính |
| Driver acceptance | Khảo sát ngắn sau mỗi tuần vận hành | ≥ 70% tài xế không phản đối tiếp tục sử dụng | Tham khảo thực hành ngành |
| Manager acknowledge time | Thời gian từ khi phát sinh cảnh báo đến khi fleet manager xác nhận | ≤ 20 giây | Mục 20 báo cáo chính |
| Coaching completion rate | Tỷ lệ sự kiện có coaching được hoàn tất | ≥ 80% | Tham khảo thực hành ngành |

---

## 4. Yêu cầu về Dữ liệu và Cỡ Mẫu

- **Cỡ mẫu tối thiểu:** 5 xe; khuyến nghị 10 xe để đảm bảo số lượng sự kiện đủ cho phân tích thống kê có ý nghĩa.
- **Tuyến đường và ca vận hành:** Ưu tiên tuyến đường và ca lặp lại để giảm nhiễu do sự khác biệt điều kiện vận hành.
- **Điều kiện tiên quyết:** Yêu cầu có sự đồng ý của tài xế (consent) trước khi bắt đầu thu thập dữ liệu, theo quy định tại E-34 (draft policy bảo mật).

---

## 5. Điều kiện Dừng / Mở rộng

| Kết quả | Điều kiện kích hoạt | Hành động |
|---|---|---|
| **Mở rộng (Scale)** | False alert rate đạt ngưỡng VÀ driver acceptance ≥ 70% sau giai đoạn Assisted pilot | Tiến hành mở rộng quy mô |
| **Dừng (Stop)** | False alert rate vượt 2× ngưỡng liên tục trong 2 tuần HOẶC driver acceptance < 40% | Dừng pilot, đánh giá lại |
| **Điều chỉnh (Pivot)** | Kết quả ở mức trung gian | Hiệu chỉnh ngưỡng / mô hình trước khi chạy vòng pilot tiếp theo |

---

## 6. Giới hạn Công bố

Tài liệu này là **giao thức dự kiến** — chưa có đối tác fleet xác nhận tham gia, chưa có dữ liệu thực địa. Toàn bộ ngưỡng KPI nêu trên (≤ 2 lần/giờ, ≥ 70%, ≤ 20 giây...) là **mục tiêu đề xuất** dựa trên tham khảo mục 20 của báo cáo chính, không phải kết quả đo thực tế.

Để bắt đầu triển khai pilot, cần hoàn thành ba điều kiện theo thứ tự: (1) xác định và ký kết thỏa thuận với đối tác fleet; (2) hoàn thiện thỏa thuận dữ liệu và thu thập consent từ tài xế; (3) khởi động giai đoạn Offline replay.
