# FPTU DMS Vision – Proposal README

> Chuyển đổi nội dung proposal sang tài liệu README.
>
> **Vai trò file:** cam kết gốc giai đoạn Proposal, được giữ nguyên để so sánh
> với kết quả C2. Không dùng file này để mô tả trạng thái triển khai hiện tại.

---

# Slide 1 – PROPOSAL HACKATHON 2026

## Title
**PROPOSAL HACKATHON 2026**

**Date**
- Hanoi, July 12, 2026

---

# Slide 2 – BAREM ĐIỂM VÒNG PROPOSAL

## Tiêu chí chấm điểm

### Ý tưởng (35)
- Mô tả rõ ràng bài toán
- Giá trị thực tế
- Tiềm năng phát triển

### Tính khả thi (30)
- Có thể triển khai
- Kiến trúc rõ ràng
- Flow hợp lý

### Hiểu đề & Starter Pack (20)
- Hiểu đúng đề
- Tận dụng Starter Pack

### Năng lực đội (15)
- Phân công hợp lý
- Khả năng thực thi

---

# Slide 3 – Table of Contents

1. Thông tin đội chơi
2. Bài tập lựa chọn
3. Vấn đề & Các giải pháp
4. Lộ trình Vòng 2

---

# Slide 4 – Thông tin đội chơi

## Team
**FPTU DMS Vision**

### Thành viên
- Đoàn Ngọc Nhân — Team Lead, Backend
- Dương Thị Mỹ Tâm — AI & Backend
- Phan Lê Thanh Hùng — AI & Backend
- Trương Tô Dân — IoT & Embedded
- Nguyễn Trí Thiện — Frontend & UI/UX

---

# Slide 5 – Hình ảnh đội chơi

- Ảnh nhóm
- Avatar đội: **FPTU DMS Vision**

---

# Slide 6 – Thông tin bài tập

## Đề tài
**DMS-10 – Driver Intelligence Platform**

### Mục tiêu
- Live Fleet Monitor
- Driver Behavior Analytics
- Unified Risk Score

### Input
- Driver Camera
- Road Camera
- Telemetry

### Output
- Fleet Dashboard
- Risk Score
- Coaching Report

---

# FPTU DMS Vision – Proposal Hackathon 2026

> Nội dung được chuyển từ slide sang Markdown. Phần dưới đây ghi chi tiết từ **Slide 7 đến Slide 17**.

---

# Slide 7 – VẤN ĐỀ CẦN GIẢI QUYẾT

## Thông điệp chính

> **Tai nạn không bắt đầu bằng một cảnh báo – mà bằng nhiều tín hiệu nguy hiểm bị nhìn riêng lẻ.**

## RỦI RO ĐANG BỊ NHÌN THẤY TỪNG MẢNH

Trạng thái tài xế, nguy cơ trên đường và phản ứng của phương tiện đều được ghi nhận – nhưng chưa được kết nối để cho thấy bức tranh nguy hiểm thực sự.

### Dữ liệu biết từng phần – không ai hiểu toàn cảnh

Camera tài xế, camera đường và telemetry hoạt động với độ trễ, ngữ cảnh và mức tin cậy khác nhau.

### Cảnh báo càng nhiều – niềm tin càng ít

Những tín hiệu đơn lẻ dễ tạo cảnh báo thiếu ngữ cảnh. Khi cảnh báo biến thành tiếng ồn, người dùng sẽ bỏ qua cả nguy hiểm thật.

### Fleet Manager luôn biết sau khi sự việc đã xảy ra

Người quản lý thấy danh sách sự kiện, nhưng chưa thể biết xe nào cần ưu tiên, vì sao nguy hiểm và phải hành động thế nào.

## Kết luận

> **Bài toán không phải phát hiện thêm một sự kiện.**  
> **Bài toán là nhận ra đúng rủi ro trước khi quá muộn.**

---

# Slide 8 – INSIGHT KHÁC BIỆT

## Giá trị xuất hiện khi các tín hiệu được hiểu cùng nhau

Một tín hiệu chỉ mô tả sự kiện. Bối cảnh kết hợp mới cho thấy rủi ro đang hình thành.

### TRẠNG THÁI TÀI XẾ

- Mệt mỏi
- Mất tập trung

### NGUY CƠ TRÊN ĐƯỜNG

- TTC giảm
- Vật cản xuất hiện

### PHẢN ỨNG PHƯƠNG TIỆN

- Tốc độ
- Phanh
- Góc lái

