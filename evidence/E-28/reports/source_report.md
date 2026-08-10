# E-28 — Market Sources (Nguồn số liệu thị trường)

> **Bối cảnh dự án:** Hiện đang trong giai đoạn hoàn thiện solution/setup demo, chưa có pilot, chưa có đối tác fleet, và **chưa có bản demo chạy ổn định trên Jetson**. Vì chưa pilot, mọi con số kinh doanh cụ thể (giá bán, doanh thu theo khách hàng, quy mô hợp đồng) **không được đưa vào** — chỉ chấp nhận số liệu thị trường công khai có nguồn rõ ràng, dùng làm bối cảnh/target, không phải kết quả đã đạt được.

**Trạng thái:** **PARTIAL — đã tìm và xác minh nguồn cho claim quy mô thị trường logistics VN; phát hiện sai lệch cần sửa trong báo cáo chính.** Ngày thực hiện: 10/08/2026.

---

## 1. Nguồn đã xác minh — quy mô & tăng trưởng ngành logistics Việt Nam

| # | Nội dung | Số liệu | Nguồn | Ngày đăng | Ngày truy cập |
|---|---|---|---|---|---|
| 1 | Tăng trưởng ngành dịch vụ logistics VN (theo VLA, dẫn lại bởi Bộ Công Thương) | **14% – 16%/năm**, quy mô **40 – 42 tỷ USD/năm** | Cổng thông tin Logistics Việt Nam (logistics.gov.vn — Trung tâm Thông tin Công nghiệp và Thương mại, thuộc Bộ Công Thương), bài "Bộ Công Thương đồng hành cùng ngành dịch vụ logistics" — https://logistics.gov.vn/tin-hoat-dong/bo-cong-thuong-dong-hanh-cung-nganh-dich-vu-logistics | 24/02/2025 | 10/08/2026 |
| 2 | Mục tiêu chính thức của Chính phủ đến 2025/dài hạn | Giảm chi phí logistics/GDP từ 18% → 15% (2025); nâng tỷ trọng logistics/GDP từ 10% → 15% (mục tiêu 20%); nâng tốc độ tăng trưởng ngành từ 14–15%/năm hiện nay lên 20% | Cùng nguồn trên (logistics.gov.vn), trích phát biểu tại Diễn đàn Logistics Việt Nam 2024 | 24/02/2025 | 10/08/2026 |
| 3 | Kim ngạch xuất nhập khẩu VN 2024 | 786,29 tỷ USD (+15,4% svck) | Cùng nguồn trên | 24/02/2025 | 10/08/2026 |
| 4 | Quy mô thị trường logistics VN theo tổ chức nghiên cứu quốc tế (định nghĩa khác, để đối chiếu) | USD 31,1 tỷ (2025) → dự báo USD 42,8 tỷ (2034), CAGR 3,61% (2026–2034) | IMARC Group — https://www.imarcgroup.com/vietnam-logistics-market | Không ghi rõ trên trang | 10/08/2026 |

## 2. Đối chiếu với claim trong báo cáo chính — PHÁT HIỆN SAI LỆCH CẦN SỬA

Báo cáo chính (mục 27, ghi chú R11) hiện đang nêu: **"quy mô thị trường logistics Việt Nam 45–50 tỷ USD, tăng trưởng 14–16%/năm"** và tự flag là "Nguồn Bộ Công Thương chính thức phải được bổ sung trước khi sử dụng tuyên bố này."

**Kết quả xác minh:** Nguồn chính thức từ Bộ Công Thương (logistics.gov.vn, 24/02/2025, dẫn số liệu của Hiệp hội Doanh nghiệp dịch vụ Logistics Việt Nam – VLA) ghi nhận:
- Phần **tăng trưởng 14–16%/năm** → **KHỚP**, có thể dùng và trích dẫn nguồn [R11-new].
- Phần **quy mô 45–50 tỷ USD** → **KHÔNG KHỚP**. Nguồn chính thức ghi **40–42 tỷ USD/năm**, không phải 45–50 tỷ USD. Chưa tìm thấy nguồn nào (kể cả IMARC ở dòng 4, vốn dùng định nghĩa hẹp hơn và cho số 31,1 tỷ USD) ủng hộ con số 45–50 tỷ USD.

