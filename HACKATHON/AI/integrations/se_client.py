"""HTTP client for handing canonical DecisionEvents to the SE boundary."""
from __future__ import annotations

import math
import time
from typing import Any

import httpx

from core.decision_engine.schemas import DecisionEvent


class SEApiClient:
    """Small synchronous client intended for scripts and contract tests.

    Requests retry transient transport, rate-limit and server failures. Event
    retries remain safe because the SE boundary enforces idempotency keys.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        api_key: str | None = None,
        bearer_token: str | None = None,
        timeout_sec: float = 3.0,
        max_retries: int = 2,
        retry_backoff_sec: float = 0.15,
    ) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("SE endpoint must start with http:// or https://")
        self.endpoint = endpoint
        self.cabin_frame_endpoint = endpoint.rstrip("/") + "/cabin-frame"
        self.road_frame_endpoint = endpoint.rstrip("/") + "/road-frame"
        self.snapshot_endpoint = endpoint.rstrip("/") + "/snapshot"
        self.trips_endpoint = endpoint.rstrip("/") + "/trips"
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff_sec = max(0.0, float(retry_backoff_sec))
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        self._client = httpx.Client(
            headers=headers,
            timeout=httpx.Timeout(timeout_sec),
        )

    def _post_with_retry(self, url: str, **kwargs: Any) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.post(url, **kwargs)
            except httpx.TransportError:
                if attempt >= self.max_retries:
                    raise
            else:
                if response.status_code not in {408, 429} and response.status_code < 500:
                    return response
                if attempt >= self.max_retries:
                    return response
                response.close()
            time.sleep(self.retry_backoff_sec * (2**attempt))
        raise RuntimeError("Unreachable retry state")

    def send(self, event: DecisionEvent) -> dict[str, Any]:
        headers = {
            "Idempotency-Key": event.idempotency_key,
            "X-Event-ID": event.event_id,
        }
        response = self._post_with_retry(
            self.endpoint,
            json=event.transport_dict(),
            headers=headers,
        )
        response.raise_for_status()
        if not response.content:
            return {"status_code": response.status_code}
        payload = response.json()
        return payload if isinstance(payload, dict) else {"response": payload}

    def send_cabin_frame(
        self,
        jpeg: bytes,
        *,
        trip_id: str,
        frame_id: int,
        timestamp_ms: int,
    ) -> dict[str, Any]:
        response = self._post_with_retry(
            self.cabin_frame_endpoint,
            content=jpeg,
            headers={
                "Content-Type": "image/jpeg",
                "X-Trip-ID": trip_id,
                "X-Frame-ID": str(frame_id),
                "X-Timestamp-MS": str(timestamp_ms),
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"response": payload}

    def send_live_update(
        self,
        *,
        cabin_jpeg: bytes,
        road_jpeg: bytes,
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        trip_timestamp_ms = int(
            snapshot.get(
                "trip_timestamp_ms",
                snapshot.get("timestamp_ms", 0),
            )
        )
        headers = {
            "Content-Type": "image/jpeg",
            "X-Trip-ID": str(snapshot["trip_id"]),
            "X-Frame-ID": str(snapshot["frame_id"]),
            "X-Timestamp-MS": str(trip_timestamp_ms),
        }
        predicted_ttc = snapshot.get("predicted_ttc_sec")
        try:
            predicted_ttc = float(predicted_ttc)
        except (TypeError, ValueError):
            predicted_ttc = None
        if predicted_ttc is not None and not math.isfinite(predicted_ttc):
            predicted_ttc = None

        def float_field(name: str, default: float = 0.0) -> float:
            value = snapshot.get(name, default)
            if value is None:
                return float(default)
            try:
                number = float(value)
            except (TypeError, ValueError):
                return float(default)
            return number if math.isfinite(number) else float(default)

        def int_field(name: str, default: int = 0) -> int:
            value = snapshot.get(name, default)
            if value is None:
                return int(default)
            try:
                return int(value)
            except (TypeError, ValueError):
                return int(default)

        snapshot_payload = {
            "schema_version": "1.0",
            "trip_id": str(snapshot["trip_id"]),
            "frame_id": int(snapshot["frame_id"]),
            "trip_timestamp_ms": trip_timestamp_ms,
            "speed_kmh": float_field("speed_kmh", 0.0),
            "predicted_ttc_sec": predicted_ttc,
            "risk_score": float_field("risk_score", float_field("c3_risk_score", 0.0)),
            "driver_state": str(snapshot.get("driver_state", "alert")),
            "driver_confidence": float_field("driver_confidence", 0.0),
            "alertness_score": float_field("alertness_score", 1.0),
            "eye_state": str(snapshot.get("eye_state", "unknown")),
            "head_pose": str(snapshot.get("head_pose", "unknown")),
            "mouth_state": str(snapshot.get("mouth_state", "normal")),
            "longitudinal_accel": float_field("longitudinal_accel", 0.0),
            "lateral_accel": float_field("lateral_accel", 0.0),
            "speed_limit_kmh": float_field("speed_limit_kmh", 0.0),
            "safe_driving_score": float_field("safe_driving_score", float_field("c3_safe_score", 100.0)),
            "penalty_points": float_field("penalty_points", float_field("c3_penalty_points", 0.0)),
            "harsh_brake": bool(snapshot.get("harsh_brake", False)),
            "harsh_accel": bool(snapshot.get("harsh_accel", False)),
            "harsh_corner": bool(snapshot.get("harsh_corner", False)),
            "speeding": bool(snapshot.get("speeding", False)),
            "tailgating": bool(snapshot.get("tailgating", False)),
            "harsh_brake_count": int_field("harsh_brake_count", 0),
            "harsh_accel_count": int_field("harsh_accel_count", 0),
            "harsh_corner_count": int_field("harsh_corner_count", 0),
            "near_miss_count": int_field("near_miss_count", 0),
            "microsleep_count": int_field("microsleep_count", 0),
            "speeding_pct_time": float_field("speeding_pct_time", 0.0),
            "tailgating_pct_time": float_field("tailgating_pct_time", 0.0),
            "avg_headway_sec": float_field("avg_headway_sec", 0.0),
        }
        results: dict[str, Any] = {}
        errors: list[str] = []
        for name, url, jpeg in (
            ("cabin", self.cabin_frame_endpoint, cabin_jpeg),
            ("road", self.road_frame_endpoint, road_jpeg),
        ):
            try:
                response = self._post_with_retry(url, content=jpeg, headers=headers)
                response.raise_for_status()
                results[name] = response.json()
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        try:
            response = self._post_with_retry(
                self.snapshot_endpoint,
                json=snapshot_payload,
            )
            response.raise_for_status()
            results["snapshot"] = response.json()
        except Exception as exc:
            errors.append(f"snapshot: {exc}")
        if errors:
            raise RuntimeError("; ".join(errors))
        return results

    def register_trips(
        self,
        trips: list[dict[str, Any]],
        *,
        reset_existing: bool = False,
    ) -> dict[str, Any]:
        response = self._post_with_retry(
            self.trips_endpoint + "/register",
            json={"trips": trips, "reset_existing": reset_existing},
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"response": payload}

    def complete_trip(self, trip_id: str) -> dict[str, Any]:
        response = self._post_with_retry(
            self.trips_endpoint + f"/{trip_id}/complete"
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"response": payload}

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SEApiClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