## CONTEXT FUSION

# RISK INTELLIGENCE

Hiểu mối quan hệ giữa các tín hiệu – không chỉ đếm sự kiện.

## MỘT KẾT LUẬN CÓ THỂ HÀNH ĐỘNG

### XE NÀO ĐANG NGUY HIỂM?

- Vì sao rủi ro tăng?
- Cần ưu tiên hành động gì?

> **Đây là bước chuyển từ giám sát sự kiện sang hiểu và quản trị rủi ro.**

---

# Slide 9 – Ý TƯỞNG TRIỂN KHAI

## Kiến trúc phân tán – Thông minh ở xe, kiểm soát ở HQ

> **Mỗi chiếc xe là một điểm quyết định độc lập. HQ là trung tâm điều hành thông tin.**

## Ví dụ Visual Layout

- Xe 1 – DMS Box
- Xe 2 – DMS Box
- ...
- Xe N – DMS Box
- API Gateway (Internet/4G)
- Fleet Dashboard  
  *(Tập trung điều hành, xem toàn bộ đội)*

## Mô hình 3 tầng

### Tầng 1 – Vehicles

Mỗi xe có DMS Box – cái “bộ não” cục bộ.

### Tầng 2 – Gateway

Kênh liên lạc giữa xe và trung tâm.

### Tầng 3 – HQ

Fleet Dashboard – nơi quản lý toàn bộ đội.

## Key Insight

> “Tại sao phân tán? Để nghe ở slide tiếp...”

### Câu hỏi chuyển tiếp

> **Nhưng tại sao lại phân tán như vậy?**  
> **Có 2 lý do rất quan trọng.**

---

# Slide 10 – LỢI THẾ #1: REAL-TIME LOCAL PROCESSING

## Độ trễ edge box < cloud và không phụ thuộc mạng 4G

### Vấn đề

> “Xe chạy ở đèo, núi, khu vực mạng 4G bị gián đoạn. Nếu gửi ảnh lên cloud xử lý, chậm 2–3 giây. Trong thời gian đó tài xế có thể ngủ gục và gây tai nạn.”

### Giải pháp

> “DMS Box xử lý ảnh cục bộ. Chỉ trong 500ms, đã cảnh báo tài xế. Không cần chờ Internet.”

### Lợi ích chính

- Mạng Việt Nam không ổn định → edge-first phù hợp thực tế.
- An toàn tài xế không thể chờ đợi.
- Khác biệt rõ ràng so với competitors.

## Thông điệp

> “500ms là con số gì? Đó là thời gian tối thiểu để tài xế phản ứng với môi trường. Nhanh hơn sẽ không cần thiết.”

---

# Slide 11 – LỢI THẾ #2: DATA-LEVEL DECISIONS

## Chỉ gửi kết luận, không gửi ảnh

## Bảng so sánh luồng dữ liệu

### Cách tiếp cận truyền thống

Camera  
→ Video thô  
→ Cloud  
→ Xử lý đám mây  
→ Cảnh báo

#### Vấn đề

- Gửi video thô liên tục, khoảng 10 GB/ngày.
- Chi phí rất cao:
  - Băng thông lớn.
  - Lưu trữ đám mây.
- Bảo mật:
  - Truyền và lưu trữ hình ảnh thô.
  - Lưu trữ hình ảnh đầy đủ.
- Tốc độ chậm:
  - Trễ cao.
  - Có thể lớn hơn 5 giây.

### Cách tiếp cận của chúng tôi

Camera  
→ Trích xuất Feature  
→ Ra quyết định cục bộ  
→ Gửi cảnh báo

#### Lợi ích

- Gửi dữ liệu tóm tắt:
  - Rất nhẹ.
  - Event-based.
- Chi phí thấp và tối ưu.
- Bảo mật:
  - Không lưu trữ hình ảnh thô.
  - Xử lý tại biên.
  - Chỉ gửi tín hiệu.
- Tốc độ nhanh:
  - Real-time.
  - Dưới khoảng 50ms.

## Giá trị

- **Efficiency:** Bandwidth tiết kiệm → server cost thấp.
- **Privacy:** Không lưu ảnh tài xế → comply GDPR, bảo vệ privacy.
- **Security:** Ít dữ liệu cá nhân → ít rủi ro data breach.
- **Ethics:** Transparent – tài xế biết chúng tôi không lưu ảnh của họ.

## Câu hỏi chuyển tiếp

> **Vậy cụ thể kiến trúc sẽ như thế nào?**

---

