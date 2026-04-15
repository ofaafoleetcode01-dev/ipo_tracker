from __future__ import annotations

import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("ipo_tracker")

from src.main import IPOTrackerMain

def handler(event, context):
    """AWS Lambda entry point. Triggered by EventBridge on a daily schedule."""
    logger.info("Lambda invoked. Event: %s", json.dumps(event))
    return IPOTrackerMain().main()
