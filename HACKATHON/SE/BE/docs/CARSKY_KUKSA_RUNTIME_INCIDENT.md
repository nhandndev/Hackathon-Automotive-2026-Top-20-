ê# CarSky KUKSA Runtime Incident

## Kết luận hiện tại

Backend, AI contract và APK/HMI chưa phải nguyên nhân làm deployment đứng ở
`0/N nodes ready`. CarSky đang kẹt ở tầng provisioning/runtime: KUKSA Broker và
Skycraft không vượt qua bước `PodInitializing`, còn Script Node container chạy
nhưng sidecar chưa ready nên toàn room không đạt trạng thái usable.

Đây là blocker thuộc tầng cluster/runtime của CarSky và cần BTC kiểm tra
Kubernetes events, init-container, volume mount, image pull hoặc registry/runtime
của node `kuksa-databroker` và `skycraft`.

## Bằng chứng đã kiểm tra ngày 2026-07-26

1. Script Node Health Test chạy được và liên tục in `DMS_DEVICE_HEALTH_OK`.
2. Blueprint KUKSA dùng artifact DMS hợp lệ nhưng pod đứng `Pending`.
3. Blueprint KUKSA dùng đúng artifact VSS của blueprint BTC `FPTU DMS Vision` vẫn
   đứng `Pending`.
4. Blueprint KUKSA tối giản, không artifact và không prefix:
   - CarSky validation: `valid: true`.
   - Deployment tạo namespace thành công.
   - Node phase: `Provisioning`.
   - Pod phase: `Pending`.
   - Container `kuksa-databroker`: `waiting`.
   - API log trả: `PodInitializing` nên chưa có application log.
5. Cùng blueprint tối giản được thử trên hai device khác nhau và cho kết quả giống
   nhau. Vì vậy không phải lỗi riêng của device.
6. Device BTC `FPTU DMS Vision` đã được dùng để kiểm tra theo quyền nhóm:
   - Deployment test KUKSA tối giản đang chiếm device đã được xóa.
   - Deploy lại blueprint BTC gốc `FPTU DMS Vision` thất bại ở preflight:
     `node 'IVI - Android': skycraft requires 'image' config with VM image artifact details`.
   - Blueprint BTC gốc có vẻ là bản demo cũ, node `IVI - Android` thiếu
     `config.image` theo schema Skycraft hiện tại.
7. Deploy blueprint DMS HMI 3-node của nhóm lên device `FPTU DMS Vision`:
   - Blueprint validation: `valid: true`.
   - Deployment ID: `17738907-0a7c-49bc-b94c-b913d9d06812`.
   - Namespace: `room-rxc03zqo`.
   - Status sau 60 giây: `DEPLOYING`, `0/3 nodes ready`.
   - `DMS Signal Broker`: node phase `Provisioning`, pod `Pending`,
     container `kuksa-databroker` `waiting`, log API trả `PodInitializing`.
   - `DMS HMI Bridge`: pod `Running`, container `script-node` `running`,
     container `sidecar` `waiting`; live log API không đọc được vì CarSky yêu
     cầu container name nhưng endpoint không expose tham số container.
   - `DMS Android HMI`: node phase `Provisioning`, pod `Pending`, container
     `skycraft` `waiting`, log API trả `PodInitializing`.
8. Kiểm tra thêm theo hướng CMD/ENTRYPOINT/restart/debug:
   - Blueprint config của `DMS Signal Broker` chỉ chứa VSS artifact:
     `artifactId=Q4ruRJhflspQoU0SY1l2f`, `versionId=Gf_KU8fO-yAnonHE8gNe7`,
     `version=0.0.3`.
   - Không có CMD, ENTRYPOINT, `--vss`, `--grpc-port`, `RUST_LOG` hoặc `LOG_LEVEL`
     trong blueprint/repo; các tham số này do CarSky runtime sinh ở tầng
     Kubernetes/container.
   - Restart đúng runtime node Broker `n-1408douatrkcwxba9bm3d-n0` trả
     `500 Internal server error`.
   - Sau restart, CarSky tạo thêm pod Broker mới
     `n-1408douatrkcwxba9bm3d-n0-5f5dccc7d-lcnwz`, nhưng pod mới vẫn `Pending`,
     container `kuksa-databroker` vẫn `waiting`, log vẫn `PodInitializing`.
   - Vì container chưa start, không thể thêm debug flag ở runtime qua endpoint
     hiện có; cần BTC/admin xem hoặc sửa manifest/generated pod spec.