# Slide 12 – KIẾN TRÚC & STARTER PACK SỬ DỤNG

## Tổng quan pipeline

### 1. DMS Box thu tín hiệu

**Nguồn dữ liệu:**

- Driver camera.
- Road camera stereo.
- Telemetry từ dataset trip.

**Tài nguyên sử dụng:** Starter Pack.

---

### 2. Phát hiện trạng thái & TTC

- Driver-state: tự xây.
- Baseline TTC Predictor: stereo SGBM.
- Kết hợp tài nguyên Starter Pack và phần tự xây.

**Tài nguyên sử dụng:** Starter Pack + Tự xây.

---

### 3. Context Fusion & Risk Engine

Kết hợp:

- Driver-state.
- TTC.
- Context:
  - Trip.
  - Road.
  - Vehicle.

Kết quả:

- Unified Risk Score.
- Có explainability.

**Tài nguyên sử dụng:** Tự xây.

---

### 4. Fleet Dashboard

Các chức năng:

- Live Map.
- Alert Log.
- Behavior Analytics.
- Coaching Report tự động.

**Tài nguyên sử dụng:** Tự xây.

---

## Cách dùng Starter Kit cụ thể

### Dataset Loader + Explorer Notebook

Nạp trip data, visualize driver-state timeline/TTC để debug nhanh trong 3 tuần.

### Baseline TTC Predictor

Dùng thẳng làm road-risk stream cho MVP, chỉ tối ưu thêm nếu còn thời gian – tập trung nguồn lực AI vào driver-state fusion và explainability, đúng thế mạnh của đội.

---

# Slide 13 – KIẾN TRÚC & NGUYÊN LIỆU STARTER PACK SỬ DỤNG

## Nguồn dữ liệu đầu vào

### Starter Pack

- GPS.
- Face Camera.
- Road Camera.

### Raw Data

Dữ liệu thô đi vào Feature Extraction và Context.

---

## Luồng xử lý

### 1. Feature Extraction

- Primitive → domain features.

**Nguồn:** Tự xây.

---

### 2. Fusion (1)

- Rule + ML → driver event.

**Nguồn:** Tự xây.

---

### 3. Context

- Trip.
- Road.
- Môi trường.
- Các thông tin ngữ cảnh liên quan.

---

### 4. Context Fusion (2)

- Driver event.
- Context.
- TTC baseline.
- New model.

**Nguồn:** Starter Pack + Tự xây.

---

### 5. Decision Engine

- Sinh alert.
- Xác định driver state.

**Nguồn:** Starter Pack + Tự xây.

---

### 6. Local Warning

- Cảnh báo ngay trên xe.

**Nguồn:** Tự xây.

---

### 7. API Gateway

- Versioning.
- Rate limiting.

Điều kiện:

- Nếu alert kéo dài lớn hơn ngưỡng thì gửi lên hệ thống trung tâm.

**Nguồn:** Tự xây.

---

### 8. Fleet Dashboard

- Giám sát.
- Cảnh báo.
- Báo cáo.

**Nguồn:** Tự xây.

---

## Offline-first

Nếu mất kết nối, DMS Box lưu hàng đợi offline-first và tự đồng bộ khi có mạng trở lại.

---

## Cách dùng Starter Kit cụ thể

### Dataset Loader + Explorer Notebook

Nạp trip data, visualize driver-state timeline/TTC để debug nhanh trong 3 tuần.

### Baseline TTC Predictor

Dùng thẳng làm road-risk stream cho MVP, chỉ tối ưu thêm nếu còn thời gian – tập trung nguồn lực AI vào driver-state fusion và explainability, đúng thế mạnh của đội.

---

# Slide 14 – LỘ TRÌNH VÒNG 2 – 3 TUẦN

## Từ pipeline DMS đến demo end-to-end

---

## Tuần 1 – Dựng đường ống

### Must-have

- Chạy được DMS Box pipeline:
  - Driver-state hard-rule.
  - Chạy trên Pi 5 + Hailo-8L.
- Tích hợp Baseline TTC Predictor làm road stream.
- Dựng local message broker + offline queue.

---

## Tuần 2 – Kết nối hệ thống

### Must-have

- API Gateway:
  - MQTT/gRPC → WebSocket.
- Dashboard MVP:
  - Live Map.
  - Alert Log.
- Unified Risk Score có explainability cơ bản.

### Nice-to-have

- Behavior Analytics Panel chi tiết.

---

## Tuần 3 – Hoàn thiện & Demo

