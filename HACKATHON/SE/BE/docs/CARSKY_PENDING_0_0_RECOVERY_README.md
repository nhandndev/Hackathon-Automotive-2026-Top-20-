# CarSky — Hướng dẫn sửa `Pending 0/0 nodes ready`

> Làm lần lượt từ trên xuống. Không bỏ qua bước kiểm tra. Quy trình này chỉ xoá
> deployment bị kẹt; không xoá Blueprint, Device, Artifact hoặc tài nguyên của BTC.

## 1. Hiện tượng cần sửa

Áp dụng tài liệu này khi CarSky đang hiển thị:

```text
Deployment: dms-hmi-demo-01
Status: Pending
Nodes ready: 0/0
```

`0/0` nghĩa là CarSky chưa tạo node runtime nào từ Blueprint. Không bấm
`Restart All` vì chưa có pod/node để khởi động lại.

## 2. Kiểm tra Blueprint trước khi xoá deployment

1. Mở <https://hackathon-1.carsky.io/> và đăng nhập.
2. Ở thanh bên trái, bấm `Nydus`.
3. Chọn Blueprint `DMS Driver Safety HMI UI`.
4. Xác nhận canvas có đúng ba node:
   - `DMS Signal Broker`.
   - `DMS HMI Bridge`.
   - `DMS Android HMI`.
5. Xác nhận có đúng hai đường nối:
   - `DMS Signal Broker` nối với pin `kuksa` của `DMS HMI Bridge`.
   - Pin `vhal` của `DMS Android HMI` nối với pin `vhal` của `DMS HMI Bridge`.
6. Nếu thiếu node hoặc dây, dừng tại đây và chụp màn hình. Không xoá deployment.

## 3. Kiểm tra Android Artifact

1. Trên canvas, bấm node `DMS Android HMI`.
2. Nhìn `Inspector` bên phải.
3. Trong phần Image/Artifact, xác nhận:
   - Artifact: `aaos`.
   - Version: `0.0.1`.
   - Architecture: `aarch64`.
4. Nếu Version đang trống:
   - Mở `Artifacts` ở thanh bên trái.
   - Chọn artifact `aaos`.
   - Xác nhận version `0.0.1` tồn tại.
   - Quay lại `Nydus` và chọn lại `aaos` → `0.0.1`.
5. Sau khi chọn, chờ 10 giây để giao diện lưu cấu hình.

Không tự upload Android image khác và không sửa artifact `aaos` của BTC.

## 4. Xoá riêng deployment bị kẹt

1. Trong `Nydus`, tìm danh sách `Deployments` ở góc dưới bên trái.
2. Bấm `dms-hmi-demo-01`.
3. Kiểm tra lần cuối màn hình đang ghi:

   ```text
   Pending
   0/0 nodes ready
   ```

4. Trong `Inspector` bên phải, bấm `Delete Deployment`.
5. Đọc tên trong hộp thoại xác nhận.
6. Chỉ xác nhận nếu tên chính xác là `dms-hmi-demo-01`.
7. Chờ deployment biến mất khỏi danh sách.

Thao tác này giữ lại Blueprint `DMS Driver Safety HMI UI` và ba node bên trong.

## 5. Deploy lại bằng giao diện CarSky

1. Chọn lại Blueprint `DMS Driver Safety HMI UI`.
2. Bấm vùng trống trên canvas để Inspector hiển thị thông tin Blueprint.
3. Bấm `New Deployment`.
4. Điền:
   - Deployment Name: `dms-hmi-demo-01`.
   - Device: `DMS Driver Safety HMI`.
5. Bấm `Deploy` đúng một lần.
6. Không dùng script hoặc REST API để tạo deployment thay cho bước này.

### Nếu giao diện báo `artifact version not found`

1. Không bấm Deploy lại nhiều lần.
2. Không tạo deployment bằng REST API.
3. Chụp đầy đủ thông báo lỗi.
4. Dừng quy trình và gửi BTC nội dung ở mục 9.

## 6. Theo dõi deployment mới

