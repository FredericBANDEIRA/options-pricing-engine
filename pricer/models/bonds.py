"""
Fixed-Income Bond Pricer.

Provides analytical pricing and risk measures for plain-vanilla fixed-rate bonds:
    - Dirty & clean price from yield (discounted cash-flow)
    - Accrued interest (ACT/ACT or 30/360)
    - Yield to maturity (YTM) — Newton-Raphson + Brent fallback
    - Macaulay duration
    - Modified duration
    - Convexity
    - DV01 (Dollar Value of a Basis Point)
    - Key-rate duration (parallel shift sensitivity)
    - Price/yield curve data
    - Cash-flow schedule

Conventions
-----------
- Coupon frequency: annual (1), semi-annual (2), quarterly (4)
- Day count: ACT/ACT for accrued interest (simplified)
- Yield and coupon are in decimal form (e.g. 0.05 for 5%)
"""

import numpy as np
from scipy.optimize import brentq


# ---------------------------------------------------------------------------
# Cash-flow schedule
# ---------------------------------------------------------------------------

def cash_flow_schedule(
    face: float,
    coupon_rate: float,
    n_periods: int,
    freq: int = 2,
) -> list[dict]:
    """Generate the cash-flow schedule for a fixed-rate bond.

    Parameters
    ----------
    face : float – Face (par) value
    coupon_rate : float – Annual coupon rate (decimal)
    n_periods : int – Total number of remaining coupon periods
    freq : int – Coupon frequency per year (1, 2, or 4)

    Returns
    -------
    list of dict with keys: period, time (years), coupon, principal, total
    """
    coupon = face * coupon_rate / freq
    schedule = []

    for i in range(1, n_periods + 1):
        t = i / freq
        principal = face if i == n_periods else 0.0
        schedule.append({
            "period": i,
            "time": t,
            "coupon": coupon,
            "principal": principal,
            "total": coupon + principal,
        })

    return schedule


# ---------------------------------------------------------------------------
# Bond pricing
# ---------------------------------------------------------------------------

def dirty_price(
    face: float,
    coupon_rate: float,
    ytm: float,
    n_periods: int,
    freq: int = 2,
) -> float:
    """Compute the dirty (full) price of a bond.

    Uses standard discounted cash-flow:
        P = Σ CF_i / (1 + y/freq)^i

    Parameters
    ----------
    face : float – Face value
    coupon_rate : float – Annual coupon rate (decimal)
    ytm : float – Yield to maturity (decimal, annual)
    n_periods : int – Remaining coupon periods
    freq : int – Coupon frequency per year

    Returns
    -------
    float – Dirty price
    """
    if n_periods <= 0:
        return face

    coupon = face * coupon_rate / freq
    y = ytm / freq

    if abs(y) < 1e-12:
        # Zero yield — just sum undiscounted cash flows
        return coupon * n_periods + face

    # PV of coupon annuity + PV of face
    pv_coupons = coupon * (1 - (1 + y) ** (-n_periods)) / y
    pv_face = face / (1 + y) ** n_periods

    return pv_coupons + pv_face


def accrued_interest(
    face: float,
    coupon_rate: float,
    freq: int,
    days_since_last_coupon: int,
    days_in_coupon_period: int,
) -> float:
    """Compute accrued interest (linear day-count approximation).

    AI = (days_since / days_in_period) × coupon_per_period
    """
    coupon_per_period = face * coupon_rate / freq
    if days_in_coupon_period <= 0:
        return 0.0
    return coupon_per_period * days_since_last_coupon / days_in_coupon_period


def clean_price(
    face: float,
    coupon_rate: float,
    ytm: float,
    n_periods: int,
    freq: int = 2,
    days_since_last_coupon: int = 0,
    days_in_coupon_period: int = 182,
) -> float:
    """Compute the clean price (dirty price minus accrued interest)."""
    dp = dirty_price(face, coupon_rate, ytm, n_periods, freq)
    ai = accrued_interest(face, coupon_rate, freq,
                          days_since_last_coupon, days_in_coupon_period)
    return dp - ai


# ---------------------------------------------------------------------------
# Yield to Maturity solver
# ---------------------------------------------------------------------------

def yield_to_maturity(
    market_price: float,
    face: float,
    coupon_rate: float,
    n_periods: int,
    freq: int = 2,
    tol: float = 1e-10,
) -> float:
    """Solve for the yield to maturity given a market price.

    Uses Newton-Raphson (fast) with Brent fallback (robust).

    Parameters
    ----------
    market_price : float – Observed market price (dirty)
    face : float – Face value
    coupon_rate : float – Annual coupon rate (decimal)
    n_periods : int – Remaining coupon periods
    freq : int – Coupon frequency per year

    Returns
    -------
    float – YTM (annual, decimal). Returns NaN if no solution.
    """
    if n_periods <= 0 or market_price <= 0:
        return float("nan")

    def objective(y: float) -> float:
        return dirty_price(face, coupon_rate, y, n_periods, freq) - market_price

    # Newton-Raphson with numerical derivative
    # Initial guess: current yield
    coupon_annual = face * coupon_rate
    y = coupon_annual / market_price  # Current yield as starting point
    if y <= 0:
        y = 0.05

    for _ in range(100):
        p = objective(y)
        # Numerical derivative
        dy = 1e-6
        dp = (objective(y + dy) - p) / dy
        if abs(dp) < 1e-15:
            break
        y_new = y - p / dp
        if y_new < -0.5:
            y_new = y * 0.5
        if abs(y_new - y) < tol:
            return float(y_new)
        y = y_new

    # Fallback: Brent's method
    try:
        return float(brentq(objective, -0.20, 2.0, xtol=tol, maxiter=500))
    except ValueError:
        return float("nan")