**Khuyến nghị hành động (P0 trước khi nộp/pitch):**
1. Sửa số trong báo cáo chính từ "45–50 tỷ USD" thành **"40–42 tỷ USD/năm (theo VLA, dẫn lại bởi Bộ Công Thương, 24/02/2025)"**.
2. Giữ nguyên phần "tăng trưởng 14–16%/năm" vì đã có nguồn khớp.
3. Nếu muốn dùng số IMARC (31,1 tỷ USD 2025), phải ghi rõ đây là định nghĩa "logistics market" theo phương pháp luận quốc tế, khác với số liệu "ngành dịch vụ logistics" nội địa theo VLA/Bộ Công Thương — không được trộn hai định nghĩa vào cùng một câu.
4. **Tuyệt đối không dùng số "tiết kiệm 45 tỷ USD"** làm claim lợi ích — cảnh báo này báo cáo chính đã tự ghi và vẫn còn hiệu lực, vì đây là nhầm lẫn giữa "quy mô thị trường" và "lợi ích tiềm năng", hai khái niệm khác nhau.

## 3. Nguồn đã có sẵn trong báo cáo chính, phù hợp giữ nguyên (bối cảnh vấn đề, KHÔNG dùng cho market sizing)

| Mã | Nội dung | Vai trò hợp lệ | Giới hạn |
|---|---|---|---|
| R1 | WHO — tử vong do TNGT toàn cầu | Bối cảnh vấn đề | Số liệu toàn cầu, không đại diện VN |
| R2, R3 | NHTSA — mất tập trung/drowsy driving tại Mỹ 2024 | Bối cảnh vấn đề | Số liệu Mỹ, không quy đổi VN |
| R4, R5, R8 | EU DDAW / Euro NCAP / Regulation 2023/2590 | Hướng dịch chuyển tiêu chuẩn | Không phải bằng chứng homologation của sản phẩm |

## 4. Nguồn còn treo — chưa map vào claim cụ thể (không xóa nhưng cần rà lại)

| Mã | Nội dung | Vấn đề |
|---|---|---|
| R9 | Báo cáo KT-XH 2025 (Cổng TTĐT Chính phủ) | Có link nhưng chưa xác định rõ đoạn/số nào trong báo cáo chính dùng nguồn này — cần rà lại hoặc bỏ khỏi danh mục tham khảo nếu không dùng |
| R10 | Số liệu TNGT/Bộ Công an 2025 | Tương tự R9 |

## 5. Loại số liệu được chấp nhận ở giai đoạn hiện tại

**KHÔNG được đưa vào** (vì chưa pilot, chưa demo Jetson ổn định):
- Giá bán cụ thể đã chốt với khách hàng thật, quy mô hợp đồng, doanh thu dự kiến theo khách hàng cụ thể.

**ĐƯỢC chấp nhận:**
- Số liệu thị trường công khai có nguồn, ngày đăng, ngày truy cập rõ ràng (như bảng mục 1) — dùng làm bối cảnh, không phải cam kết.
- Mục tiêu/target có công thức tính minh bạch (ví dụ công thức ROI ở E-33) — ghi rõ là **target/proposed**.

## 6. Việc cần làm — còn lại, cần con người xử lý

1. Cập nhật lại con số ở mục 27 báo cáo chính theo mục 2 phía trên (40–42 tỷ USD thay vì 45–50 tỷ USD), và cập nhật danh mục tài liệu tham khảo với nguồn logistics.gov.vn (24/02/2025).
2. Lưu snapshot (PDF/ảnh chụp) trang logistics.gov.vn vào `evidence/E-28/raw/` để phòng trường hợp trang gốc bị gỡ/sửa sau này.
3. Rà lại R9, R10 xem có claim cụ thể nào trong báo cáo chính thực sự dùng hai nguồn này không; nếu không, cân nhắc bỏ khỏi danh mục tài liệu tham khảo.
4. Nếu cần số liệu thị trường sát hơn với ngành fleet-safety/DMS (thay vì logistics nói chung), cần tìm nguồn riêng — hiện chưa có, không được suy diễn từ quy mô logistics tổng thể.
