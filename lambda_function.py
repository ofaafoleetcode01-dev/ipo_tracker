from __future__ import annotations

import json
import logging

logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ipo_tracker")

from src.main import IPOTrackerMain
from src.models import IPOTrackerMainInput

def handler(event, context):
    """AWS Lambda entry point. Triggered by EventBridge on a daily schedule."""
    logger.info("Lambda invoked. Event: %s", json.dumps(event))
    args = IPOTrackerMainInput()
    args.morning = event.get("morning", "").lower() == "true"
    args.dry_run = event.get("dry_run", "").lower() == "true"
    args.debug = event.get("debug", "").lower() == "true"
    args.skip_date_filter = event.get("skip_date_filter", "").lower() == "true"
    return IPOTrackerMain().main(args)
