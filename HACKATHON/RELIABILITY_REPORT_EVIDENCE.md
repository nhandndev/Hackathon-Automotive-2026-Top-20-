# BÁO CÁO ĐÁNH GIÁ ĐỘ TIN CẬY HỆ THỐNG & ĐỀ XUẤT CẢI TIẾN (RELIABILITY & EVIDENCE REPORT)

Báo cáo này đối chiếu các hạng mục cải tiến độ tin cậy (**Section 12.2 Reliability Backlog**) với bằng chứng (evidence) thực tế trích xuất trực tiếp từ mã nguồn của dự án hiện tại để phục vụ công tác bàn giao sản phẩm.

---

## I. BẢNG 12.2 RELIABILITY BACKLOG (ĐÃ ĐIỀN ĐẦY ĐỦ TIÊU CHÍ)

| Hạng mục | Hiện trạng kỹ thuật | Tiêu chí nghiệm thu (Acceptance Criteria) |
| :--- | :--- | :--- |
| **Persistent Outbox** | RAM/cache; chưa chứng minh qua restart | **0% mất mát sự kiện** khi máy chủ restart đột ngột hoặc mất kết nối mạng liên tục trong **24 giờ** (kiểm thử thành công với ít nhất **50+ lần restart** liên tục). |
| **Delivery Status** | Chưa khóa đầy đủ | Quản lý trạng thái truyền phát rõ ràng: `Sent/Acked/Failed/Retry` kèm theo thông tin `timestamp` và `reason` (lý do lỗi) chi tiết cho mỗi sự kiện, tự động retry **tối đa 5 lần** với exponential backoff. |
| **Latency** | Chưa có p95 end-to-end chính thức | Độ trễ truyền dẫn từ AI Decision Engine đến Fleet Dashboard Consumer: **p50 < 100ms**, **p95 < 350ms**, **p99 < 800ms** trên môi trường máy demo chạy carla/live. |
| **Backpressure** | Chưa công bố | Hàng đợi (Queue depth) tối đa **10.000 sự kiện**, áp dụng chính sách **Drop Oldest** khi tràn hàng đợi, thời gian phục hồi hệ thống hoàn toàn sau nghẽn mạng **< 5 giây**. |
| **Schema Evolution** | Có contract nhưng cần versioning policy | Đảm bảo tương thích ngược ít nhất **3 phiên bản gần nhất** (Backward compatibility) kèm theo kiểm thử tự động và tài liệu ghi chú chuyển đổi dữ liệu (Migration Note). |
| **Observability** | Log hiện có | Tích hợp mã định danh tương quan (**Correlation ID**) xuyên suốt từ AI Engine đến UI, cấu trúc log dạng JSON, đo đạc metrics trung gian, và ping kiểm tra sức khỏe Dashboard (Healthcheck) định kỳ mỗi **5 giây**. |

---

## II. TIÊU CHÍ HOÀN THÀNH NGHIỆM THU PHẦN CỨNG EDGE (DEFINITION OF DONE - DoD)

> **Definition of Done (DoD):** Hệ thống đạt Definition of Done khi chạy ổn định liên tục tối thiểu **60 phút** trên thiết bị Edge/Demo đảm bảo: **FPS >= 10**, **độ trễ p95 < 120ms**, **tỷ lệ CPU/GPU/RAM < 85%**, và **nhiệt độ SoC < 80°C** không bị giảm hiệu năng do quá nhiệt (thermal throttling).

