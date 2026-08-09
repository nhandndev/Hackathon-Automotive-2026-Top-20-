# E-37 - Calibration Quality là gì?

Calibration quality thuộc Challenge 1 / stereo camera.

Mục tiêu là chứng minh thông tin calibration của road stereo camera đủ tốt để tính depth/TTC.

## Vì sao cần?

Challenge 1 tính TTC từ:

```text
left road frame + right road frame + calibration -> depth -> object distance -> TTC
```

Nếu calibration sai:

- depth sai,
- khoảng cách xe/VRU sai,
- TTC sai,
- Challenge 3 risk cũng sai theo.

## Evidence thường cần

| Evidence | Ý nghĩa |
|---|---|
| baseline distribution | Baseline stereo có hợp lý và ổn định giữa trip không |
| focal length / projection matrix summary | Camera intrinsics có đọc đúng không |
| epipolar montage | Điểm/cạnh tương ứng giữa left/right có nằm cùng hàng epipolar không |
| parse log | Chứng minh calibration file đọc được cho từng trip |

## Hiện trạng

Chưa làm trong lượt này vì cần chốt dataset/calibration manifest đầu vào.

Nếu dùng Practice Dataset, input thường là:

```text
Practice_Dataset/Txx-Sample/kitti/calibration_info.txt
```

## Việc tiếp theo nếu muốn hoàn thiện

1. Parse calibration của 6 trip.
2. Xuất `baseline_distribution.csv`.
3. Vẽ montage left/right + epipolar guide lines.
4. Ghi `calibration_quality_report.md`.
