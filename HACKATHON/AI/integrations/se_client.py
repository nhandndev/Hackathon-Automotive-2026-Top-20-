"""HTTP client for handing canonical DecisionEvents to the SE boundary."""
from __future__ import annotations

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
        headers = {
            "Content-Type": "image/jpeg",
            "X-Trip-ID": str(snapshot["trip_id"]),
            "X-Frame-ID": str(snapshot["frame_id"]),
            "X-Timestamp-MS": str(snapshot["trip_timestamp_ms"]),
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
            response = self._post_with_retry(self.snapshot_endpoint, json=snapshot)
            response.raise_for_status()
            results["snapshot"] = response.json()
        except Exception as exc:
            errors.append(f"snapshot: {exc}")
        if errors:
            raise RuntimeError("; ".join(errors))
        return results

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SEApiClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
