"""Small formatting helpers shared by services and the seed script."""
from __future__ import annotations

from datetime import date
from typing import Optional


def format_lakh(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"Rs {value:,.2f} lakh"


def format_percent(value: Optional[float]) -> str:
    return "-" if value is None else f"{value:.1f}%"


def financial_year(day: date) -> str:
    """Indian financial year label, e.g. 2025-26."""
    if day.month >= 4:
        return f"{day.year}-{str(day.year + 1)[-2:]}"
    return f"{day.year - 1}-{str(day.year)[-2:]}"
