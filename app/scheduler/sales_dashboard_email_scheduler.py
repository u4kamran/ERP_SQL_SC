"""Background scheduler for sales dashboard email snapshots."""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timedelta

from app.logging.logger import logger
from app.services.sales_dashboard_email_service import SalesDashboardEmailService
from app.services.sales_dashboard_email_store import get_config, update_runtime


class SalesDashboardEmailSchedulerRunner:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self._service = SalesDashboardEmailService()

    @property
    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.is_running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="sales-dashboard-email-scheduler")
        logger.info("Sales dashboard email scheduler started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Sales dashboard email scheduler stopped")

    async def _loop(self) -> None:
        await asyncio.sleep(10)
        while self._running:
            config = get_config()
            interval_seconds = max(config.interval_minutes, 15) * 60

            try:
                result = await asyncio.to_thread(self._service.run_check)
                logger.info("Sales dashboard email check: %s", result.message)
            except Exception:
                logger.exception("Sales dashboard email check failed")

            interval_seconds = max(get_config().interval_minutes, 15) * 60
            update_runtime(next_check_at=datetime.now() + timedelta(seconds=interval_seconds))

            slept = 0
            while self._running and slept < interval_seconds:
                chunk = min(15, interval_seconds - slept)
                await asyncio.sleep(chunk)
                slept += chunk
                new_interval = max(get_config().interval_minutes, 15) * 60
                if new_interval != interval_seconds:
                    interval_seconds = new_interval
                    break


_runner: SalesDashboardEmailSchedulerRunner | None = None
_lock = threading.Lock()


def get_sales_dashboard_email_runner() -> SalesDashboardEmailSchedulerRunner:
    global _runner
    with _lock:
        if _runner is None:
            _runner = SalesDashboardEmailSchedulerRunner()
        return _runner