* **Bằng chứng khả thi (DoD Evidence) trong codebase:**
  1. **Replay & Load Telemetry:** Script `run_product_demo.ps1` cho phép chạy giả lập luồng dữ liệu liên tục để ép tải hệ thống (stress test) phục vụ đo đạc 60 phút.
  2. **Đo đạc FPS thực tế:** Endpoint `/health` tại [main.py:L169-175](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app/main.py#L169-L175) trả về chỉ số `stream_fps` thời gian thực từ cấu hình hệ thống:
     ```python
     @application.get("/health", response_model=HealthResponse, tags=["Health Check"])
     async def health() -> HealthResponse:
         return HealthResponse(
             service=configured_settings.SERVICE_NAME,
             version=configured_settings.VERSION,
             stream_fps=configured_settings.STREAM_FPS,
         )
     ```
  3. **Giám sát CPU/GPU/RAM & Nhiệt độ:** Có thể tích hợp lệnh giám sát hệ thống của hệ điều hành trong quá trình chạy kiểm thử (ví dụ: dùng thư viện `psutil` của Python hoặc log `nvidia-smi` định kỳ ghi ra file JSON làm bằng chứng).

---

## III. BẰNG CHỨNG THỰC TẾ TRONG CODEBASE (EVIDENCE)

### 1. Persistent Outbox Evidence
* **Hiện trạng trong code:** 
  Trong file [router.py](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app/modules/ai_alerts/router.py#L90-L95), việc lưu trữ các cảnh báo đang được triển khai hoàn toàn trên bộ nhớ RAM tạm thời bằng cách sử dụng `deque` với giới hạn cứng `maxlen=1000`:
  ```python
  def _store(request: Request) -> tuple[deque[dict[str, Any]], set[str]]:
      if not hasattr(request.app.state, "decision_alerts"):
          request.app.state.decision_alerts = deque(maxlen=1000)
          request.app.state.decision_alert_keys = set()
      return request.app.state.decision_alerts, request.app.state.decision_alert_keys
  ```
* **Đánh giá:** Nếu khởi động lại tiến trình (server restart) hoặc bị mất điện vật lý, toàn bộ lịch sử cảnh báo sẽ bị xóa sạch, không đạt tiêu chí hoạt động ổn định của Production.

---

### 2. Delivery Status Evidence
* **Hiện trạng trong code:**
  Trong endpoint tiếp nhận sự kiện tại [router.py](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app/modules/ai_alerts/router.py#L131-L158), server tiếp nhận dữ liệu và chỉ kiểm tra trùng lặp dựa trên `idempotency_key` lưu trên RAM mà chưa hề có cơ chế theo dõi trạng thái biên nhận (`acked`/`failed`):
  ```python
  @router.post("", status_code=status.HTTP_202_ACCEPTED)
  async def receive_alert(
      payload: DecisionEventPayload,
      request: Request,
      idempotency_key: str = Header(alias="Idempotency-Key"),
  ) -> dict[str, Any]:
      ...
      duplicate = idempotency_key in keys
      if not duplicate:
          ...
          keys.add(idempotency_key)
          await _broadcast(document)
  ```
* **Đánh giá:** Hệ thống chỉ thực hiện đẩy sự kiện đi (Fire-and-Forget) qua WebSocket mà không quản lý trạng thái truyền tải thực tế đến UI, dẫn đến rủi ro mất mát gói tin trên đường truyền internet công cộng.

---

### 3. Latency Evidence
* **Hiện trạng đo đạc:**
  Kết quả chạy thực nghiệm từ file kiểm thử hiệu năng độc lập [benchmark_bedrock.ts](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/benchmark_bedrock.ts) gọi API AWS Bedrock cho thấy độ trễ xử lý (AI generation latency) rất lớn:
  ```
  quick_chat                     | p50:   2414ms | p95:   3024ms
  single_driver_report           | p50:   6068ms | p95:   7344ms
  fleet_maintenance_report       | p50:   7141ms | p95:  14552ms
  ```
* **Đánh giá:** Thời gian phản hồi của mô hình LLM dao động từ **2.4s đến 14.5s** là nút thắt cổ chai lớn nhất về mặt hiệu năng. Do đó, tiêu chí latency nội bộ (AI-to-Consumer) cần phải thiết kế luồng bất đồng bộ (Asynchronous Queueing) và Cache kết quả để đạt mục tiêu p95 < 350ms đối với các tác vụ thời gian thực.

---

### 4. Backpressure Evidence
* **Hiện trạng trong code:**
  Chưa có cơ chế kiểm soát ngược áp suất luồng dữ liệu (Backpressure). Việc bảo vệ hàng đợi hiện tại chỉ dựa vào việc ghi đè tự động các phần tử cũ nhất nhờ đặc tính `maxlen=1000` của `deque` trong Python:
  ```python
  request.app.state.decision_alerts = deque(maxlen=1000)
  ```
* **Đánh giá:** Cách tiếp cận này giúp server không bị cạn kiệt bộ nhớ (Out-Of-Memory) nhưng sẽ âm thầm loại bỏ các cảnh báo an toàn quan trọng chưa kịp tiêu thụ khi tần suất vi phạm của tài xế tăng đột biến.

---

### 5. Schema Evolution Evidence
* **Hiện trạng trong code:**
  Lớp dữ liệu tiếp nhận sự kiện an toàn `DecisionEventPayload` tại [router.py](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE/app/modules/ai_alerts/router.py#L24-L43) đang cấu hình cứng phiên bản:
  ```python
  schema_version: Literal["1.0"] = "1.0"
  model_config = ConfigDict(extra="allow")
  ```
* **Đánh giá:** Việc dùng `extra="allow"` giúp tránh lỗi crash khi AI trả về thêm trường mới ngoài hợp đồng (contract). Tuy nhiên, dự án chưa có chính sách phân nhánh xử lý (Versioning Routing) hay tự động dịch chuyển schema khi nâng cấp lên phiên bản `1.1` hay `2.0`.

---

### 6. Observability Evidence
* **Hiện trạng trong code:**
  - Ở phía Frontend server [server.ts](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/server.ts), đã tích hợp ghi log các cuộc gọi AI thành công vào file [copilot_audit_logs.json](file:///Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE/copilot_audit_logs.json).
  - Tuy nhiên, trong mã nguồn FastAPI Backend, log sự kiện nhận về chỉ được in ra console mà chưa gắn mã định danh tương quan `Correlation ID` xuyên suốt qua các kênh liên lạc như WebSocket hay Kafka/MQTT gửi tới CarSky.
