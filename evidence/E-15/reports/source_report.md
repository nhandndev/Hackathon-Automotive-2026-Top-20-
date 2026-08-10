# Source Report - E-15 Automated Test Traceability

| Evidence | Source | Ghi chú |
|---|---|---|
| `raw/be_pytest_all.log` | `SE/BE/tests` | Full Backend test run |
| `junit/be_pytest.xml` | `pytest --junitxml` | Machine-readable Backend JUnit |
| `raw/fe_lint.log` | `npm run lint` | TypeScript validation |
| `raw/fe_build.log` | `npm run build` | Production FE build + bundled Express server |
| `derived/hmi_apk_artifact.json` | `SE/HMI/release/dms-hmi-realtime-vhal.apk` | APK hash and size |
| `raw/hmi_apk_static_scan.log` | APK `classes.dex` strings | Confirms HMI runtime strings and CarProperty path exist in artifact |

## Kết quả

- Backend pytest passed: `True`.
- FE lint passed: `True`.
- FE production build passed: `True`.
- HMI APK artifact/static scan passed: `True`.

## Trạng thái

**DONE / BE TESTS, FE LINT-BUILD, HMI ARTIFACT VERIFIED**

## Caveat

`SE/HMI` has no Gradle wrapper in this checkout, so this evidence does not claim a clean local APK rebuild/test. It verifies the release APK artifact and runtime strings.
