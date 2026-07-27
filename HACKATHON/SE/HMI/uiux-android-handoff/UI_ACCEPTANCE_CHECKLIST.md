# UI acceptance checklist

Dùng checklist này để nghiệm thu folder Android UI/UX trước khi merge vào repo chính.

## 1. Checklist preview

- [ ] Mở được `preview/index.html` bằng browser.
- [ ] Preview không cần internet.
- [ ] Có nút SAFE.
- [ ] Có nút WARNING.
- [ ] Có nút CRITICAL.
- [ ] Mỗi state đổi màu rõ ràng.
- [ ] Text tiếng Việt đọc được.
- [ ] Layout là landscape 16:9.
- [ ] Không có API key thật trong preview.

## 2. Checklist Android source

- [ ] Đã đọc `APK_REQUIREMENTS_STRICT.md`.
- [ ] Không dùng tool/framework convert chưa được Nhân duyệt.
- [ ] Có `android/src/.../MainActivity.java`.
- [ ] Có `android/AndroidManifest.xml`.
- [ ] Có `android/build_demo_apk.sh` hoặc hướng dẫn build rõ ràng.
- [ ] Package là `vn.fpt.dms.hmi` hoặc đã ghi rõ nếu đổi.
- [ ] Activity chính là `.MainActivity` hoặc đã ghi rõ nếu đổi.
- [ ] App landscape.
- [ ] Không hardcode API key thật.
- [ ] Không phụ thuộc internet chỉ để vẽ UI.

## 3. Checklist thông tin hiển thị

- [ ] Có severity/title chính.
- [ ] Có recommended action.
- [ ] Có driver state.
- [ ] Có risk score.
- [ ] Có speed.
- [ ] Có alertness.
- [ ] Có TTC.
- [ ] Có AI status.
- [ ] Có voice status.
- [ ] Có ECU status.

## 4. Checklist demo

- [ ] Safe nhìn bình tĩnh, không gây hoảng.
- [ ] Warning đủ nổi bật.
- [ ] Critical rất nổi bật.
- [ ] Nhìn trong 3 giây hiểu được tình huống.
- [ ] Không nhồi quá nhiều chữ.
- [ ] Không hiển thị JSON raw cho driver.

## 5. Checklist handoff

- [ ] Có `README.md`.
- [ ] Có `DESIGN_NOTES.md`.
- [ ] Có screenshot Safe.
- [ ] Có screenshot Warning.
- [ ] Có screenshot Critical.
- [ ] Có ghi rõ cách build.
- [ ] Có ghi rõ cách test bằng mock state.

Nếu thiếu một trong các mục quan trọng trên, chưa nên merge vào demo chính.
