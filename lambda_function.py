from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("ipo_tracker")

from src.main import morning_check, run  # noqa: E402


def _build_config() -> dict:
    return {
        "scraper": {
            "base_url": os.environ.get("SCRAPER_BASE_URL", "https://www.chittorgarh.com"),
            "year": date.today().year,
        },
        "filters": {
            "ipo_type": "mainboard",
            "only_last_day": True,
        },
        "alert_rules": {
            "min_total_subscription": float(os.environ.get("MIN_TOTAL_SUBSCRIPTION", "1.0")),
            "min_qib_subscription": float(os.environ.get("MIN_QIB_SUBSCRIPTION", "0")),
            "min_retail_subscription": float(os.environ.get("MIN_RETAIL_SUBSCRIPTION", "0")),
        },
        "telegram": {
            "bot_token": os.environ["TELEGRAM_BOT_TOKEN"],
            "chat_id": os.environ["TELEGRAM_CHAT_ID"],
        },
    }


def handler(event, context):
    """AWS Lambda entry point. Triggered by EventBridge on a daily schedule."""
    logger.info("Lambda invoked. Event: %s", json.dumps(event))

    try:
        config = _build_config()

        mode = event.get("mode", "report")
        if mode == "morning":
            morning_check(config)
        else:
            run(config)

        return {"statusCode": 200, "body": f"{mode} completed"}
    except Exception:
        logger.exception("Unhandled error in IPO tracker")
        raise
