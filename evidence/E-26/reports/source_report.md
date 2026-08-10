# Source Report - E-26 Clean-room Build/Run

| Evidence | Source | Ghi chú |
|---|---|---|
| `raw/docker_info.log` | Docker CLI | Checks whether container clean-room is available |
| `raw/git_archive_extract.log` | `git archive HEAD` | Creates source-only clean archive from commit, excluding dirty/untracked files |
| `raw/clean_room_check_*.log` | Commands inside clean archive | Static compile/file-presence checks |
| `derived/environment.lock.json` | Host tool versions + command results | Environment lock for reviewer |

## Kết quả

- Docker daemon available: `False`.
- Source archive extracted: `True`.
- Python source compile check passed: `True`.

## Trạng thái

**PARTIAL / CLEAN SOURCE ARCHIVE AND STATIC COMPILE CHECK CREATED; FULL CLEAN-ROOM BUILD NOT EXECUTED**

## Caveat

This is not a full clean-room dependency reinstall/build. Docker daemon was not available, and no fresh `pip install` / `npm ci` / HMI Gradle build was completed in a new container. Treat this as partial reproducibility evidence only.
