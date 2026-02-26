import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import run_scrape

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()


def start():
    interval = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
    _scheduler.add_job(run_scrape, "interval", hours=interval, id="scrape_job", replace_existing=True)
    _scheduler.start()
    logger.info("Scheduler started — scraping every %d hours", interval)


def shutdown():
    _scheduler.shutdown(wait=False)
