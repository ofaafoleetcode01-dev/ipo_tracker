from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


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
class AlertMessage:
    """A formatted alert ready to be sent."""

    ipos: list[IPOSubscription] = field(default_factory=list)

    def format(self) -> str:
        if not self.ipos:
            return ""

        header = "IPO Subscription Alert"
        separator = "─" * 30
        parts = [header, separator]

        for ipo in self.ipos:
            parts.append(ipo.summary())
            parts.append(separator)

        return "\n".join(parts)
