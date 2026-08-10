# E-30 — Pricing / BOM / Unit Economics
## Báo cáo Ước tính Chi phí Linh kiện Dựa trên Giá Niêm yết Thị trường

**Trạng thái:** ESTIMATED — Số liệu được xây dựng dựa trên giá niêm yết công khai. Chưa có báo giá đàm phán từ nhà cung cấp. Chưa qua giai đoạn pilot để xác thực chi phí vận hành thực tế.

---

## 1. Bảng BOM cho một bộ thiết bị (một xe — cấu hình prototype hiện tại, mục 3.1.6 báo cáo chính)

| Hạng mục | Model tham khảo | Giá thị trường công khai | Nguồn | Ngày tra cứu |
|---|---|---|---|---|
| Edge compute | NVIDIA Jetson Orin Nano Super Developer Kit (8GB) | **$249 USD** (giá niêm yết chính thức NVIDIA, giảm từ $499) | developer.nvidia.com/blog, nvidia.com | 10/08/2026 |
| Road camera | USB stereo/mono camera công nghiệp (ELP hoặc tương đương, USB2.0/3.0, industrial-grade) | **~$40–90 USD** (khoảng giá phổ biến, tùy độ phân giải và global shutter) | Khảo sát nhiều nhà cung cấp (ELP, e-con Systems, Leopard Imaging) | 10/08/2026 |
| Driver camera (cabin) | Tương tự road camera hoặc webcam công nghiệp thấp hơn | **~$25–60 USD** | Cùng nguồn trên | 10/08/2026 |
| Mount / dây nối / phụ kiện | Ước tính tổng hợp | **~$20–40 USD** | Ước tính nội bộ (chưa có báo giá chính thức) | — |
| **Tổng BOM / một xe (prototype)** | | **≈ $335 – $440 USD** | Tổng hợp các hạng mục trên | 10/08/2026 |

### Ghi chú về mức độ tin cậy của số liệu

- Giá NVIDIA Jetson Orin Nano là giá bán lẻ chính thức từ nhà sản xuất — độ tin cậy cao, có thể trích dẫn trực tiếp trong tài liệu kỹ thuật.
- Giá camera là khoảng giá tổng hợp từ nhiều nhà cung cấp OEM. **Đây chưa phải báo giá đã qua đàm phán** — cần xin báo giá chính thức (quote PDF hoặc email xác nhận) trước khi đưa vào hợp đồng hoặc cam kết thương mại với khách hàng.
- Chi phí lắp đặt, hiệu chỉnh (calibration), vận chuyển và thuế nhập khẩu chưa được tính vào bảng trên.

---

## 2. Chi phí phần mềm và dịch vụ đám mây
*(Đã có số liệu đo thực tế từ báo cáo chính, mục 14.3.2 — trạng thái: VERIFIED/MEASURED)*

| Hạng mục | Đơn giá | Nguồn |
|---|---|---|
| AWS Bedrock — deepseek.v3.2 (ap-southeast-2) | Input ~$0.0008/1.000 tokens — Output ~$0.0016/1.000 tokens | Bedrock Converse API pricing, đã đo thực tế trong [E-20] |

---

## 3. Giới hạn công bố

Các ràng buộc sau đây cần được nêu rõ khi sử dụng số liệu trong tài liệu trình bày:

1. Bảng BOM này phản ánh chi phí **một bộ thiết bị prototype** (một Jetson + hai camera). Số liệu này không đại diện cho chi phí sản xuất hàng loạt hay triển khai fleet quy mô 100 xe — chi phí sản xuất hàng loạt thường thấp hơn đáng kể nhờ chiết khấu số lượng, nhưng cần có báo giá thực tế từ nhà cung cấp khi đàm phán quy mô lớn.
2. Bảng BOM là chi phí linh kiện đầu vào, không phải giá bán sản phẩm. Giá bán ra thị trường cần tính thêm margin, chi phí R&D phân bổ, chi phí hỗ trợ kỹ thuật và các hạng mục khác.
3. Trước khi đưa vào hợp đồng hoặc cam kết với đối tác, bắt buộc phải có báo giá chính thức bằng văn bản từ nhà cung cấp cụ thể.
