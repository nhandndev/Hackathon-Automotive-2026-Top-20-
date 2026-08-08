FINAL_LABELS = (
    "alert",
    "drowsy",
    "yawning",
    "distracted",
    "microsleep",
)

FATIGUE_LABELS = (
    "alert",
    "drowsy",
    "yawning",
    "microsleep",
)

DISTRACTION_LABELS = (
    "not_distracted",
    "distracted",
)

ALIASES = {
    "unknown": "alert",
    "awake": "alert",
    "normal": "alert",
    "drowsiness": "drowsy",
    "yawn": "yawning",
    "distraction": "distracted",
    "micro_sleep": "microsleep",
    "micro-sleep": "microsleep",
}


def normalize_driver_state(
    label,
) -> str:

    if label is None:
        raw = "unknown"
    else:
        raw = (
            str(label)
            .strip()
            .lower()
        )

    if raw == "":
        raw = "unknown"

    value = ALIASES.get(
        raw,
        raw,
    )

    if value not in FINAL_LABELS:
        raise ValueError(
            f"Unsupported state: {label!r}"
        )

    return value
