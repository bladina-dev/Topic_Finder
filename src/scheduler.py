"""Scheduler — automated pipeline runs via APScheduler."""

from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .pipeline import run_pipeline
from .telegram_bot import send_message

logger = logging.getLogger(__name__)


async def scheduled_run() -> None:
    """Execute the pipeline on schedule. Sends Telegram alert on failure."""
    logger.info("Scheduled pipeline starting at %s", datetime.now().isoformat())
    try:
        output = await run_pipeline(mock=False)
        logger.info(
            "Scheduled pipeline done: %d trends, %d angles, %d errors",
            output.trend_count,
            output.angle_count,
            len(output.errors),
        )
    except Exception as e:
        logger.exception("Scheduled pipeline failed: %s", e)
        try:
            await send_message(
                f"❌ *Topic Finder pipeline failed*\n\n"
                f"`{type(e).__name__}: {e}`\n\n"
                f"Check GitHub Actions logs for details."
            )
        except Exception as alert_err:
            logger.error("Failed to send failure alert to Telegram: %s", alert_err)


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler instance."""
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(
        hour=settings.agent_schedule_hour,
        minute=settings.agent_schedule_minute,
        timezone=settings.agent_timezone,
    )
    scheduler.add_job(
        scheduled_run,
        trigger=trigger,
        id="pipeline",
        name="Marketing Agent Pipeline",
        replace_existing=True,
    )
    return scheduler


def start_scheduler() -> AsyncIOScheduler:
    """Start the scheduler in the current event loop."""
    scheduler = create_scheduler()
    scheduler.start()
    logger.info(
        "Scheduler started — pipeline runs daily at %02d:%02d (%s)",
        settings.agent_schedule_hour,
        settings.agent_schedule_minute,
        settings.agent_timezone,
    )
    return scheduler
