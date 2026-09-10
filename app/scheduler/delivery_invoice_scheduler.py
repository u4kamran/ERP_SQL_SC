"""Small in-process poller that imports recent eligible ERP invoices."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from functools import lru_cache

from app.database.business_session import BusinessSessionLocal
from app.logging.logger import logger
from app.services.delivery_service import DeliveryService


class DeliveryInvoiceScheduler:
    def __init__(self, interval_seconds: int = 120):
        self.interval_seconds = max(interval_seconds, 10)
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()
        self._reported_unavailable = False

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopping.clear()
        self._task = asyncio.create_task(self._run(), name="delivery-invoice-sync")

    async def stop(self) -> None:
        self._stopping.set()
        if not self._task:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run(self) -> None:
        await asyncio.sleep(5)
        while not self._stopping.is_set():
            try:
                created = await asyncio.to_thread(self._sync_once)
                if created:
                    logger.info("Delivery scheduler imported %s invoice(s).", created)
                self._reported_unavailable = False
            except Exception as exc:
                if not self._reported_unavailable:
                    logger.warning(
                        "Delivery invoice sync is unavailable; run the delivery setup script: %s",
                        exc,
                    )
                    self._reported_unavailable = True
            try:
                await asyncio.wait_for(
                    self._stopping.wait(),
                    timeout=self.interval_seconds,
                )
            except asyncio.TimeoutError:
                pass

    @staticmethod
    def _sync_once() -> int:
        db = BusinessSessionLocal()
        try:
            result = DeliveryService(db).sync(
                lookback_hours=6,
                limit=80,
                actor_username="SYSTEM",
            )
            return result.created
        finally:
            db.close()


@lru_cache
def get_delivery_invoice_scheduler() -> DeliveryInvoiceScheduler:
    return DeliveryInvoiceScheduler()
