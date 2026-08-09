# VHAL VSOCK Relay Hotfix

Temporary BTC hotfix for AAOS images that connect to fake VHAL at
`vsock:1:9210` while the CarSky DMS HMI Bridge exposes VHAL at `vsock:2:9300`.

The relay runs inside the Android guest:

```text
listen vsock:1:9210 -> connect vsock:2:9300
```

Build:

```bash
./SE/HMI/vhal-vsock-relay/build_android_relay.sh
```

Copy Android-shell init commands to clipboard:

```bash
./SE/HMI/vhal-vsock-relay/copy_relay_init_to_clipboard.sh
```

After deployment:

1. Paste the copied commands into the CarSky Android terminal / adb shell flow
   where the prompt looks like `trout_arm64:/ #` or `trout_arm64:/ $`.
2. Restart VHAL client and Car Service using the copied commands.
3. Send a DMS scenario from backend:

```bash
cd SE/BE
.venv/bin/python scripts/carsky_phase05.py scenario critical
```

Expected confirmation:

```text
Bridge: DMS_HMI_DUAL ... mux 0x11600207=41.088
Android logcat: DMS_HMI ... raw=41.088
APK: CRITICAL / risk 88
```

This hotfix is temporary. It must be re-applied when the Android VM/pod is
recreated.
