"""
Black-Scholes-Merton closed-form pricing and Greeks for European vanilla options.

Implements the standard BSM model with continuous dividend yield:
    C = S·exp(-qT)·N(d1) - K·exp(-rT)·N(d2)
    P = K·exp(-rT)·N(-d2) - S·exp(-qT)·N(-d1)

where:
    d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
    d2 = d1 - σ√T

All Greeks are computed analytically (no finite-difference approximation).
"""

import numpy as np
from scipy.stats import norm


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _d1d2(S: float, K: float, T: float, r: float, q: float, sigma: float):
    """Compute d1 and d2 for the BSM formula.

    Returns (d1, d2). Handles the edge case T ≈ 0 by returning
    extreme values based on moneyness.
    """
    if T <= 0 or sigma <= 0:
        # At expiry or zero-vol: intrinsic value regime
        if S > K:
            return 1e10, 1e10
        elif S < K:
            return -1e10, -1e10
        else:
            return 0.0, 0.0

    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------

def price(S: float, K: float, T: float, r: float, q: float,
          sigma: float, option_type: str = "call") -> float:
    """Black-Scholes price for a European call or put.

    Parameters
    ----------
    S : float – Spot price
    K : float – Strike price
    T : float – Time to maturity (years)
    r : float – Risk-free rate (decimal, e.g. 0.05 for 5%)
    q : float – Continuous dividend yield (decimal)
    sigma : float – Volatility (decimal, e.g. 0.20 for 20%)
    option_type : str – "call" or "put"

    Returns
    -------
    float – Option price
    """
    d1, d2 = _d1d2(S, K, T, r, q, sigma)

    if option_type == "call":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def forward(S: float, T: float, r: float, q: float) -> float:
    """Forward price: F = S · exp((r - q) · T)."""
    return S * np.exp((r - q) * T)


# ---------------------------------------------------------------------------
# Unit Greeks (per-option, not position-scaled)
# ---------------------------------------------------------------------------

def delta(S: float, K: float, T: float, r: float, q: float,
          sigma: float, option_type: str = "call") -> float:
    """BSM Delta.

    Call: exp(-qT) · N(d1)
    Put:  exp(-qT) · (N(d1) - 1)
    """
    d1, _ = _d1d2(S, K, T, r, q, sigma)
    discount = np.exp(-q * T)
    if option_type == "call":
        return discount * norm.cdf(d1)
    else:
        return discount * (norm.cdf(d1) - 1.0)


def gamma(S: float, K: float, T: float, r: float, q: float,
          sigma: float) -> float:
    """BSM Gamma (same for call and put).

    Γ = exp(-qT) · n(d1) / (S · σ · √T)
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, _ = _d1d2(S, K, T, r, q, sigma)
    return np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))


def vega(S: float, K: float, T: float, r: float, q: float,
         sigma: float) -> float:
    """BSM Vega (same for call and put).

    ν = S · exp(-qT) · n(d1) · √T

    This is the sensitivity per 1 unit (100%) change in σ.
    For Vega/1%, multiply by 0.01.
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, _ = _d1d2(S, K, T, r, q, sigma)
    return S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)


def theta(S: float, K: float, T: float, r: float, q: float,
          sigma: float, option_type: str = "call") -> float:
    """BSM Theta (per year).

    Call: -(S·n(d1)·σ·exp(-qT))/(2√T) - r·K·exp(-rT)·N(d2) + q·S·exp(-qT)·N(d1)
    Put:  -(S·n(d1)·σ·exp(-qT))/(2√T) + r·K·exp(-rT)·N(-d2) - q·S·exp(-qT)·N(-d1)

    To get Theta/day, divide by 365.
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, d2 = _d1d2(S, K, T, r, q, sigma)
    sqrt_T = np.sqrt(T)
    exp_qT = np.exp(-q * T)
    exp_rT = np.exp(-r * T)
    nd1 = norm.pdf(d1)

    term1 = -(S * nd1 * sigma * exp_qT) / (2 * sqrt_T)

    if option_type == "call":
        return term1 - r * K * exp_rT * norm.cdf(d2) + q * S * exp_qT * norm.cdf(d1)
    else:
        return term1 + r * K * exp_rT * norm.cdf(-d2) - q * S * exp_qT * norm.cdf(-d1)


def rho(S: float, K: float, T: float, r: float, q: float,
        sigma: float, option_type: str = "call") -> float:
    """BSM Rho (per 1 unit = 100% change in r).

    Call: K·T·exp(-rT)·N(d2)
    Put: -K·T·exp(-rT)·N(-d2)

    For Rho/1%, multiply by 0.01.
    """
    if T <= 0:
        return 0.0
    _, d2 = _d1d2(S, K, T, r, q, sigma)
    exp_rT = np.exp(-r * T)
    if option_type == "call":
        return K * T * exp_rT * norm.cdf(d2)
    else:
        return -K * T * exp_rT * norm.cdf(-d2)


def vanna(S: float, K: float, T: float, r: float, q: float,
          sigma: float) -> float:
    """BSM Vanna (∂Δ/∂σ = ∂ν/∂S). Same for call and put.

    Vanna = -exp(-qT) · n(d1) · d2 / σ
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, d2 = _d1d2(S, K, T, r, q, sigma)
    return -np.exp(-q * T) * norm.pdf(d1) * d2 / sigma


