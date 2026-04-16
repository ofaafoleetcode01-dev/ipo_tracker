from __future__ import annotations

import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("ipo_tracker")

from src.main import IPOTrackerMain
from src.models import IPOTrackerMainInput

def handler(event, context):
    """AWS Lambda entry point. Triggered by EventBridge on a daily schedule."""
    logger.info("Lambda invoked. Event: %s", json.dumps(event))
    args = IPOTrackerMainInput()
    args.morning = bool(event.get("morning", False))
    args.dry_run = bool(event.get("dry_run", False))
    return IPOTrackerMain().main(args)
