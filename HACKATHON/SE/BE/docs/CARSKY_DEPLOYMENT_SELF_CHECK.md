# CarSky Deployment Self-Check — DMS HMI

> Mục tiêu: tự xác nhận deployment DMS có chạy thật hay đang bị kẹt ở CarSky.
> Các bước mặc định chỉ đọc trạng thái, không tạo/xoá/sửa tài nguyên.

## 1. Tài nguyên cần kiểm tra

```text
Device:        DMS Driver Safety HMI
Room ID:       glnbfekge5m0bigg7lokc
Deployment:    dms-hmi-demo-01
Deployment ID: 87b754c0-6f2c-4927-9c36-205c48f52ef5
Namespace:     room-01yki2m8
Blueprint:     DMS Driver Safety HMI UI
Blueprint ID:  UEvNecDPUDgmOwo6-dA48
```

Không gửi mật khẩu, API key hoặc file `.env` cho người khác.

## 2. Kiểm tra nhanh trên giao diện CarSky

1. Mở `https://hackathon-1.carsky.io/` và đăng nhập.
2. Bấm `Dashboard` ở thanh menu trái.
3. Chọn card/device `DMS Driver Safety HMI`.
4. Tìm deployment `dms-hmi-demo-01`.
5. Ghi lại ba giá trị:
   - Trạng thái: `Pending`, `Deploying`, `Running`, `Degraded` hay `Failed`.
   - Số `nodes ready`, ví dụ `0/0`, `2/3` hoặc `3/3`.
   - Namespace có phải `room-01yki2m8` không.
6. Chờ 60 giây, bấm `Refresh` rồi kiểm tra lại một lần.

### Cách kết luận

| Kết quả | Kết luận |
|---|---|
| `Running`, `3/3 nodes ready` | Room đạt điều kiện để cài APK |
| `Pending`, `0/0` quá 2 phút | CarSky chưa dựng topology/pod |
| `Deploying`, `1/3` hoặc `2/3` | Bấm node chưa ready để xem lỗi |
| `Degraded`/`Failed` | Chụp node error và logs gửi BTC |
| Có namespace nhưng `0/0` | Deployment record có nhưng Operator chưa tạo node |

Không coi status API `Running` là PASS nếu Dashboard vẫn `0/0`.

## 3. Kiểm tra Blueprint không chỉnh sửa

1. Bấm `Nydus`.
2. Chọn `DMS Driver Safety HMI UI`.
3. Chỉ quan sát, không kéo node hoặc đổi dropdown.
4. Xác nhận canvas có:
   - `DMS Signal Broker`.
   - `DMS HMI Bridge`.
   - `DMS Android HMI`.
5. Xác nhận có hai dây:
   - Bridge `kuksa` → Broker `kuksa`.
   - Android `vhal` → Bridge `vhal`.
6. Chụp toàn bộ canvas.

Nếu đủ ba node và hai dây nhưng Dashboard vẫn `0/0`, lỗi nằm sau bước thiết kế Blueprint.

## 4. Kiểm tra bằng công cụ có sẵn

Mở Terminal tại thư mục dự án rồi chạy:

```bash
cd SE/BE
.venv/bin/python scripts/carsky_phase05.py status
.venv/bin/python scripts/carsky_phase05.py nodes
```

Công cụ tự đọc API key trong `.env` và không in secret.

### Kết quả tốt

`status` phải thể hiện Room `RUNNING`. `nodes` phải có ba runtime node tương ứng Broker,
Bridge và Android/Skycraft, tất cả ready/running.

### Kết quả đang bị kẹt hiện nay

```json
{
  "status": "RUNNING",
  "namespace": "room-01yki2m8"
}
```

nhưng:

```json
[]
```

Nếu `nodes` vẫn là `[]`, không chạy lệnh `install-apk` hoặc `scenario`.

## 5. Kiểm tra read-only bằng API

Chỉ dùng nếu công cụ Python không chạy. Mở Terminal tại `SE/BE`:

```bash
set -a
source .env
set +a

curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/deployments/${CARSKY_ROOM_ID}/status"

curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/deployments/${CARSKY_ROOM_ID}/nodes"

curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/deployments/${CARSKY_ROOM_ID}/pods"

curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CARSKY_API_KEY}" \
  "${CARSKY_BASE_URL}/api/v1/signals/${CARSKY_ROOM_ID}"
```

Không chụp Terminal nếu API key đang hiện trong history hoặc cửa sổ `.env` đang mở.

## 6. Khi nào mới được cài APK

Chỉ tiếp tục khi đồng thời đạt:

- Dashboard: `Running`.
- Dashboard: `3/3 nodes ready`.
- `nodes` có Android/Skycraft node.
- Signals API có node Broker.

Sau đó mới chạy:

```bash
cd SE/BE
.venv/bin/python scripts/carsky_phase05.py install-apk \
  ../HMI/app/build/outputs/apk/debug/app-debug.apk
```

Nếu `nodes=[]`, lệnh cài APK chắc chắn không có Android VM để nhận file.

## 7. Khi nào mới gửi mock signal

Sau khi APK cài thành công và Screen widget mở được:

```bash
.venv/bin/python scripts/carsky_phase05.py scenario normal
.venv/bin/python scripts/carsky_phase05.py scenario warning
.venv/bin/python scripts/carsky_phase05.py scenario critical
```

Kỳ vọng:

| Scenario | HMI |
|---|---|
| `normal` | Nền an toàn, AI ONLINE, không phát cảnh báo |
| `warning` | Màu vàng/cam, yêu cầu tập trung, voice một lần |
| `critical` | Màu đỏ, risk/TTC, yêu cầu phanh an toàn, voice ưu tiên |

## 8. Bộ ảnh cần chụp để tự kiểm tra hoặc gửi BTC

Chụp ba ảnh, không chứa secret:

1. `01-dashboard.png`: thấy deployment, status và `nodes ready`.
2. `02-blueprint.png`: thấy đủ ba node và hai dây.
3. `03-artifacts.png`: thấy artifact/version được Blueprint sử dụng hoặc lỗi preflight.

Nếu node đã được tạo nhưng không Running, chụp thêm:

4. `04-node-error.png`: badge/error của node.
5. `05-node-logs.png`: 30–50 dòng logs gần nhất.

## 9. Nội dung kết quả cần gửi lại

Điền và gửi nguyên block này:

```text
Thời điểm kiểm tra:
Dashboard status:
Nodes ready:
Namespace:
Kết quả lệnh status:
Kết quả lệnh nodes:
Kết quả lệnh pods:
Kết quả signals:
Thông báo lỗi trên UI:
Ảnh đính kèm:
```

## 10. Tuyệt đối không làm khi đang kiểm tra

- Không bấm `New Deployment` thêm lần nữa.
- Không bấm dấu `+` trong Devices.
- Không xoá Blueprint, artifact hoặc device.
- Không đổi Blueprint sang Public chỉ để thử.
- Không sửa `FPTU DMS Vision`.
- Không chạy `install-apk` khi chưa có Android runtime node.
- Không gửi mật khẩu/API key cho BTC hoặc chụp secret trong ảnh.

## 11. Tài liệu liên quan

- [Hướng dẫn sửa Pending 0/0 nodes ready](CARSKY_PENDING_0_0_RECOVERY_README.md)
- [AI contract và change memory](AI_CONTRACT_AND_CHANGELOG.md)
- [Phase 05.2 — Quy trình CarSky HMI](phases/PHASE_05_2_CARSKY_HMI_ACTION_CHECKLIST.md)
- [Android HMI README](../../HMI/README.md)
