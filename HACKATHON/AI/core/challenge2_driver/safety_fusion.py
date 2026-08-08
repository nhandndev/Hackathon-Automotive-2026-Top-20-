def should_force_microsleep(dms_output: dict, microsleep_min_ms: int) -> bool:
    """Determine if a microsleep state should be forced based on raw DMS output."""
    observation = dms_output.get("observation", {})
    features = dms_output.get("features", {})

    reliable = bool(
        observation.get("face_detected")
        and observation.get("left_eye_valid")
        and observation.get("right_eye_valid")
        and observation.get("monitoring_available")
        and observation.get("quality_status") not in {"face_missing", "invalid", "calibrating"}
    )

    closure_ms = max(0, int(features.get("continuous_eye_closure_ms", 0) or 0))

    return reliable and closure_ms >= int(microsleep_min_ms)
