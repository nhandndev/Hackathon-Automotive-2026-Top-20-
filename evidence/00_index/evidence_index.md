# Evidence Index

| ID | Claim | Owner | File | Hash | Ngày | Status |
|---|---|---|---|---|---|---|
| E-01 | Reproducibility C1/C2/C3 | Hùng/Tâm | evidence/01_reproducibility/evaluation_bundle.zip | f7995dfec7c76c089b74d217aec3e675b29d487db5661f6664d2d7ce4b267b64 | 2026-08-09 | ✨ C1 bundled (config+v2 weights+evaluator+TTC engine, real hashes in manifest.json). C2/C3 still pending owner |
| E-02 | AS-IS architecture khớp code | Nhân/Hùng | evidence/02_architecture/source_map.csv | | | Draft — BE parsed via AST (chính xác cao), FE parsed via regex (cần review thủ công), pending owner sign-off |
| E-03 | DecisionEvent schema thống nhất | Nhân/Hùng | evidence/03_decision_schema/decision_event.schema.DRAFT-UNVERIFIED.json | | | DRAFT — pending owner review |
| E-04 | Golden event trace (end-to-end) | Nhân/Hùng/Thiện/Dân | | | | |
| E-05 | Alert Orchestrator state/policy | Hùng | | | | |
| E-06 | Ablation: raw alert vs orchestrated | Hùng/Nhân | | | | |
| E-07 | C3 formula/thresholds | Hùng | | | | |
| E-08 | C2 dependencies đầy đủ | Tâm | | | | |
| E-09 | Edge performance đo trên target thật | Dân/Hùng | | | | |
| E-10 | Edge thermal/power/stability | Dân/Hùng | | | | |
| E-11 | CARLA dataset manifest đầy đủ | Dân/Hùng | | | | |
| E-12 | CARLA collection tái lập được | Dân | | | | |
| E-13 | C1 critical cases evaluated | Hùng | | | | |
| E-14 | Backend reliability giới hạn đúng thực tế| Nhân | | | | |
| E-15 | Automated test claims traceable | Nhân/Hùng | | | | |
| E-16 | Failure handling demonstrated | Nhân/Technical Team | | | | |
| E-17 | Intervention chỉ là human workflow | Nhân/Thiện | | | | |
| E-18 | Release packet immutable | Nhân | | | | |
| E-19 | Copilot grounded, không bịa | Nhân/Thiện | | | | |
| E-20 | Copilot latency/cost/failure | Nhân | | | | |
| E-21 | Report export chính xác | Thiện | | | | |
| E-22 | Dashboard workflow | Thiện | | | | |
| E-23 | Dashboard fails honestly | Thiện | | | | |
| E-24 | CarSky/KUKSA/VHAL/APK correlation | Dân/Nhân | | | | |
| E-25 | Audio path | Dân | | | | |
| E-26 | Clean-room build | Nhân/Technical Team | | | | |
| E-27 | C2 generalization | Tâm | | | | |
| E-28 | Market/context statistics sourced | Nhân | | | | |
| E-29 | Competitive gap factual | Nhân | | | | |
| E-30 | Pricing/BOM coherent | Nhân/Dân | | | | |
| E-31 | User/buyer hypotheses tested | Nhân | | | | |
| E-32 | Pilot value measurement | Nhân/Hùng | | | | |
| E-33 | ROI not invented | Nhân | | | | |
| E-34 | Safety/privacy gates | Nhân/Dân | | | | |
| E-35 | Evidence index | Nhân/Thiện | | | | |
| E-36 | Long-run load test | Nhân | | | | |
| E-37 | Calibration quality | Hùng/Dân | | | | |
| E-38 | CARLA scenario matrix | Dân/Hùng | | | | |
| E-39 | HMI usability (alert fatigue) | Thiện/Dân | | | | |
| E-40 | Copilot improves review time | Nhân/Thiện | | | | |
| E-41 | Multi-instance readiness | Nhân | | | | |
| E-42 | Model drift/domain gap | Tâm/Hùng | evidence/05_model_ablation/psi_ks_metrics.csv, domain_gap_report.md | 920cbac9585c14e1de05d10c6341d10b6f686ae7f000bd586adb52d9055f3c12 | 2026-08-09 | ✨ C1 done — PSI 0.83-8.56 (all "major shift") across luminance/density/box-scale between Data_train and Practice_Dataset; root-caused to 3 real training regressions (v3/v4/v5) |
| E-SCRIPT-01 | File renaming utility | Agent | evidence/scripts/rename_evidence.py | D4B46551D47BDDC8D70E4FC25DDF5BADFD1721753FD972BC084AB9BFECA36572 | 2026-08-09 | ✨ Verified |
| E-SCRIPT-02 | File redaction utility | Agent | evidence/scripts/redact_evidence.py | CBA8B8862272795B5695E27A6B8F2E1CB9EC20C99972E892F467F525DAE1E0E8 | 2026-08-09 | ✨ Verified |

## Supporting scripts & tickets
*Note: These are tools and task tracking files, not formal evidence claims.*
- `evidence/scripts/export_real_schema.py`
- `evidence/scripts/export_schema.py`
- `evidence/scripts/map_architecture.py`
- `evidence/scripts/run_eval_bundle.py`
- `evidence/commands.log`
- `evidence/tasks/Task_Dan.md`
- `evidence/tasks/Task_Hung_Tam.md`
- `evidence/tasks/Task_Nhan.md`
- `evidence/tasks/Task_Thien.md`
