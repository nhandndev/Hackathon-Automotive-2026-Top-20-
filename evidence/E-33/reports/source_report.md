# E-33 — ROI Model
## Báo cáo Mô hình ROI — Nguồn gốc Giả định và Giới hạn Công bố

**Trạng thái:** MODEL DEFINED / INPUTS ESTIMATED — Công thức và cấu trúc phân tích đúng chuẩn tài chính. Tuy nhiên, các đầu vào (inputs) là số liệu ước tính, chưa được xác thực qua pilot. Mô hình này không được sử dụng để cam kết ROI thực tế với khách hàng cho đến khi có dữ liệu pilot.

---

## 1. Nguồn gốc của Bộ Số Giả định

Bộ số được sử dụng trong mô hình ROI ("100 xe / $400/xe / $25/xe/tháng...") **không xuất phát từ dữ liệu đo thực tế của dự án**. Các con số này được xây dựng từ ba nguồn:

1. **Benchmark ngành công khai** (FMCSA / NSC / ATRI): chi phí tai nạn xe tải trung bình từ $91.000 đến $148.000/vụ.
2. **BOM ước tính tại E-30**: giá Jetson + camera đã tra cứu thực tế, làm tròn lên $400/xe để tạo buffer cho chi phí lắp đặt và vận chuyển.
3. **Giả định quy mô minh họa**: "100 xe" là kịch bản minh họa cho fleet thương mại tương lai, **không phản ánh quy mô dự án hiện tại** (dự án hiện có một bộ prototype — một Jetson, mục 3.1.6 báo cáo chính).

Mô hình này trình bày **logic tính toán tài chính**, không phải ROI đã đo được. Khi trình bày trước ban giám khảo, cần nêu rõ bản chất giả định này để tránh nhầm lẫn với kết quả thực địa.

---

## 2. Cập nhật BOM theo Giá Thị trường Đã Tra cứu

| Hạng mục | Giá trị cũ (không có nguồn) | Giá trị mới (có nguồn — E-30) |
|---|---|---|
| Chi phí phần cứng / xe | $400 (ước tính nội bộ, không có tài liệu hỗ trợ) | **$335–$440** (Jetson $249 + camera ~$65–150 + phụ kiện ~$30) |

Khoảng giá cập nhật **gần khớp** với ước tính ban đầu, do đó công thức ROI trong báo cáo Business Value trước vẫn có giá trị tham khảo. Điểm khác biệt quan trọng: giá Jetson Orin Nano $249 là giá niêm yết chính thức từ NVIDIA, làm tăng mức độ tin cậy của đầu vào BOM.

---

## 3. Hai Kịch bản Cần Phân biệt Rõ khi Trình bày

### Kịch bản A — Chi phí Prototype Hiện tại (Số liệu Thực tế, Quy mô Nhỏ)

| Hạng mục | Giá trị |
|---|---|
| Cấu hình | 1 Jetson Orin Nano + 2 camera + phụ kiện |
| Chi phí ước tính | ≈ $335–$440 |
| Bản chất | Chi phí đầu vào thực tế cho demo — không phải ROI |

### Kịch bản B — Mô hình ROI Fleet Thương mại (Giả định, Quy mô 100 Xe)

Mô hình này minh họa logic tài chính khi sản phẩm được thương mại hóa ở quy mô fleet, bao gồm ba mức kịch bản:

| Kịch bản | ROI | Thời gian hoàn vốn | Giả định chính |
|---|---|---|---|
| Conservative | 56% | 12 tháng | Không ngăn được tai nạn nào — lợi ích chỉ từ tiết kiệm vận hành |
| Base (Thực tế) | 285% | 5 tháng | Ngăn 1 tai nạn/năm + giảm 10% phí bảo hiểm |
| Optimistic | 495% | 3 tháng | Ngăn 2 tai nạn + tối ưu thêm các hạng mục khác |

**Điều kiện bắt buộc khi trình bày Kịch bản B:** Cần nêu rõ đây là **mô hình minh họa cho tương lai thương mại hóa**, không phải cam kết hay kết quả đo thực địa — nhất quán với Phụ lục B của báo cáo chính ("ROI thực địa vẫn NOT VALIDATED khi chưa có pilot thực tế").

---

## 4. Trạng thái Chi tiết và Lộ trình Nâng cấp

| Thành phần | Trạng thái | Ghi chú |
|---|---|---|
| Công thức và phân loại 3 kịch bản | **COMPLETE** | Đã có nguồn BOM từ E-30; sẵn sàng trình bày |
| Baseline log (dữ liệu vận hành thực tế) | **PENDING E-32** | Phụ thuộc tuần tự hợp lý: model cần có trước, dữ liệu đổ vào sau khi pilot hoàn thành |

**Các việc còn lại không phụ thuộc trực tiếp vào baseline log:**
- Có báo giá chính thức (quote) từ nhà cung cấp Jetson và camera → thay khoảng giá bằng số cố định.
- Có xác nhận từ đối tác bảo hiểm Việt Nam về mức giảm phí thực tế (hiện đang giả định 10% theo thị trường Mỹ — thị trường Việt Nam chưa có chính sách tương đương, đã được cảnh báo trong báo cáo Business Value trước đó).
