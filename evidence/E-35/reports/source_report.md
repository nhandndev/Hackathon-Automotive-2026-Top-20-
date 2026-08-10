# E-35 — Reviewer Evidence Index
## Chỉ mục Bằng chứng Tổng hợp — Dành cho Ban Giám khảo

**Phiên bản:** Cập nhật sau khi tích hợp E-30, E-31, E-32, E-33, E-34 vào repo  
**Ngày cập nhật:** 10/08/2026  
**Trạng thái tổng thể:** PARTIAL — Phần lớn nội dung phân tích và thiết kế đã hoàn chỉnh; một số hạng mục đang chờ xác nhận thực địa (phỏng vấn, pilot, phê duyệt pháp lý) theo đúng lộ trình dự án.

---

## Lời dẫn

Tài liệu này là chỉ mục tổng hợp toàn bộ bằng chứng của dự án, được chuẩn bị để hỗ trợ ban giám khảo trong việc tra cứu và đối chiếu thông tin. Mỗi hạng mục được ghi nhận trạng thái thực tế — phân biệt rõ phần đã hoàn chỉnh và phần đang chờ điều kiện thực địa.

Cách tiếp cận này phản ánh tiêu chuẩn nghiên cứu và phát triển sản phẩm nghiêm túc: **trình bày trung thực, không phóng đại, không che giấu giới hạn**.

---

## 1. Bảng Tổng hợp Trạng thái — E-01 đến E-35

### Nhóm Kỹ thuật Lõi (E-01 đến E-29)

| Nhóm | Phạm vi | Trạng thái chung | Ghi chú |
|---|---|---|---|
| E-01 đến E-10 | Kiến trúc hệ thống, pipeline AI, dữ liệu đầu vào | VERIFIED / PARTIAL | Các hạng mục kỹ thuật cốt lõi đã có log và đo thực tế trên thiết bị |
| E-11 đến E-20 | Hiệu năng edge, alert orchestrator, C3 AI, chi phí đám mây | VERIFIED / PARTIAL | Có benchmark và log AWS Bedrock thực tế; một số hạng mục pending runtime capture |
| E-21 đến E-29 | Dashboard, reliability, HMI, kiểm thử hệ thống | VERIFIED / PARTIAL | Một số hạng mục thử nghiệm trên CARLA; một số đo thực tế |

Trạng thái chi tiết của toàn bộ E-01 đến E-42 được lưu tại:
`evidence/E-35/derived/evidence_status_summary.csv`

### Nhóm Kinh doanh và Triển khai (E-28 đến E-35) — Chi tiết

| Evidence | Tên hạng mục | Model / Thiết kế | Dữ liệu / Input thực tế | Trạng thái tổng | File nguồn |
|---|---|---|---|---|---|
| **E-28** | Market Sources (Nguồn số liệu thị trường) | N/A | PARTIAL — đã tìm và xác minh nguồn cho claim quy mô thị trường logistics VN; phát hiện sai lệch cần sửa trong báo cáo chính. | **PARTIAL** | `evidence/E-28/reports/source_report.md` |
| **E-29** | Competitive Matrix (Ma trận cạnh tranh) | N/A | PARTIAL — đã có feature matrix; chưa có pricing comparison vì pricing công ty chưa chốt | **PARTIAL** | `evidence/E-29/reports/source_report.md` |
| **E-30** | Pricing / BOM / Unit Economics | COMPLETE — công thức BOM rõ ràng; giá Jetson $249 có nguồn chính thức | PARTIAL — camera chưa có báo giá đàm phán; mới có khoảng giá thị trường | **PARTIAL** | `evidence/E-30/reports/source_report.md` |
| **E-31** | Customer / Buyer Hypotheses | COMPLETE — bảng persona / hypothesis đầy đủ, dựa trên phân tích ngành (mục 24.1) | NOT STARTED — phỏng vấn thực tế chưa thực hiện; kế hoạch sau pilot | **PARTIAL** | `evidence/E-31/reports/source_report.md` |
| **E-32** | Pilot Protocol | COMPLETE — protocol pre-registered đầy đủ 4 giai đoạn; KPI pre-defined; điều kiện Stop/Scale rõ ràng | NOT STARTED — chưa có đối tác fleet xác nhận; chưa bắt đầu Offline replay | **PARTIAL** | `evidence/E-32/reports/source_report.md` |
| **E-33** | ROI Model | COMPLETE — công thức 3 kịch bản (Conservative / Base / Optimistic); nguồn BOM từ E-30 | PENDING E-32 — baseline log chưa có vì pilot chưa chạy; phụ thuộc tuần tự hợp lý | **PARTIAL** | `evidence/E-33/reports/source_report.md` |
| **E-34** | Safety / Privacy Gates | COMPLETE — dự thảo chính sách đầy đủ; căn cứ Nghị định 13/2023/NĐ-CP và mục 28 báo cáo chính | NOT STARTED — tabletop review và phê duyệt chính thức chưa thực hiện | **PARTIAL** | `evidence/E-34/reports/source_report.md` |
| **E-35** | Reviewer Evidence Index | Tài liệu này | Phụ thuộc toàn bộ 5 hạng mục trên | **PARTIAL** | Tài liệu này |

---

## 2. Cập nhật claim_evidence_hash_map.csv

Bảng dưới đây ghi nhận 5 claim mới cần bổ sung vào `claim_evidence_hash_map.csv` sau khi các file được commit vào nhánh chính.

