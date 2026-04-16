from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

import yaml

from src.models import IPOAlertMessage, IPOSubscription, IPOTrackerMainInput
from src.ipo_scrapers.ipo_scrapers import get_scraper
from src.telegram_bot import TelegramBot

logger = logging.getLogger("ipo_tracker")

class IPOTrackerMain(object):
    _DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"

    def _load_config(self, path: Path) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    def _apply_filters(self, ipos: list[IPOSubscription], config: dict) -> list[IPOSubscription]:
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

    def main(self, args: IPOTrackerMainInput) -> None:
        log_level = "DEBUG" if not args.debug else "INFO"
        logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
        logger.info(f"Received args: {args}")

        config = self._load_config(self._DEFAULT_CONFIG)
        scraper = get_scraper(config)
        telegram_bot = TelegramBot(config)
        today = date.today()    # TODO: Has timezone issues

        all_ipos: list[IPOSubscription] = scraper.scrape_ipos()
        matched = self._apply_filters(all_ipos, config)   # Keeping this for now
        closing_today = [ipo for ipo in all_ipos if ipo.close_date == today]

        if not all_ipos:
            logger.info("No IPOs found. Nothing to do.")
            return
        
        alert = IPOAlertMessage(ipos=all_ipos)

        if args.dry_run:
            print("\n--- DRY RUN: message that would be sent ---")
            print(alert.format(is_morning = args.morning))
            print("---")
            return
        else:
            telegram_bot.send_telegram_message(alert.format(is_morning = args.morning))
            print("Telegram notification sent!")
        

def setup_parser():
        parser = argparse.ArgumentParser(description="Indian IPO Subscription Tracker Bot")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Scrape and filter but print message instead of sending via Telegram",
        )
        parser.add_argument(
            "--skip-date-filter",
            action="store_true",
            help="Ignore the 'only_last_day' filter (useful for testing)",
        )
        parser.add_argument(
            "--morning",
            action="store_true",
            help="Run the morning check (heads-up about today's closing IPOs)",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging",
        )
        return parser

if __name__ == "__main__":
    parser = setup_parser()
    args = IPOTrackerMainInput().build_from_args(vars(parser.parse_args()))
    IPOTrackerMain().main(args)