9. Blueprint/device `FPTU DMS Vision` của BTC không bị sửa trực tiếp. Chỉ có
   deployment test được xóa và deployment DMS HMI của nhóm được tạo để kiểm tra.

## Những nguyên nhân đã loại trừ

- JSON output của AI.
- Backend REST/WebSocket.
- Lua bridge.
- APK/HMI Android.
- Edge KUKSA/VHAL.
- Custom VSS artifact của nhóm.
- Sai device riêng lẻ.
- Blueprint validation.
- Thiếu `config.image` trong blueprint DMS HMI của nhóm.

## Việc BTC cần kiểm tra

- Kubernetes events của pod KUKSA đang `PodInitializing`.
- Kubernetes events của pod Skycraft đang `PodInitializing`.
- Trạng thái init-container, volume mount, image pull và registry credentials.
- Image/runtime mặc định của node type `kuksa-databroker` và `skycraft` trong
  workspace.
- Vì sao API chỉ trả container chính ở trạng thái `waiting` nhưng không trả chi tiết
  init-container hoặc pod events.
- Vì sao restart riêng Broker trả `500 Internal server error` nhưng vẫn tạo thêm
  pod Broker mới ở trạng thái `Pending`.
- Generated pod spec của Broker đang truyền CMD/ENTRYPOINT/args/env gì, đặc biệt
  `--vss`, `--grpc-port`, `RUST_LOG` hoặc `LOG_LEVEL`.
- Vì sao blueprint BTC gốc `FPTU DMS Vision` không deploy lại được do node
  `IVI - Android` thiếu `image` config.
- Sau khi sửa, xác nhận:
  - Blueprint một KUKSA Broker có thể đạt `1/1 nodes ready`.
  - Blueprint DMS HMI 3-node có thể đạt `3/3 nodes ready`.

## Nội dung gửi BTC

> Chào BTC, nhóm em đang bị blocker ở Nydus KUKSA Broker. Blueprint đã validate
> `valid: true`, namespace được tạo nhưng node luôn ở Provisioning, pod Pending và
> container `kuksa-databroker` ở waiting. Khi mở log, API trả container đang
> `PodInitializing`, chưa có application log. Nhóm đã thử: (1) VSS artifact của
> nhóm, (2) đúng VSS artifact từ blueprint BTC `FPTU DMS Vision`, và (3) KUKSA
> schema-less không artifact; đồng thời thử trên hai device khác nhau, kết quả đều
> giống nhau. Nhóm cũng deploy thử blueprint DMS HMI 3-node lên device BTC
> `FPTU DMS Vision`: deployment tạo được namespace `room-rxc03zqo` nhưng vẫn
> `0/3 nodes ready`; KUKSA và Skycraft đều `PodInitializing`, Script Node container
> chạy nhưng sidecar waiting. Deploy lại blueprint BTC gốc `FPTU DMS Vision` bị
> preflight fail vì node `IVI - Android` thiếu `image` config theo schema Skycraft
> hiện tại. Nhờ BTC kiểm tra Kubernetes events/init-container, volume mount, image
> pull, registry hoặc runtime của `kuksa-databroker` và `skycraft`, đồng thời xác
> nhận blueprint BTC mẫu nên deploy bằng config image nào. Nhóm có thể cung cấp
> thời điểm kiểm tra 2026-07-26, deployment ID
> `17738907-0a7c-49bc-b94c-b913d9d06812`, namespace `room-rxc03zqo`, blueprint
> `DMS Driver Safety HMI UI` và blueprint `DMS Broker Schema-less Atomic` nếu cần
> tái hiện.

## Tiếp tục sau khi BTC xác nhận đã sửa

1. Deploy `DMS Broker Schema-less Atomic` và chờ `1/1 nodes ready`.
2. Deploy topology DMS gồm KUKSA Broker, DMS HMI Bridge và Android HMI; chờ
   `3/3 nodes ready`.
3. Cài APK, mở Screen/ADB widget.
4. Gửi mock signal theo AI contract.
5. Nghiệm thu số liệu, cảnh báo và text-to-speech trên HMI.

Không cần chạy lại Phase 01-04 và không cần thay đổi AI contract để xử lý incident
này.
