# Task Ticket - Hùng & Tâm (AI/ML)

Primary scope: E-01, E-05, E-06, E-07, E-08, E-13, E-27, E-37, E-42.

## E-01 - Frozen challenge evaluation bundle

**Status: PARTIAL**  
Primary: Hùng. Supporting: Tâm.

Đã có `commands.log`, `manifest.json`, `final_evaluation_summary.json` và source report.

Việc còn lại:

- [ ] Khóa model/config/evaluator/data scope đúng release.
- [ ] Đóng `evaluation_bundle.zip`.
- [ ] Tạo SHA-256 cho bundle và từng artifact trọng yếu.
- [ ] Chạy lại lệnh từ clean environment và lưu exit code/stdout/stderr.

Lưu tại `evidence/E-01/`.

## E-05 - Alert Orchestrator state/policy/lifecycle

**Status: PARTIAL**  
Primary: Hùng. Owner review: Tâm.

Đã có policy snapshot, state trace và JUnit-style file nhưng hiện còn static placeholder.

- [ ] Tâm xác nhận policy/threshold đúng thiết kế.
- [ ] Chạy dynamic tests cho confirmation, persistence, cooldown, suppression, idempotency và OPEN/UPDATE/RESOLVED.
- [ ] Thay placeholder bằng JUnit/log từ test thật.

Lưu tại `evidence/E-05/`.

## E-06 - Raw-frame alert vs orchestrated event ablation

**Status: PARTIAL**  
Primary: Hùng. Supporting: Nhân, Tâm.

- [ ] Chốt episode boundary và label protocol.
- [ ] Replay cùng labeled episodes qua raw alert và Decision Engine.
- [ ] Xuất `ablation.csv` và `ablation_notebook.html`.
- [ ] Báo alerts/episode, duplicate rate, open delay và false alerts/hour theo denominator rõ ràng.

Lưu tại `evidence/E-06/`.

## E-07 - C3 formula and threshold verification

**Status: PARTIAL**  
Primary: Hùng.

Đã có formula, threshold, deterministic tests và sample calculation.

- [ ] Owner sign-off rằng snapshot khớp exact release source.
- [ ] Nếu BTC yêu cầu nguồn contract bên ngoài code, đính kèm PDF/screenshot và đối chiếu từng threshold.

Lưu tại `evidence/E-07/`.

## E-08 - C2 dependencies and provenance

**Status: DONE (runtime evidence)**  
Primary: Tâm.

Artifact manifest, SHA-256, dependency preflight và source/license notes đã có; preflight PASS. Không để như task mở.

Follow-up ngoài evidence runtime: legal/owner review redistribution của `Face Landmark runtime binary` trước public release.

## E-13 - C1 critical-case evaluation

**Status: PARTIAL**  
Primary: Hùng. Reviewer: Tâm.

Đã có `c1_metrics.json`.

- [ ] Chốt danger/critical bin definition.
- [ ] Xuất prediction/GT CSV theo case/scenario.
- [ ] Tạo `c1_cases.pdf` gồm worst cases và montage.
- [ ] Ghi model/config/evaluator hash.

Lưu tại `evidence/E-13/`.

## E-27 - C2 generalization evaluation

**Status: PARTIAL**  
Primary: Tâm. Supporting: Hùng.

- [ ] Đưa actual `c2_eval.json`, per-class metrics và confusion matrix vào `evidence/E-27/` thay vì chỉ dẫn đường dẫn nguồn.
- [ ] Khóa exact `candidate_013.joblib` hash, `model_version=4`, split và label policy.
- [ ] Audit subject/trip-disjoint; nếu không chứng minh được thì disclosure rõ random 70/30 limitation.
- [ ] Bổ sung dataset provenance/license snapshot.

## E-37 - Stereo calibration audit

**Status: DONE**  
Primary: Hùng. Supporting: Dân.

`baseline_distribution.csv` và `epipolar_montage.png` đã tồn tại. Không để như task mở. Chỉ đổi format sang PDF nếu packet cuối yêu cầu.

## E-42 - Domain gap and model drift

**Status: OPEN**  
Primary: Tâm. Supporting: Hùng.

- [ ] Xác nhận real-data consent và provenance.
- [ ] Khóa baseline domain và target domain.
- [ ] Tính PSI/KS hoặc metric phù hợp trên các feature so sánh được.
- [ ] Xuất domain-gap report kèm sample size và limitation.

Lưu tại `evidence/E-42/`.
