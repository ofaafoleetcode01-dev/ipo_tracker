from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

from src.models import AlertMessage
from src.notifier import send_telegram
from src.rules import apply_filters
from src.scraper import scrape_ipos

logger = logging.getLogger("ipo_tracker")

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, stream=sys.stdout)


def _load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run(config: dict, dry_run: bool = False) -> None:
    logger.info("Scraping mainboard IPO subscription data from chittorgarh.com ...")
    all_ipos = scrape_ipos(config)

    if not all_ipos:
        logger.info("No IPOs found. Nothing to do.")
        return

    logger.info("Found %d mainboard IPOs total. Applying filters ...", len(all_ipos))
    matched = apply_filters(all_ipos, config)

    if not matched:
        logger.info("No IPOs matched the alert rules. No notification sent.")
        return

    logger.info("%d IPO(s) matched alert rules:", len(matched))
    for ipo in matched:
        logger.info("  %s — Total: %.2fx", ipo.name, ipo.total_subscription)

    alert = AlertMessage(ipos=matched)

    if dry_run:
        print("\n--- DRY RUN: message that would be sent ---")
        print(alert.format())
        print("---")
        return

    send_telegram(alert, config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Indian IPO Subscription Tracker Bot")
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        help="Path to config.yaml (default: %(default)s)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
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
    args = parser.parse_args()

    _setup_logging(args.verbose)

    config = _load_config(args.config)

    if args.skip_date_filter:
        config.setdefault("filters", {})["only_last_day"] = False

    run(config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
