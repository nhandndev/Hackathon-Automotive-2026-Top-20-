from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.integrations.carsky.client import CarSkyClient, CarSkyDeliveryError


class DeliveryKind(str, Enum):
    TELEMETRY = "telemetry"
    TRANSITION = "transition"


@dataclass(frozen=True)
class Delivery:
    payload: dict[str, Any]
    kind: DeliveryKind
    dedup_key: str


class CarSkyPublisher:
    """Non-blocking single-worker publisher with transition-safe queueing."""

    def __init__(self, client: CarSkyClient, *, queue_size: int = 100) -> None:
        self.client = client
        self.queue: asyncio.Queue[Delivery] = asyncio.Queue(maxsize=queue_size)
        self.worker: asyncio.Task[None] | None = None
        self.last_delivered_key: str | None = None
        self.delivery_status = "idle"
        self.last_error: str | None = None

    async def start(self) -> None:
        if self.worker is None:
            self.worker = asyncio.create_task(self._run(), name="carsky-publisher")

    async def stop(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            try:
                await self.worker
            except asyncio.CancelledError:
                pass
            self.worker = None
        await self.client.close()

    async def enqueue(
        self,
        payload: dict[str, Any],
        *,
        dedup_key: str,
        kind: DeliveryKind = DeliveryKind.TELEMETRY,
    ) -> bool:
        if dedup_key == self.last_delivered_key:
            return False
        delivery = Delivery(payload=payload, kind=kind, dedup_key=dedup_key)
        if not self.queue.full():
            self.queue.put_nowait(delivery)
            return True
        if kind is DeliveryKind.TELEMETRY:
            return False

        retained: list[Delivery] = []
        removed = False
        while not self.queue.empty():
            queued = self.queue.get_nowait()
            self.queue.task_done()
            if not removed and queued.kind is DeliveryKind.TELEMETRY:
                removed = True
                continue
            retained.append(queued)
        for queued in retained:
            self.queue.put_nowait(queued)
        if removed:
            self.queue.put_nowait(delivery)
            return True
        try:
            await asyncio.wait_for(self.queue.put(delivery), timeout=0.1)
            return True
        except TimeoutError:
            self.delivery_status = "degraded"
            self.last_error = "transition queue timeout"
            return False

    async def _run(self) -> None:
        while True:
            delivery = await self.queue.get()
            try:
                await self.client.actuate(delivery.payload)
                self.last_delivered_key = delivery.dedup_key
                self.delivery_status = "ready"
                self.last_error = None
            except CarSkyDeliveryError as exc:
                self.delivery_status = "degraded"
                self.last_error = str(exc)
            finally:
                self.queue.task_done()
