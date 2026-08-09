#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$SCRIPT_DIR/build"
OUT="$OUT_DIR/vhal-vsock-relay"
API="${ANDROID_API:-30}"

find_clang() {
  if [[ -n "${ANDROID_NDK_HOME:-}" && -x "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/aarch64-linux-android${API}-clang" ]]; then
    echo "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/aarch64-linux-android${API}-clang"
    return
  fi

  local sdk="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
  local ndk_dir
  ndk_dir="$(ls -d "$sdk"/ndk/* 2>/dev/null | sort -V | tail -1 || true)"
  if [[ -n "$ndk_dir" && -x "$ndk_dir/toolchains/llvm/prebuilt/darwin-x86_64/bin/aarch64-linux-android${API}-clang" ]]; then
    echo "$ndk_dir/toolchains/llvm/prebuilt/darwin-x86_64/bin/aarch64-linux-android${API}-clang"
    return
  fi

  if command -v "aarch64-linux-android${API}-clang" >/dev/null 2>&1; then
    command -v "aarch64-linux-android${API}-clang"
    return
  fi

  echo ""
}

CLANG="$(find_clang)"
if [[ -z "$CLANG" ]]; then
  cat >&2 <<MSG
Android NDK clang not found.

Install/set one of these, then rerun:
  export ANDROID_NDK_HOME=/path/to/android-sdk/ndk/<version>
  export ANDROID_HOME=$HOME/Library/Android/sdk

Expected compiler:
  aarch64-linux-android${API}-clang
MSG
  exit 1
fi

mkdir -p "$OUT_DIR"
"$CLANG" -O2 -Wall -Wextra -D_GNU_SOURCE "$SCRIPT_DIR/vhal-vsock-relay.c" -o "$OUT" -pthread
file "$OUT"
ls -lh "$OUT"