### Must-have

- Kiểm thử mất mạng.
- Đo latency.
- Đo false alarm.
- Post-trip Coaching Report tự động.
- Video demo 5–7 phút.
- Writeup.

### Nice-to-have

- Cải thiện TTC vượt baseline.
- Thử một chiều Remote Back-to-Car.

---

## Ghi chú quan trọng

### Phương án dự phòng

Nếu giữa Tuần 2 chưa ổn định, chuyển hướng nộp mức tương đương Đề 02 – Collision Risk Monitor.

### Nguyên tắc MVP

Ưu tiên rule-based có thể giải thích được. ML/Hybrid Engine như XGBoost hoặc CatBoost chuyển sang roadmap sau hackathon.

### Ký hiệu

- ■ = Must-have.
- □ = Nice-to-have – chỉ làm nếu kịp.

---

# Slide 15 – TẦM NHÌN CỦA ĐỘI

## Tuyên bố

> **Biến mỗi phương tiện thành một mắt xích chủ động trong mạng lưới an toàn đội xe.**

Chúng tôi không muốn dừng lại ở một hệ thống phát hiện buồn ngủ hay một dashboard hiển thị cảnh báo.

Tầm nhìn của đội là xây dựng một **Driver Risk Intelligence Platform** có khả năng hiểu đồng thời tài xế, phương tiện và môi trường đường – từ đó dự báo, giải thích và hỗ trợ xử lý rủi ro trước khi sự cố xảy ra.

---

## HÔM NAY

Hợp nhất:

- Trạng thái tài xế.
- TTC.
- Telemetry.

Thành một đánh giá rủi ro thống nhất, giúp Fleet Manager biết:

- Xe nào đang cần ưu tiên?
- Điều gì khiến rủi ro tăng?
- Tài xế cần cải thiện hành vi nào?

---

## TIẾP THEO

Khi được triển khai trên nhiều phương tiện, hệ thống có thể học từ lịch sử vận hành để:

- Nhận diện tài xế, khung giờ và tuyến đường có rủi ro cao.
- Cá nhân hóa ngưỡng cảnh báo theo từng tài xế và điều kiện lái.
- Đề xuất coaching sau chuyến đi dựa trên bằng chứng thực tế.
- Giúp doanh nghiệp chuyển từ xử lý sự cố sang quản trị rủi ro chủ động.

---

## TƯƠNG LAI

Khi phát hiện nguy hiểm, nền tảng không chỉ cảnh báo người quản lý mà còn có thể gửi phản hồi an toàn trở lại phương tiện:

- Cảnh báo phù hợp với mức độ rủi ro.
- Gợi ý giảm tốc hoặc nghỉ ngơi.
- Hỗ trợ cockpit đưa ra phản ứng theo ngữ cảnh.
- Duy trì cảnh báo cục bộ khi xe mất kết nối.

## Thông điệp cuối

> **Từ giám sát sự kiện → hiểu rủi ro → chủ động phòng ngừa.**

---

# Slide 16 – TẦM NHÌN PHÁT TRIỂN & GIÁ TRỊ THỰC TIỄN

## KHẢ NĂNG PHÁT TRIỂN

Nền tảng được thiết kế mở để OEM và doanh nghiệp vận tải có thể bổ sung:

- Camera, cảm biến và nguồn telemetry mới.
- Mô hình AI phát hiện hành vi mới.
- Quy tắc an toàn riêng cho từng loại hình đội xe.
- API tích hợp với hệ thống quản lý vận tải, bảo hiểm và bảo trì.

---

## GIÁ TRỊ DÀI HẠN

### Đối với tài xế

Được cảnh báo đúng lúc, đúng ngữ cảnh.

### Đối với Fleet Manager

Biết nơi cần ưu tiên hành động.

### Đối với doanh nghiệp

Giảm rủi ro vận hành và xây dựng văn hóa lái xe an toàn.

### Đối với OEM

Có một lớp Risk Intelligence có thể tích hợp và mở rộng trên nhiều dòng xe.

> **Mỗi chuyến đi không chỉ tạo ra dữ liệu – mà còn giúp chuyến đi tiếp theo an toàn hơn.**

---

# Slide 17 – THANK YOU

## FPT Software Company Limited

**Địa chỉ:**

FPT Cau Giay Building, Duy Tan Street, Cau Giay Ward, Hanoi City, Vietnam.

**Tel:** +84 (24) 3 768 9048  
**Fax:** +84 (24) 3 768 9049

# THANK YOU!
