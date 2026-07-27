from __future__ import annotations

import asyncio
from typing import Any

import httpx


class CarSkyDeliveryError(RuntimeError):
    """A bounded CarSky delivery failed and may be reported as degraded."""


class CarSkyClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        room_id: str,
        node_key: str,
        auth_mode: str = "bearer",
        timeout_sec: float = 1.5,
        max_retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if auth_mode not in {"bearer", "x-api-key"}:
            raise ValueError("auth_mode must be 'bearer' or 'x-api-key'")
        self.base_url = base_url.rstrip("/")
        self.room_id = room_id
        self.node_key = node_key
        self.max_retries = max_retries
        header = "Authorization" if auth_mode == "bearer" else "X-API-Key"
        value = f"Bearer {api_key}" if auth_mode == "bearer" else api_key
        self._client = httpx.AsyncClient(
            timeout=timeout_sec,
            transport=transport,
            headers={header: value, "Accept": "application/json"},
        )

    @property
    def signal_url(self) -> str:
        return f"{self.base_url}/api/v1/signals/{self.room_id}/{self.node_key}"

    async def close(self) -> None:
        await self._client.aclose()

    async def list_signals(self) -> Any:
        response = await self._client.get(self.signal_url)
        response.raise_for_status()
        return response.json()

    async def actuate(self, payload: dict[str, Any]) -> Any:
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                response = await self._client.post(f"{self.signal_url}/actuate", json=payload)
                if response.status_code < 400:
                    return response.json() if response.content else None
                if response.status_code < 500 and response.status_code != 429:
                    raise CarSkyDeliveryError(
                        f"CarSky rejected payload with status {response.status_code}"
                    )
                response.raise_for_status()
            except CarSkyDeliveryError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                if attempt == attempts - 1:
                    raise CarSkyDeliveryError("CarSky delivery failed after bounded retries") from exc
                await asyncio.sleep(0.25 * (2**attempt))
        raise CarSkyDeliveryError("CarSky delivery failed")
