# E-29 — Competitive Matrix (Ma trận cạnh tranh)

> **Bối cảnh dự án:** Hiện đang trong giai đoạn hoàn thiện solution/setup demo, chưa có pilot, chưa có đối tác fleet, và **chưa có bản demo chạy ổn định trên Jetson**. Vì vậy bảng dưới đây **không so sánh giá của FPTU DMS Vision với đối thủ** (giá của mình trong mục 24.2 báo cáo chính vẫn là giả thuyết chưa chốt) — chỉ tổng hợp thông tin công khai về đối thủ để tham khảo định vị.

**Trạng thái:** **PARTIAL — đã có snapshot/nguồn cho 5 đối thủ (M1–M5); pricing dựa trên ước lượng của bên thứ ba (third-party estimate), không phải giá niêm yết chính thức của vendor.** Ngày thực hiện: 10/08/2026.

---

## 1. Bảng nguồn đã xác minh

| Mã | Đối thủ | Nguồn chính (trang sản phẩm/tin tức) | Ngày đăng/cập nhật | Ngày truy cập |
|---|---|---|---|---|
| M1 | Samsara | https://www.samsara.com/products/cameras , https://www.samsara.com/products/models | Không ghi rõ | 10/08/2026 |
| M1-p | Samsara — pricing (third-party) | https://checkthat.ai/brands/samsara/pricing | 17/04/2026 | 10/08/2026 |
| M2 | Motive | https://ledgersupply.com/review/motive/ (third-party review, không phải trang chính thức) | Không ghi rõ | 10/08/2026 |
| M2-p | Motive — pricing (third-party) | https://spytec.com/blogs/news/fleet-tracking-pricing-comparison | 26/05/2026 | 10/08/2026 |
| M3 | Geotab GO Focus Plus | https://www.geotab.com/products/go-focus-plus/ , https://www.geotab.com/press-release/geotab-launches-go-focus-plus/ | Ra mắt ~15/09/2025 | 10/08/2026 |
| M3-p | Geotab — pricing (third-party) | https://tech.co/fleet-management/geotab-review-fleet-management | 25/06/2026 | 10/08/2026 |
| M4 | Netradyne Driver·i | https://techcrunch.com/2025/01/17/netradyne-snags-90m-at-1-25b-valuation-to-expand-smart-dashcams-for-commercial-fleets | 17/01/2025 | 10/08/2026 |
| M5 | Seeing Machines Guardian | https://marketplace.geotab.com/solutions/seeing-machines-guardian/ | Không ghi rõ | 10/08/2026 |

**Lưu ý về độ tin cậy nguồn:** M1, M3 lấy trực tiếp từ trang chính thức của vendor. M2, M4, M5 hiện đang dùng nguồn thứ cấp (review site/tin tức) vì trang chính thức của Motive **không công khai giá** (xác nhận ở mục 2). Toàn bộ dòng "-p" (pricing) đều là **ước lượng/tổng hợp của bên thứ ba**, không phải giá niêm yết chính thức — cần ghi rõ điều này mỗi khi trích dẫn.

## 2. Bảng tính năng — định tính (tổng hợp từ nguồn công khai)

