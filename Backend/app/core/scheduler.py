from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()
daily_midnight_trigger = CronTrigger(hour=0, minute=0)  # Run every day at midnight