Mở Deployment Viewer và quan sát `nodes ready`.

Luồng bình thường:

```text
Pending 0/3
→ 1/3 hoặc 2/3 nodes ready
→ Running 3/3 nodes ready
```

Lần đầu có thể lâu vì CarSky cần tải Android image. Chờ tối đa 10 phút và theo
dõi node Android trên Dashboard.

| Trạng thái | Việc cần làm |
|---|---|
| `Pending 0/3` trong vài phút | Tiếp tục chờ |
| `1/3` hoặc `2/3` | Bấm node chưa ready và xem lỗi/log |
| `Running 3/3` | Chuyển sang bước 7 |
| Trở lại `Pending 0/0` | Dừng và gửi BTC |
| `ImagePullBackOff` | Gửi log cho BTC; không đổi image tùy ý |
| `Failed` hoặc `Degraded` | Chụp lỗi node và gửi BTC |

## 7. Xác nhận bằng Terminal

Mở Terminal tại thư mục gốc dự án:

```bash
cd SE/BE
.venv/bin/python scripts/carsky_phase05.py status
.venv/bin/python scripts/carsky_phase05.py nodes
```

Chỉ PASS khi:

- UI hiển thị `Running 3/3 nodes ready`.
- Lệnh `nodes` trả về ba runtime node.
- Có Android/Skycraft node trong kết quả.

Nếu `nodes` vẫn trả `[]`, không cài APK và không gửi mock signal.

## 8. Cài APK sau khi đạt `3/3`

Chỉ chạy sau khi bước 7 PASS:

```bash
cd SE/BE
.venv/bin/python scripts/carsky_phase05.py install-apk \
  ../HMI/app/build/outputs/apk/debug/app-debug.apk
```

Sau khi cài thành công:

1. Mở `Devices`.
2. Chọn `DMS Driver Safety HMI`.
3. Bấm dấu `+` tại `Widgets`.
4. Chọn `Screen`.
5. Chọn đúng Android video part/prefix của node `DMS Android HMI`.
6. Chờ màn hình Android xuất hiện.

Sau đó mới gửi mock:

```bash
.venv/bin/python scripts/carsky_phase05.py scenario normal
.venv/bin/python scripts/carsky_phase05.py scenario warning
.venv/bin/python scripts/carsky_phase05.py scenario critical
```

## 9. Nội dung gửi BTC nếu vẫn lỗi

```text
Chào BTC,

Blueprint "DMS Driver Safety HMI UI" đã có 3 node, 2 edge và validation thành công.
Android node đang chọn public artifact "aaos", version "0.0.1", architecture
"aarch64". Tuy nhiên UI deployment preflight báo không resolve được Android
artifact version, hoặc deployment vẫn Pending 0/0 nodes ready.

Room không có pod/runtime node; API nodes trả về []. Nhờ BTC kiểm tra:
1. Quyền resolve artifact/version aaos 0.0.1 trong workspace của đội.
2. Nydus Blueprint Operator/reconcile của device.
3. Kubernetes namespace và event của deployment.

Đính kèm: ảnh Blueprint, lỗi Deploy, Deployment Viewer và thời điểm xảy ra lỗi.
```

Không gửi password, API key hoặc nội dung file `.env`.

## 10. Những thứ tuyệt đối không xoá hoặc sửa

- Không xoá Blueprint `DMS Driver Safety HMI UI`.
- Không xoá Device `DMS Driver Safety HMI`.
- Không xoá/sửa artifact `aaos`.
- Không sửa Blueprint hoặc Device `FPTU DMS Vision` của BTC.
- Không tạo nhiều deployment để thử liên tục.
- Không dùng `Restart All` khi trạng thái là `0/0`.

## 11. Điều kiện hoàn thành

Quy trình chỉ hoàn thành khi đạt đủ:

- Deployment `Running 3/3`.
- Script `nodes` trả ba node.
- APK cài thành công.
- Screen widget hiển thị Android HMI.
- Ba scenario `normal`, `warning`, `critical` thay đổi HMI đúng.