| Đối thủ | Road-facing risk | Driver monitoring (DMS) | Telemetry fusion | Event/coaching workflow | Giá công khai? |
|---|---|---|---|---|---|
| Samsara | Có (AI dash cam road + dual-facing) — phát hiện drowsiness, distraction, tailgating, forward collision risk | Có (dual-facing camera) | Có, tích hợp platform telematics đầy đủ (ELD, GPS, EV) | Có — coaching workflow, safety score, gamification | **Không niêm yết công khai theo VND/USD cố định**; ước lượng bên thứ ba ~$27–33/xe/tháng (core telematics), ~$40–60+/xe/tháng nếu có dual-facing AI dashcam |
| Motive | Có (AI dashcam, harsh braking/acceleration/cornering) | Có (dual-facing, có "Driver Privacy Mode") | Có, tích hợp ELD + Vehicle Gateway | Có — AI Safety coaching, CSA score | **Không công khai** — mọi báo giá qua sales call; ước lượng bên thứ ba ~$25–50/xe/tháng |
| Geotab GO Focus Plus | Có (ADAS: tailgating, hard braking) | Có (DMS: distracted driving, fatigue) | Có, tích hợp Geotab telematics core | Có — in-cab voice alert, coaching workflow, Smart Sequence | Bán qua reseller bên thứ ba; ước lượng ~$30–40/xe/tháng (bundle phần mềm + phần cứng thuê) |
| Netradyne Driver·i | Có (edge computing, cảnh báo real-time) | Có (inward-facing camera, phát hiện distraction) | Có, tích hợp fleet platform | Có — thưởng hành vi tốt ("GreenZone"), coaching | Không tìm thấy giá công khai trong lần tra cứu này — cần bổ sung |
| Seeing Machines Guardian | Không phải trọng tâm (chuyên biệt về DMS hơn là road-facing risk) | Có — chuyên sâu eye/face tracking, tuyên bố giảm fatigue events "upwards of 90%" (claim của vendor, chưa kiểm chứng độc lập) | Có qua tích hợp Geotab Marketplace (add-in) | Có — dashboard fatigue/distraction/over-speed theo ca trực | Không tìm thấy giá công khai trong lần tra cứu này — cần bổ sung |

**Ghi chú quan trọng khi trích dẫn claim "giảm 90% fatigue events" của Seeing Machines:** đây là tuyên bố marketing của chính vendor, không phải số liệu kiểm chứng độc lập — nếu dùng trong pitch phải ghi rõ "theo công bố của Seeing Machines", không được trình bày như một benchmark trung lập.

## 3. Vì sao KHÔNG có bảng so sánh giá của FPTU DMS Vision với đối thủ

- Các đối thủ lớn (Samsara, Motive) **không công khai giá cố định** — bán qua sales call, tùy quy mô fleet và hardware bundle. Giá trong bảng trên là ước lượng bên thứ ba (third-party estimate), có thể sai lệch so với giá thật tại thời điểm đàm phán.
- Giá đề xuất của FPTU DMS Vision (mục 24.2 báo cáo chính, ví dụ 300.000 VND/xe/tháng) **là giả thuyết nội bộ chưa chốt**, dựa trên BOM/assumption ở E-30, chưa qua pilot hay khách hàng thật xác nhận.
- Vì hai vế đều chưa đủ độ tin cậy ngang nhau (một bên là ước lượng thị trường quốc tế, một bên là giả thuyết nội bộ chưa kiểm chứng), **so sánh trực tiếp hai con số này sẽ gây hiểu nhầm** — không nên đưa vào slide pitch ở giai đoạn hiện tại.
- Khi nào có thể làm: sau khi (a) FPTU DMS Vision có ít nhất một mức giá đã thảo luận với khách hàng pilot thật, và (b) có báo giá/estimate đáng tin hơn từ đối thủ (qua liên hệ sales hoặc báo cáo ngành có trả phí).

## 4. Định vị định tính rút ra được (dùng được ngay, không cần số giá)

Dựa trên bảng mục 2, có thể phát biểu (không cần số liệu định lượng):

- Phần lớn đối thủ lớn (Samsara, Motive, Geotab) là **nền tảng telematics tổng hợp** với dash cam AI là một module trong hệ sinh thái lớn hơn (ELD, GPS, EV management...) — không chuyên sâu về context fusion giữa road-risk (TTC/stereo) và driver-state như FPTU DMS Vision hướng tới.
- Seeing Machines Guardian là đối thủ **gần nhất về chuyên môn DMS** (eye/face tracking chuyên sâu) nhưng không phải nền tảng fleet-management đầy đủ — thường tích hợp qua bên thứ ba (Geotab Marketplace) thay vì tự làm cả stack.
- **Chưa có đối thủ nào trong 5 cái tên trên công khai kết hợp stereo TTC + driver state + connected-car HMI (CarSky/Android Automotive) trong cùng một kiến trúc mở** theo cách báo cáo chính mô tả ở mục 22 — đây là điểm định vị hợp lý để giữ nguyên, vì nó dựa trên khoảng trống quan sát được (đối thủ không công bố), không phải tuyên bố "vượt trội".