def charm(S: float, K: float, T: float, r: float, q: float,
          sigma: float, option_type: str = "call") -> float:
    """BSM Charm (Delta decay, ∂Δ/∂T with sign flipped for passage of time).

    Charm = -exp(-qT) · [n(d1) · (2(r-q)T - d2·σ·√T) / (2T·σ·√T)]
            + (call: -q·exp(-qT)·N(d1), put: +q·exp(-qT)·N(-d1))

    Note: This is per year. Divide by 365 for daily charm.
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, d2 = _d1d2(S, K, T, r, q, sigma)
    sqrt_T = np.sqrt(T)
    exp_qT = np.exp(-q * T)
    nd1 = norm.pdf(d1)

    common = -exp_qT * nd1 * (2 * (r - q) * T - d2 * sigma * sqrt_T) / (2 * T * sigma * sqrt_T)

    if option_type == "call":
        return common - q * exp_qT * norm.cdf(d1)
    else:
        return common + q * exp_qT * norm.cdf(-d1)


# ---------------------------------------------------------------------------
# All Greeks in one call (performance: compute d1/d2 once)
# ---------------------------------------------------------------------------

def all_greeks(S: float, K: float, T: float, r: float, q: float,
               sigma: float, option_type: str = "call") -> dict:
    """Compute all unit Greeks in a single pass.

    Returns a dict with keys:
        delta, gamma, vega, theta, rho, vanna, charm
    """
    if T <= 0 or sigma <= 0:
        # At expiry: only delta has meaning (0 or 1)
        intrinsic_delta = 0.0
        if option_type == "call":
            intrinsic_delta = 1.0 if S > K else (0.5 if S == K else 0.0)
        else:
            intrinsic_delta = -1.0 if S < K else (-0.5 if S == K else 0.0)
        return {
            "delta": intrinsic_delta,
            "gamma": 0.0,
            "vega": 0.0,
            "theta": 0.0,
            "rho": 0.0,
            "vanna": 0.0,
            "charm": 0.0,
        }

    d1, d2 = _d1d2(S, K, T, r, q, sigma)
    sqrt_T = np.sqrt(T)
    exp_qT = np.exp(-q * T)
    exp_rT = np.exp(-r * T)
    nd1_pdf = norm.pdf(d1)
    Nd1 = norm.cdf(d1)
    Nd2 = norm.cdf(d2)

    # --- Delta ---
    if option_type == "call":
        _delta = exp_qT * Nd1
    else:
        _delta = exp_qT * (Nd1 - 1.0)

    # --- Gamma (same for call/put) ---
    _gamma = exp_qT * nd1_pdf / (S * sigma * sqrt_T)

    # --- Vega (same for call/put) ---
    _vega = S * exp_qT * nd1_pdf * sqrt_T

    # --- Theta ---
    term1 = -(S * nd1_pdf * sigma * exp_qT) / (2 * sqrt_T)
    if option_type == "call":
        _theta = term1 - r * K * exp_rT * Nd2 + q * S * exp_qT * Nd1
    else:
        _theta = term1 + r * K * exp_rT * norm.cdf(-d2) - q * S * exp_qT * norm.cdf(-d1)

    # --- Rho ---
    if option_type == "call":
        _rho = K * T * exp_rT * Nd2
    else:
        _rho = -K * T * exp_rT * norm.cdf(-d2)

    # --- Vanna ---
    _vanna = -exp_qT * nd1_pdf * d2 / sigma

    # --- Charm ---
    charm_common = -exp_qT * nd1_pdf * (2 * (r - q) * T - d2 * sigma * sqrt_T) / (2 * T * sigma * sqrt_T)
    if option_type == "call":
        _charm = charm_common - q * exp_qT * Nd1
    else:
        _charm = charm_common + q * exp_qT * norm.cdf(-d1)

    return {
        "delta": float(_delta),
        "gamma": float(_gamma),
        "vega": float(_vega),
        "theta": float(_theta),
        "rho": float(_rho),
        "vanna": float(_vanna),
        "charm": float(_charm),
    }


# ---------------------------------------------------------------------------
# Cash / Position-level Greeks
# ---------------------------------------------------------------------------

def cash_greeks(S: float, K: float, T: float, r: float, q: float,
                sigma: float, option_type: str = "call",
                lots: float = 1.0, mult: float = 100.0) -> dict:
    """Compute position-level (cash) Greeks.

    Returns a dict with keys:
        bs_price, forward, cash_delta, delta_hedge, delta_t1d,
        gamma_1pct, theta_day, vega_1pct, charm_day, vanna_1pct, rho_1pct
    Also includes unit greeks nested under 'unit'.
    """
    unit = all_greeks(S, K, T, r, q, sigma, option_type)
    bs_price = price(S, K, T, r, q, sigma, option_type)
    fwd = forward(S, T, r, q)
    position = lots * mult

    return {
        "bs_price": bs_price,
        "forward": fwd,
        # Cash delta = Δ × S × position
        "cash_delta": unit["delta"] * S * position,
        # Delta hedge = Δ × position (number of shares)
        "delta_hedge": unit["delta"] * position,
        # ΔT+1D = charm per day × position (daily change in delta shares)
        "delta_t1d": (unit["charm"] / 365) * position,
        # Gamma / 1% = P&L for a 1% spot move = ½ Γ (S × 0.01)² × position
        "gamma_1pct": 0.5 * unit["gamma"] * (S * 0.01) ** 2 * position,
        # Theta / day = Θ / 365 × position
        "theta_day": (unit["theta"] / 365) * position,
        # Vega / 1% = ν × 0.01 × position
        "vega_1pct": unit["vega"] * 0.01 * position,
        # Charm / day = charm / 365 × S × position
        "charm_day": (unit["charm"] / 365) * S * position,
        # Vanna / 1% = vanna × 0.01 × S × position
        "vanna_1pct": unit["vanna"] * 0.01 * S * position,
        # Rho / 1% = rho × 0.01 × position
        "rho_1pct": unit["rho"] * 0.01 * position,
        # Nested unit greeks
        "unit": unit,
    }


# ---------------------------------------------------------------------------
# Gamma PnL calculator
# ---------------------------------------------------------------------------

def gamma_pnl(S: float, K: float, T: float, r: float, q: float,
              sigma: float, option_type: str = "call",
              spot_move_pct: float = 1.0,
              lots: float = 1.0, mult: float = 100.0) -> dict:
    """Compute Gamma P&L for a given spot move.

    Parameters
    ----------
    spot_move_pct : float – Spot move in percent (e.g. 1.0 = 1%)

    Returns
    -------
    dict with:
        new_delta_cash : Cash delta after the spot move
        gamma_pnl : P&L from gamma (second-order)
        iv_pct : Implied vol (passed through)
        daily_move : Daily 1-σ move in percent
    """
    unit = all_greeks(S, K, T, r, q, sigma, option_type)
    position = lots * mult
    move_frac = spot_move_pct / 100.0

    # New spot
    S_new = S * (1 + move_frac)
    # New delta at new spot (approximate using gamma)
    new_delta_approx = unit["delta"] + unit["gamma"] * (S_new - S)
    new_cash_delta = new_delta_approx * S_new * position

    # Gamma P&L = ½ Γ S² Δx² × position
    g_pnl = 0.5 * unit["gamma"] * S**2 * move_frac**2 * position

    # Daily 1-σ move
    daily_move = sigma / np.sqrt(252) * 100  # in percent

    return {
        "new_delta_cash": new_cash_delta,
        "gamma_pnl": g_pnl,
        "iv_pct": sigma * 100,
        "daily_move": daily_move,
    }


# ---------------------------------------------------------------------------
# Quick Calc: Gamma → Theta bill
# ---------------------------------------------------------------------------

def gamma_theta_bill(S: float, K: float, T: float, r: float, q: float,
                     sigma: float, option_type: str = "call",
                     lots: float = 1.0, mult: float = 100.0) -> dict:
    """Gamma → Theta bill relationship.

    Theoretical daily theta implied by gamma exposure:
        Θ_daily ≈ ½ · Γ · S² · σ² / 365

    This is useful for understanding the gamma/theta trade-off:
    a long gamma position pays theta (time decay) to maintain its convexity.

    Returns
    -------
    dict with:
        gamma_cash : Cash gamma (1%)
        theta_implied : Theoretical daily theta from gamma
        theta_actual : Actual daily theta from BS
        theta_ratio : Actual / Implied (should be close to 1 for ATM, short-dated)
    """
    unit = all_greeks(S, K, T, r, q, sigma, option_type)
    position = lots * mult

    gamma_cash_1pct = 0.5 * unit["gamma"] * (S * 0.01) ** 2 * position
    theta_implied_daily = 0.5 * unit["gamma"] * S**2 * sigma**2 / 365.0 * position
    theta_actual_daily = (unit["theta"] / 365.0) * position

    ratio = theta_actual_daily / theta_implied_daily if abs(theta_implied_daily) > 1e-12 else 0.0

    return {
        "gamma_cash_1pct": gamma_cash_1pct,
        "theta_implied_daily": theta_implied_daily,
        "theta_actual_daily": theta_actual_daily,
        "theta_ratio": ratio,
    }
