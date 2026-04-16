from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

@dataclass
class IPOTrackerMainInput:
    """Represents the input object to be sent to IPOTrackerMain.main()"""
    debug: bool = False
    morning: bool = False
    skip_date_filter: bool = False
    dry_run: bool = False

    def build_from_args(self, args: dict):
        self.debug = bool(args["debug"])
        self.morning = bool(args["morning"])
        self.skip_date_filter = bool(args["skip_date_filter"])
        self.dry_run = bool(args["dry_run"])

@dataclass
class IPOSubscription:
    """Represents subscription data for a single IPO."""

    name: str
    close_date: date
    ipo_type: str  # "mainboard" or "sme"
    issue_size_cr: Optional[float] = None
    qib_subscription: float = 0.0
    snii_subscription: float = 0.0
    bnii_subscription: float = 0.0
    retail_subscription: float = 0.0
    employee_subscription: float = 0.0
    others_subscription: float = 0.0
    total_subscription: float = 0.0
    detail_url: str = ""

    @property
    def is_mainboard(self) -> bool:
        return self.ipo_type.lower() == "mainboard"

    @property
    def is_closing_today(self) -> bool:
        return self.close_date == date.today()

    def summary(self) -> str:
        lines = [
            f"*{self.name}*",
            f"Close Date: {self.close_date.strftime('%d %b %Y')}",
            f"Type: {self.ipo_type.capitalize()}",
        ]
        if self.issue_size_cr is not None:
            lines.append(f"Issue Size: Rs {self.issue_size_cr:.2f} Cr")
        lines += [
            f"QIB: {self.qib_subscription:.2f}x",
            f"sNII: {self.snii_subscription:.2f}x",
            f"bNII: {self.bnii_subscription:.2f}x",
            f"Retail: {self.retail_subscription:.2f}x",
            f"Total: {self.total_subscription:.2f}x",
        ]
        return "\n".join(lines)


@dataclass
class IPOAlertMessage:
    """A formatted alert ready to be sent."""
    def __init__(self, ipos: list[IPOSubscription]):
        self.today = date.today()    # TODO: Has timezone issues
        self.today_str = self.today.strftime("%d %b %Y")
        self.ipos: list[IPOSubscription] = ipos
        self.closing_today = [ipo for ipo in self.ipos if ipo.close_date == self.today]

    def format(self, is_morning: bool = False) -> str:
        return self.default() if not is_morning else self.morning_message()

    def default(self) -> str:
        if not self.ipos:
            return ""

        header = "IPO Alert"
        separator = "─" * 30
        parts = [header, separator]

        for ipo in self.ipos:
            parts.append(ipo.summary())
            parts.append(separator)

        return "\n".join(parts)

    def morning_message(self) -> str:
        if self.closing_today:
            names = "\n".join(f"  • {ipo.name}" for ipo in self.closing_today)
            msg = (
                f"*Good Morning! IPOs for {self.today_str}*\n"
                f"{'─' * 30}\n\n"
                f"*{len(self.closing_today)} IPO(s) closing today:*\n"
                f"{names}\n\n"
                f"Subscription reports coming at *3:00 PM* and *3:30 PM* IST.\n"
                f"Buckle up — it's going to be an exciting day!"
            )
        else:
            msg = (
                f"*Good Morning! IPOs for {self.today_str}*\n"
                f"{'─' * 30}\n\n"
                f"No IPOs closing today.\n"
                f"Enjoy your day — we'll keep watching!"
            )
        return msg