| Claim được hỗ trợ | File chứng minh | Hash SHA-256 | Ngày tạo | Người phụ trách |
|---|---|---|---|---|
| BOM / giá thiết bị có nguồn thị trường xác minh | `evidence/E-30/reports/source_report.md` | *(cần chạy `sha256sum` sau khi commit)* | 2026-08-10 | Dân (theo backlog gốc) |
| Persona / hypothesis khách hàng có cơ sở phân tích ngành | `evidence/E-31/reports/source_report.md` | *(cần chạy `sha256sum` sau khi commit)* | 2026-08-10 | Chưa gán |
| Pilot protocol pre-registered trước khi có dữ liệu | `evidence/E-32/reports/source_report.md` | *(cần chạy `sha256sum` sau khi commit)* | 2026-08-10 | Hùng (theo backlog gốc) |
| ROI model có nguồn gốc minh bạch; phân tách rõ kịch bản | `evidence/E-33/reports/source_report.md` | *(cần chạy `sha256sum` sau khi commit)* | 2026-08-10 | Chưa gán |
| Dự thảo chính sách bảo mật / an toàn có căn cứ pháp lý | `evidence/E-34/reports/source_report.md` | *(cần chạy `sha256sum` sau khi commit)* | 2026-08-10 | Dân (theo backlog gốc) |
| Quy mô thị trường logistics VN | `evidence/E-28/reports/source_report.md` | (cần tính) | 2026-08-10 | — (chưa gán) |
| Định vị định tính và thông tin đối thủ | `evidence/E-29/reports/source_report.md` | (cần tính) | 2026-08-10 | — (chưa gán) |

Cột Hash hiện để trống vì các file chưa qua commit chính thức — ghi nhận đúng trạng thái thực tế thay vì điền số ước tính.

---

## 3. Sửa access_test.csv — Xóa Đường dẫn Không hợp lệ

Trong quá trình kiểm tra, phát hiện một dòng trong `access_test.csv` chứa đường dẫn không tồn tại trong hệ thống thực tế. Dòng này cần được xử lý như sau:

**Dòng cần xóa:**
```
Báo cáo PDF / Phụ lục C,...,Video Demo: https://drive.google.com/file/d/sample_demo_video/view,NO (REAL_LINK),VERIFIED_PUBLIC
```

**Lý do:** Đường dẫn trên không tồn tại — đây là trường hợp điển hình của lỗi "overclaim", trong đó thông tin được tạo ra để có vẻ hoàn chỉnh mà không có cơ sở thực tế.

**Dòng thay thế (phản ánh đúng thực trạng):**
```
Báo cáo PDF / Phụ lục C,...,Video Demo: [CHƯA CÓ LINK — CẦN UPLOAD VIDEO DEMO THẬT],YES (PLACEHOLDER),NEEDS_HUMAN_UPLOAD
```

---

## 4. Hạng mục còn lại Yêu cầu Hành động Trực tiếp từ Nhóm Dự án

| STT | Hành động cần thực hiện | Evidence liên quan | Ghi chú |
|---|---|---|---|
| 1 | Tiến hành phỏng vấn 5–8 fleet manager / chủ đội xe thực tế | E-31 | Khung câu hỏi đã được chuẩn bị sẵn tại E-31 |
| 2 | Xác định đối tác fleet đồng ý tham gia pilot; khởi động giai đoạn Offline replay | E-32 | Protocol đã sẵn sàng — chỉ cần đối tác xác nhận |
| 3 | Chỉ định approver; tổ chức buổi họp tabletop review chính thức cho chính sách bảo mật | E-34 | Dự thảo đầy đủ — chỉ cần phê duyệt |
| 4 | Xin báo giá chính thức (quote bằng văn bản) từ nhà cung cấp camera công nghiệp | E-30 | Nâng từ khoảng giá ước lượng lên số liệu đàm phán thực tế |
| 5 | Chạy `sha256sum` thực tế; điền hash vào claim_evidence_hash_map.csv | E-35 | Sau khi commit file vào nhánh chính |
| 6 | Upload video demo thực tế lên Drive; cập nhật đường dẫn vào Phụ lục C | E-35 | Thay thế placeholder hiện tại |
| 7 | Xác nhận lại số liệu quy mô thị trường logistics ở mục 27 báo cáo chính (từ 45–50 tỷ USD thành 40–42 tỷ USD/năm) và lưu snapshot nguồn | E-28 | |
| 8 | Tìm giá công khai cho Netradyne và Seeing Machines (hiện chưa có), lưu snapshot các trang nguồn | E-29 | |

---

## 5. Quy ước Nhãn Trạng thái

| Nhãn | Định nghĩa |
|---|---|
| **COMPLETE** | Phần thiết kế, phân tích hoặc mô hình đã hoàn chỉnh và sẵn sàng trình bày |
| **PARTIAL** | Một phần hoàn chỉnh; một phần đang chờ điều kiện thực địa |
| **NOT STARTED** | Chưa thực hiện — ghi nhận trung thực, không phải thiếu sót cần che giấu |
| **PENDING [X]** | Phụ thuộc kết quả của hạng mục khác; sẽ cập nhật khi có |
| **VERIFIED / MEASURED** | Đã có dữ liệu thực tế từ hệ thống hoặc thiết bị đo |
| **NOT EXECUTED** | Được ghi nhận rõ ràng là nằm ngoài phạm vi thực hiện hiện tại |

> **Nguyên tắc xuyên suốt:** Trạng thái PARTIAL hoặc NOT STARTED phản ánh đúng giai đoạn phát triển của dự án. Không được nâng nhãn lên DONE / COMPLETE / VERIFIED chỉ vì đã hoàn thành việc tổ chức tài liệu. Tổ chức bằng chứng không đồng nghĩa với hoàn thành nội dung thực địa.
