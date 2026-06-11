from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

def start():
    from core.predictor import predict_today

    scheduler = BackgroundScheduler(timezone=IST)

    scheduler.add_job(
        func=predict_today,
        trigger=CronTrigger(hour=12, minute=0, timezone=IST),
        id="noon_pred",
        replace_existing=True,
        misfire_grace_time=3600
    )

    scheduler.start()
    logger.info("Scheduler started - predictions run daily at 12:00 PM IST")
    return scheduler