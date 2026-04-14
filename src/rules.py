from __future__ import annotations

import logging
from datetime import date

from src.models import IPOSubscription

logger = logging.getLogger(__name__)


def apply_filters(ipos: list[IPOSubscription], config: dict) -> list[IPOSubscription]:
    """Apply all configured filters and return only the IPOs that pass."""
    filters = config.get("filters", {})
    alert_rules = config.get("alert_rules", {})

    filtered = ipos

    if filters.get("ipo_type", "").lower() == "mainboard":
        before = len(filtered)
        filtered = [ipo for ipo in filtered if ipo.is_mainboard]
        logger.info("Mainboard filter: %d -> %d IPOs", before, len(filtered))

    if filters.get("only_last_day", True):
        today = date.today()
        before = len(filtered)
        filtered = [ipo for ipo in filtered if ipo.close_date == today]
        logger.info(
            "Last-day filter (today=%s): %d -> %d IPOs",
            today.isoformat(), before, len(filtered),
        )

    min_total = alert_rules.get("min_total_subscription", 0)
    if min_total > 0:
        before = len(filtered)
        filtered = [ipo for ipo in filtered if ipo.total_subscription >= min_total]
        logger.info("Total subscription >= %.1fx: %d -> %d IPOs", min_total, before, len(filtered))

    min_qib = alert_rules.get("min_qib_subscription", 0)
    if min_qib > 0:
        before = len(filtered)
        filtered = [ipo for ipo in filtered if ipo.qib_subscription >= min_qib]
        logger.info("QIB subscription >= %.1fx: %d -> %d IPOs", min_qib, before, len(filtered))

    min_retail = alert_rules.get("min_retail_subscription", 0)
    if min_retail > 0:
        before = len(filtered)
        filtered = [ipo for ipo in filtered if ipo.retail_subscription >= min_retail]
        logger.info("Retail subscription >= %.1fx: %d -> %d IPOs", min_retail, before, len(filtered))

    return filtered
