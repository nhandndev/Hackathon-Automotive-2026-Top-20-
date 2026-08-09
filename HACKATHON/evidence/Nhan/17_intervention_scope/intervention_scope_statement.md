# E-17 Intervention Scope Statement

## Claim

Intervention trong FPTU DMS Vision là **human workflow**, không phải actuator control.

## Scope

Hệ thống được phép:

- hiển thị cảnh báo cho tài xế;
- gửi signal trạng thái sang CarSky/HMI;
- đề xuất `recommended_action`;
- yêu cầu safety review/coaching/bảo trì;
- tạo report cho Fleet Manager.

Hệ thống không claim:

- tự động phanh;
- tự động đánh lái;
- tự động ga;
- tự động dừng xe;
- tự động can thiệp actuator.

## Evidence Command

```bash
grep -RInE "actuator|brake_command|steer|throttle|autonomous|control_vehicle|vehicle_control|stop_vehicle" AI SE scripts README* 2>/dev/null
```

## Owner Sign-Off

| Role | Name | Status |
|---|---|---|
| Product / Technical Lead | Nhân | TBD |
| SE Owner | TBD | TBD |
| AI Owner | TBD | TBD |

