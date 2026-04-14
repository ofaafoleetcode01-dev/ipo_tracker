from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from src.models import IPOSubscription

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}

_DATE_RANGE_RE = re.compile(r"(\d{2})\s*-\s*(\d{2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)")
_DATE_RANGE_CROSS_MONTH_RE = re.compile(
    r"(\d{2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s*-\s*"
    r"(\d{2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
)


def _get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def _parse_close_date_from_badge(badge_text: str, year: int) -> Optional[date]:
    """Parse close date from dashboard badge like '09 - 13 Apr' or '27 Mar - 08 Apr'."""
    m = _DATE_RANGE_CROSS_MONTH_RE.search(badge_text)
    if m:
        close_day = int(m.group(3))
        close_month = m.group(4)
        dt = datetime.strptime(f"{close_day} {close_month} {year}", "%d %b %Y")
        return dt.date()

    m = _DATE_RANGE_RE.search(badge_text)
    if m:
        close_day = int(m.group(2))
        month = m.group(3)
        dt = datetime.strptime(f"{close_day} {month} {year}", "%d %b %Y")
        return dt.date()

    return None


def _parse_float(text: str) -> float:
    """Parse a float from text like '13.0415' or '-'."""
    cleaned = text.strip().replace(",", "")
    if not cleaned or cleaned == "-":
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _extract_slug_and_id(href: str) -> tuple[str, str]:
    """Extract slug and numeric id from '/ipo/<slug>/<id>/'."""
    parts = [p for p in href.strip("/").split("/") if p]
    if len(parts) >= 3:
        return parts[-2], parts[-1]
    return "", ""


def fetch_mainboard_ipos(base_url: str, year: int) -> list[dict]:
    """Fetch the list of mainboard IPOs from the dashboard.

    The dashboard server-renders up to 20 IPOs in Table 0.
    This will always include any IPO closing today or in the near future.

    Returns a list of dicts with keys: name, slug, ipo_id, close_date, detail_url.
    """
    url = f"{base_url}/ipo/ipo_dashboard.asp"
    soup = _get_soup(url)

    tables = soup.find_all("table")
    if not tables:
        logger.warning("No tables found on dashboard page")
        return []

    ipo_table = tables[0]
    tbody = ipo_table.find("tbody")
    if not tbody:
        return []

    results = []
    for row in tbody.find_all("tr"):
        link = row.find("a", href=lambda h: h and "/ipo/" in h)
        if not link:
            continue

        href = link.get("href", "")
        slug, ipo_id = _extract_slug_and_id(href)
        if not slug or not ipo_id:
            continue

        name = link.get_text(strip=True)

        spans = row.find_all("span")
        close_date = None
        for span in spans:
            span_text = span.get_text(strip=True)
            close_date = _parse_close_date_from_badge(span_text, year)
            if close_date:
                break

        results.append({
            "name": name,
            "slug": slug,
            "ipo_id": ipo_id,
            "close_date": close_date,
            "detail_url": urljoin(base_url, href),
        })

    logger.info("Found %d mainboard IPOs on dashboard", len(results))
    return results


def fetch_subscription_details(base_url: str, slug: str, ipo_id: str) -> dict:
    """Fetch subscription details from an individual IPO subscription page.

    Returns a dict with subscription multipliers and the close date from the page.
    """
    url = f"{base_url}/ipo_subscription/{slug}/{ipo_id}/"
    logger.info("Fetching subscription details: %s", url)
    soup = _get_soup(url)
    tables = soup.find_all("table")

    result: dict = {
        "qib": 0.0,
        "nii": 0.0,
        "snii": 0.0,
        "bnii": 0.0,
        "retail": 0.0,
        "employee": 0.0,
        "total": 0.0,
        "close_date": None,
        "issue_size_cr": None,
    }

    for table in tables:
        thead = table.find("thead")
        if not thead:
            continue
        header_texts = [th.get_text(strip=True).lower() for th in thead.find_all("th")]

        if "subscription (times)" in header_texts or "subscription(times)" in " ".join(header_texts):
            _parse_subscription_table(table, result)
        elif "investor category" in header_texts and "subscription" in " ".join(header_texts):
            _parse_subscription_table(table, result)

    _parse_dates_table(tables, result)
    _parse_detailed_subscription(tables, result)

    return result


