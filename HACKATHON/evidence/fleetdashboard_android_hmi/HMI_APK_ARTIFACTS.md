# HMI / APK / Relay Artifacts

| Artifact | Exists | SHA-256 | Bytes |
|---|---:|---|---:|
| `SE/HMI/release/dms-hmi-realtime-vhal.apk` | yes | `51a44e1570551c16abc83db7fa9f167f3ae40a62cd1b57bde5dc465adb91cbb0` | 16811 |
| `SE/HMI/release/adb_install_realtime_hmi.txt` | yes | `3d51727c05308a34e083b4d58ec7d229b90e47d7e6adf02b1d079d3550efa7b2` | 22985 |
| `SE/HMI/release/install_hmi_realtime_adb.sh` | yes | `3d51727c05308a34e083b4d58ec7d229b90e47d7e6adf02b1d079d3550efa7b2` | 22985 |
| `SE/HMI/app/build/outputs/apk/debug/app-debug.apk` | yes | `51a44e1570551c16abc83db7fa9f167f3ae40a62cd1b57bde5dc465adb91cbb0` | 16811 |
| `SE/HMI/vhal-vsock-relay/target/aarch64-linux-android/release/vhal-vsock-relay` | no |  |  |
| `SE/HMI/vhal-vsock-relay/vhal-vsock-relay` | no |  |  |

## APK-derived static evidence

This section is extracted from the APK artifact itself, not only from source files.

APK: `SE/HMI/release/dms-hmi-realtime-vhal.apk`
APK SHA-256: `51a44e1570551c16abc83db7fa9f167f3ae40a62cd1b57bde5dc465adb91cbb0`
APK bytes: `16811`

### ZIP entries

| Entry | Bytes | Compressed |
|---|---:|---:|
| `AndroidManifest.xml` | 2608 | 936 |
| `resources.arsc` | 604 | 604 |
| `classes.dex` | 16412 | 8652 |
| `META-INF/ANDROIDD.SF` | 412 | 298 |
| `META-INF/ANDROIDD.RSA` | 1167 | 1014 |
| `META-INF/MANIFEST.MF` | 285 | 218 |

### APK signing metadata

```text
Signature-Version: 1.0
Created-By: 1.0 (Android)
SHA-256-Digest-Manifest: Wh9jG/9FtQmTUN9GPp4AFDz0kP/0pTx8xKtIIbQHXVQ=
X-Android-APK-Signed: 2, 3

Name: AndroidManifest.xml
SHA-256-Digest: N5NW6naEwJr9IStTCHUTlcqZbD1Hx6JA9HEFq9AB3RA=

Name: classes.dex
SHA-256-Digest: 3Bw60lnK+5/ACNrhCchRroAawT80oie/lWXuBkeofhY=

Name: resources.arsc
SHA-256-Digest: npWKiiHz1XDoT7z60KdKZQ/9+NYeaVskrewxnlYiZDo=

```

### DEX strings relevant to HMI runtime

- `DMS_HMI`: found in `classes.dex`
- `vn/fpt/dms/hmi/MainActivity`: found in `classes.dex`
- `PERF_VEHICLE_SPEED`: found in `classes.dex`
- `CarPropertyManager`: found in `classes.dex`
- `Registered DMS VHAL transport`: found in `classes.dex`
- `mux decimal raw`: not found in `classes.dex`
- `mux raw`: found in `classes.dex`
- `mux speed`: found in `classes.dex`
- `V2.2 SPEED MUX`: not found in `classes.dex`
- `V2.1 CUSTOM VHAL`: found in `classes.dex`
- `SAFE`: found in `classes.dex`
- `CRITICAL`: found in `classes.dex`
- `TTC`: found in `classes.dex`
- `km/h`: found in `classes.dex`

### APK/source version consistency

- Source `BUILD_TAG`: `V2.2 SPEED MUX`
- APK `classes.dex` tag: `V2.1 CUSTOM VHAL`
- Result: `MISMATCH`; rebuild and reinstall APK before claiming the source version is deployed.

