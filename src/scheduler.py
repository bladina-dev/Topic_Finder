"""Scheduler — automated daily pipeline runs via APScheduler."""

from __future__ import annotations

import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .pipeline import run_pipeline


async def scheduled_run():
    """Scheduled pipeline execution."""
    print(f"\n[Scheduler] Running scheduled pipeline at {datetime.now().isoformat()}")
    try:
        output = await run_pipeline(mock=False)
        print(
            f"[Scheduler] Done: {output.trend_count} trends, "
            f"{output.angle_count} angles, {len(output.errors)} errors"
        )
    except Exception as e:
        print(f"[Scheduler] Pipeline failed: {e}")


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the scheduler.

    Runs the pipeline daily at the configured time (default: 6:00 PM).
    """
    scheduler = AsyncIOScheduler()

    trigger = CronTrigger(
        hour=settings.agent_schedule_hour,
        minute=settings.agent_schedule_minute,
        timezone=settings.agent_timezone,
    )

    scheduler.add_job(
        scheduled_run,
        trigger=trigger,
        id="daily_pipeline",
        name="Daily Marketing Agent Pipeline",
        replace_existing=True,
    )

    return scheduler


def start_scheduler():
    """Start the scheduler in the current event loop."""
    scheduler = create_scheduler()
    scheduler.start()

    print(
        f"[Scheduler] Started. Pipeline will run daily at "
        f"{settings.agent_schedule_hour:02d}:{settings.agent_schedule_minute:02d} "
        f"({settings.agent_timezone})"
    )

    return scheduler