# ---------------------------------------------------------------------------
# Duration & Convexity
# ---------------------------------------------------------------------------

def macaulay_duration(
    face: float,
    coupon_rate: float,
    ytm: float,
    n_periods: int,
    freq: int = 2,
) -> float:
    """Compute Macaulay duration (in years).

    D_mac = (1/P) × Σ t_i × CF_i / (1 + y/freq)^i
    """
    p = dirty_price(face, coupon_rate, ytm, n_periods, freq)
    if p <= 0 or n_periods <= 0:
        return 0.0

    coupon = face * coupon_rate / freq
    y = ytm / freq
    weighted_sum = 0.0

    for i in range(1, n_periods + 1):
        t = i / freq  # time in years
        cf = coupon + (face if i == n_periods else 0.0)
        pv_cf = cf / (1 + y) ** i
        weighted_sum += t * pv_cf

    return weighted_sum / p


def modified_duration(
    face: float,
    coupon_rate: float,
    ytm: float,
    n_periods: int,
    freq: int = 2,
) -> float:
    """Compute modified duration.

    D_mod = D_mac / (1 + y/freq)
    """
    d_mac = macaulay_duration(face, coupon_rate, ytm, n_periods, freq)
    return d_mac / (1 + ytm / freq)


def convexity(
    face: float,
    coupon_rate: float,
    ytm: float,
    n_periods: int,
    freq: int = 2,
) -> float:
    """Compute convexity.

    C = (1/P) × (1/(1+y/freq)^2) × Σ t_i×(t_i + 1/freq) × CF_i / (1+y/freq)^i
    """
    p = dirty_price(face, coupon_rate, ytm, n_periods, freq)
    if p <= 0 or n_periods <= 0:
        return 0.0

    coupon = face * coupon_rate / freq
    y = ytm / freq
    conv_sum = 0.0

    for i in range(1, n_periods + 1):
        cf = coupon + (face if i == n_periods else 0.0)
        pv_cf = cf / (1 + y) ** i
        t = i / freq
        conv_sum += t * (t + 1 / freq) * pv_cf

    return conv_sum / (p * (1 + y) ** 2)


def dv01(
    face: float,
    coupon_rate: float,
    ytm: float,
    n_periods: int,
    freq: int = 2,
) -> float:
    """Dollar Value of a Basis Point (DV01).

    Approximate change in price for a 1 bp increase in yield.
    DV01 ≈ -ModDur × Price × 0.0001
    """
    p = dirty_price(face, coupon_rate, ytm, n_periods, freq)
    md = modified_duration(face, coupon_rate, ytm, n_periods, freq)
    return abs(md * p * 0.0001)


# ---------------------------------------------------------------------------
# Price/Yield curve
# ---------------------------------------------------------------------------

def price_yield_curve(
    face: float,
    coupon_rate: float,
    n_periods: int,
    freq: int = 2,
    yield_min: float = 0.0,
    yield_max: float = 0.15,
    n_points: int = 150,
) -> dict:
    """Generate price vs yield data for plotting.

    Returns dict with: yields, prices (both as arrays)
    """
    yields = np.linspace(yield_min, yield_max, n_points)
    prices = np.array([
        dirty_price(face, coupon_rate, y, n_periods, freq) for y in yields
    ])

    return {"yields": yields, "prices": prices}


# ---------------------------------------------------------------------------
# Full bond analytics
# ---------------------------------------------------------------------------

def bond_analytics(
    face: float,
    coupon_rate: float,
    ytm: float,
    n_periods: int,
    freq: int = 2,
) -> dict:
    """Compute all bond analytics in one call.

    Returns dict with: dirty_price, macaulay_duration, modified_duration,
                       convexity, dv01, current_yield, cash_flows
    """
    dp = dirty_price(face, coupon_rate, ytm, n_periods, freq)
    d_mac = macaulay_duration(face, coupon_rate, ytm, n_periods, freq)
    d_mod = modified_duration(face, coupon_rate, ytm, n_periods, freq)
    conv = convexity(face, coupon_rate, ytm, n_periods, freq)
    dollar_dv01 = dv01(face, coupon_rate, ytm, n_periods, freq)
    annual_coupon = face * coupon_rate
    curr_yield = annual_coupon / dp if dp > 0 else 0.0

    return {
        "dirty_price": dp,
        "macaulay_duration": d_mac,
        "modified_duration": d_mod,
        "convexity": conv,
        "dv01": dollar_dv01,
        "current_yield": curr_yield,
        "annual_coupon": annual_coupon,
        "cash_flows": cash_flow_schedule(face, coupon_rate, n_periods, freq),
    }
