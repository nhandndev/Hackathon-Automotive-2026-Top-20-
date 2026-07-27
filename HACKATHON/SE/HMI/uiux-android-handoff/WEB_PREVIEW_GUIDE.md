# Cách xem demo HMI bằng web preview

File này dành cho team UI/UX nếu họ làm ở repo riêng và chưa build APK thật.

Mục tiêu: mở một trang web local để xem HMI sẽ hiển thị như thế nào ở 3 trạng thái Safe/Warning/Critical.

## 1. Cách nhanh nhất

Mở trực tiếp file:

```text
preview/index.html
```

Bằng Chrome/Safari/Edge.

Trong màn hình preview có 3 nút:

- SAFE
- WARNING
- CRITICAL

Bấm từng nút để xem layout đổi theo state.

## 2. Nếu browser chặn file local

Chạy server local đơn giản.

Tại folder handoff:

```bash
cd uiux-android-handoff
python3 -m http.server 5179
```

Mở:

```text
http://localhost:5179/preview/
```

## 3. Preview này dùng để làm gì

Preview dùng để:

- Designer xem layout nhanh.
- Test màu Safe/Warning/Critical.
- Test text tiếng Việt.
- Test bố cục landscape 16:9.
- Chụp screenshot gửi Nhân.
- Làm bản mẫu trước khi port sang Android APK.

Preview không phải APK thật.

## 4. Preview phải hoạt động độc lập

Vì folder này có thể nằm ở repo riêng, preview phải:

- Không cần Backend.
- Không cần CarSky.
- Không cần API key.
- Không cần internet.
- Không dùng CDN nếu có thể tránh.
- Dùng sample data local.

Sample data nằm ở:

```text
preview/sample-states.json
```

Nếu muốn đơn giản, có thể hardcode sample state trong `index.html`, nhưng không được hardcode API key thật.

## 5. Kích thước màn hình mục tiêu

Thiết kế theo:

```text
1920 x 1080
landscape
16:9
```

Khi xem trên web, có thể resize browser để kiểm tra.

## 6. Nếu team dùng Figma

Nên thiết kế frame:

```text
1920 x 1080
```

Export screenshot:

```text
screenshots/safe.png
screenshots/warning.png
screenshots/critical.png
```

Sau đó implement gần giống trong:

```text
preview/index.html
```

## 7. Nếu team muốn làm web thành APK

Có thể làm hướng WebView APK.

Nhưng preview web cần chuẩn trước:

```text
preview/index.html
preview/styles.css
preview/app.js
```

Sau đó mới đóng vào Android WebView.

Lưu ý:

- WebView trên Android Automotive có thể khác browser desktop.
- Không nên dùng animation quá nặng.
- Không nên phụ thuộc thư viện CDN.
- Không nên gọi CarSky REST trực tiếp từ web nếu chưa kiểm tra CORS.

## 8. Nội dung cần có trên preview

Tối thiểu phải thấy:

- AI status.
- Voice status.
- Severity title.
- Recommended action.
- Driver state.
- Risk score.
- Speed.
- Alertness.
- TTC.
- ECU status.

## 9. Khi gửi lại cho Nhân

Gửi kèm:

- Folder preview.
- Screenshot 3 state.
- Ghi rõ preview đã map sang Android chưa.

Ví dụ trong README output:

```md
## Preview

- Open: preview/index.html
- States: SAFE/WARNING/CRITICAL
- Internet required: no
- Backend required: no

## Android status

- Native Android source included: yes/no
- WebView APK included: yes/no
```