def _parse_subscription_table(table: Tag, result: dict) -> None:
    """Parse the simple subscription summary table (Table 4 pattern)."""
    tbody = table.find("tbody")
    if not tbody:
        return

    for row in tbody.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        category = tds[0].get_text(strip=True).lower()
        value = _parse_float(tds[1].get_text(strip=True))

        if "qualified" in category or category.startswith("qib"):
            result["qib"] = value
        elif "non institutional" in category or "nii" in category:
            result["nii"] = value
        elif "retail" in category:
            result["retail"] = value
        elif "employee" in category:
            result["employee"] = value
        elif "total" in category:
            result["total"] = value


def _parse_detailed_subscription(tables: list[Tag], result: dict) -> None:
    """Parse the detailed breakdown table (Table 0 pattern) for sNII/bNII split."""
    for table in tables:
        thead = table.find("thead")
        if not thead:
            continue
        headers = [th.get_text(strip=True) for th in thead.find_all("th")]
        header_lower = [h.lower() for h in headers]

        if "below ₹10l" not in " ".join(header_lower) and "above ₹10l" not in " ".join(header_lower):
            continue

        snii_idx = None
        bnii_idx = None
        for i, h in enumerate(header_lower):
            if "below" in h and "10l" in h:
                snii_idx = i
            elif "above" in h and "10l" in h:
                bnii_idx = i

        tbody = table.find("tbody")
        if not tbody:
            continue

        for row in tbody.find_all("tr"):
            tds = row.find_all("td")
            first_cell = tds[0].get_text(strip=True).lower() if tds else ""
            if "subscription" not in first_cell and "times" not in first_cell:
                continue

            if snii_idx is not None and snii_idx < len(tds):
                result["snii"] = _parse_float(tds[snii_idx].get_text(strip=True))
            if bnii_idx is not None and bnii_idx < len(tds):
                result["bnii"] = _parse_float(tds[bnii_idx].get_text(strip=True))
            break


def _parse_dates_table(tables: list[Tag], result: dict) -> None:
    """Parse the IPO timeline table (Table 5 pattern) for close date."""
    for table in tables:
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
            label = tds[0].get_text(strip=True).lower()
            if "close" in label:
                date_text = tds[1].get_text(strip=True)
                for fmt in ["%A, %B %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"]:
                    try:
                        result["close_date"] = datetime.strptime(date_text, fmt).date()
                        return
                    except ValueError:
                        continue


def scrape_ipos(config: dict) -> list[IPOSubscription]:
    """Main scraping entry point. Returns a list of IPOSubscription objects."""
    base_url = config["scraper"]["base_url"]
    year = config["scraper"]["year"]

    ipos_meta = fetch_mainboard_ipos(base_url, year)
    if not ipos_meta:
        logger.warning("No mainboard IPOs found")
        return []

    results = []
    for meta in ipos_meta:
        try:
            details = fetch_subscription_details(base_url, meta["slug"], meta["ipo_id"])
        except Exception:
            logger.exception("Failed to fetch subscription for %s", meta["name"])
            continue

        close_date = details.get("close_date") or meta.get("close_date")
        if close_date is None:
            logger.warning("No close date found for %s, skipping", meta["name"])
            continue

        ipo = IPOSubscription(
            name=meta["name"],
            close_date=close_date,
            ipo_type="mainboard",
            issue_size_cr=details.get("issue_size_cr"),
            qib_subscription=details["qib"],
            snii_subscription=details["snii"],
            bnii_subscription=details["bnii"],
            retail_subscription=details["retail"],
            employee_subscription=details["employee"],
            total_subscription=details["total"],
            detail_url=f"{base_url}/ipo_subscription/{meta['slug']}/{meta['ipo_id']}/",
        )
        results.append(ipo)

    logger.info("Scraped subscription data for %d IPOs", len(results))
    return results
