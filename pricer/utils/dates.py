"""
Date and time utilities for the Options Pricer.

Provides year-fraction computation using ACT/365 day-count convention,
which is the market standard for equity options.
"""

from datetime import date, datetime


def year_fraction(start: date, end: date) -> float:
    """Compute the year fraction between two dates using ACT/365.

    Parameters
    ----------
    start : date
        The valuation / today date.
    end : date
        The maturity / expiry date.

    Returns
    -------
    float
        Year fraction (T). Returns 0.0 if end <= start.
    """
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()

    delta = (end - start).days
    return max(delta / 365.0, 0.0)
