"""
Exotic option pricing models.

Implements closed-form pricing for:
    - Barrier options (Reiner-Rubinstein continuous-monitoring formulas)
    - Digital / Binary options (cash-or-nothing, asset-or-nothing)
    - Asian options (geometric average closed-form)

Arithmetic Asian options are priced via Monte Carlo (see monte_carlo.py).
"""

import numpy as np
from scipy.stats import norm
from pricer.models.black_scholes import price as bs_price


# ---------------------------------------------------------------------------
# Digital / Binary options (closed-form)
# ---------------------------------------------------------------------------

def digital_price(
    S: float, K: float, T: float, r: float, q: float, sigma: float,
    option_type: str = "call", payout_type: str = "cash-or-nothing",
    payout: float = 1.0,
) -> float:
    """Price a digital (binary) option.

    Parameters
    ----------
    option_type : "call" or "put"
    payout_type : "cash-or-nothing" or "asset-or-nothing"
    payout : float – Cash payout amount (for cash-or-nothing)

    Returns
    -------
    float – Option price
    """
    if T <= 0 or sigma <= 0:
        if payout_type == "cash-or-nothing":
            if option_type == "call":
                return payout * np.exp(-r * T) if S > K else 0.0
            else:
                return payout * np.exp(-r * T) if S < K else 0.0
        else:
            if option_type == "call":
                return S if S > K else 0.0
            else:
                return S if S < K else 0.0

    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T

    if payout_type == "cash-or-nothing":
        if option_type == "call":
            return payout * np.exp(-r * T) * norm.cdf(d2)
        else:
            return payout * np.exp(-r * T) * norm.cdf(-d2)
    else:  # asset-or-nothing
        if option_type == "call":
            return S * np.exp(-q * T) * norm.cdf(d1)
        else:
            return S * np.exp(-q * T) * norm.cdf(-d1)


# ---------------------------------------------------------------------------
# Barrier options (Reiner-Rubinstein closed-form, continuous monitoring)
# ---------------------------------------------------------------------------

def _barrier_params(S, K, T, r, q, sigma, barrier):
    """Pre-compute shared barrier option parameters."""
    sqrt_T = np.sqrt(T)
    mu = (r - q - 0.5 * sigma**2) / sigma**2
    lam = np.sqrt(mu**2 + 2 * r / sigma**2)
    x1 = np.log(S / K) / (sigma * sqrt_T) + (1 + mu) * sigma * sqrt_T
    x2 = np.log(S / barrier) / (sigma * sqrt_T) + (1 + mu) * sigma * sqrt_T
    y1 = np.log(barrier**2 / (S * K)) / (sigma * sqrt_T) + (1 + mu) * sigma * sqrt_T
    y2 = np.log(barrier / S) / (sigma * sqrt_T) + (1 + mu) * sigma * sqrt_T
    z = np.log(barrier / S) / (sigma * sqrt_T) + lam * sigma * sqrt_T
    return mu, lam, x1, x2, y1, y2, z, sqrt_T


def barrier_price(
    S: float, K: float, T: float, r: float, q: float, sigma: float,
    barrier: float, barrier_type: str = "down-and-out",
    option_type: str = "call",
) -> float:
    """Price a barrier option (continuous monitoring, no rebate).

    Parameters
    ----------
    barrier : float – Barrier level
    barrier_type : str – One of: "down-and-out", "down-and-in",
                         "up-and-out", "up-and-in"
    option_type : str – "call" or "put"

    Returns
    -------
    float – Option price (0 if barrier already breached at inception)
    """
    if T <= 0 or sigma <= 0:
        vanilla = max(S - K, 0.0) if option_type == "call" else max(K - S, 0.0)
        if "out" in barrier_type:
            if "down" in barrier_type and S <= barrier:
                return 0.0
            if "up" in barrier_type and S >= barrier:
                return 0.0
            return vanilla
        else:  # knock-in
            if "down" in barrier_type and S <= barrier:
                return vanilla
            if "up" in barrier_type and S >= barrier:
                return vanilla
            return 0.0

    vanilla = bs_price(S, K, T, r, q, sigma, option_type)

    # Use in-out parity: knock-in + knock-out = vanilla
    if "in" in barrier_type:
        out_type = barrier_type.replace("in", "out")
        out_price = _barrier_out_price(S, K, T, r, q, sigma, barrier, out_type, option_type)
        return max(vanilla - out_price, 0.0)

    return _barrier_out_price(S, K, T, r, q, sigma, barrier, barrier_type, option_type)


def _barrier_out_price(S, K, T, r, q, sigma, barrier, barrier_type, option_type):
    """Compute knock-out barrier option price using Reiner-Rubinstein."""
    H = barrier
    mu, lam, x1, x2, y1, y2, z, sqrt_T = _barrier_params(S, K, T, r, q, sigma, H)
    phi = 1.0 if option_type == "call" else -1.0

    def A(phi_val):
        return phi_val * S * np.exp(-q * T) * norm.cdf(phi_val * x1) - \
               phi_val * K * np.exp(-r * T) * norm.cdf(phi_val * (x1 - sigma * sqrt_T))

    def B(phi_val):
        return phi_val * S * np.exp(-q * T) * norm.cdf(phi_val * x2) - \
               phi_val * K * np.exp(-r * T) * norm.cdf(phi_val * (x2 - sigma * sqrt_T))

    def C(phi_val, eta):
        ratio = (H / S) ** (2 * (mu + 1))
        return phi_val * S * np.exp(-q * T) * ratio * norm.cdf(eta * y1) - \
               phi_val * K * np.exp(-r * T) * (H / S) ** (2 * mu) * norm.cdf(eta * (y1 - sigma * sqrt_T))

    def D(phi_val, eta):
        ratio = (H / S) ** (2 * (mu + 1))
        return phi_val * S * np.exp(-q * T) * ratio * norm.cdf(eta * y2) - \
               phi_val * K * np.exp(-r * T) * (H / S) ** (2 * mu) * norm.cdf(eta * (y2 - sigma * sqrt_T))

    if barrier_type == "down-and-out" and option_type == "call":
        if S <= H:
            return 0.0
        if K > H:
            return A(1) - C(1, 1)
        else:
            return B(1) - D(1, 1)

    elif barrier_type == "up-and-out" and option_type == "call":
        if S >= H:
            return 0.0
        if K > H:
            return 0.0
        else:
            return A(1) - B(1) + D(1, -1) - C(1, -1)

    elif barrier_type == "down-and-out" and option_type == "put":
        if S <= H:
            return 0.0
        if K > H:
            return A(-1) - B(-1) + D(-1, 1) - C(-1, 1)
        else:
            return B(-1) - D(-1, 1)

    elif barrier_type == "up-and-out" and option_type == "put":
        if S >= H:
            return 0.0
        if K > H:
            return A(-1) - C(-1, -1)
        else:
            return 0.0

    # Fallback — shouldn't reach here
    return max(bs_price(S, K, T, r, q, sigma, option_type), 0.0)


# ---------------------------------------------------------------------------
# Asian options (geometric average, closed-form)
# ---------------------------------------------------------------------------

def asian_geometric_price(
    S: float, K: float, T: float, r: float, q: float, sigma: float,
    option_type: str = "call", n_avg: int = 252,
) -> float:
    """Price an Asian option with geometric average (closed-form).

    Uses the Kemna-Vorst (1990) approximation: the geometric average
    of a GBM is lognormal, so BSM formulas apply with adjusted params.

    Parameters
    ----------
    n_avg : int – Number of averaging points (default 252 = daily)

    Returns
    -------
    float – Geometric Asian option price
    """
    if T <= 0 or sigma <= 0:
        if option_type == "call":
            return max(S - K, 0.0)
        else:
            return max(K - S, 0.0)

    # Kemna-Vorst continuous geometric average parameters
    sigma_adj = sigma / np.sqrt(3)
    b_adj = 0.5 * (r - q - sigma**2 / 6)
    q_adj = r - b_adj
    
    # Use BS with original discount rate (r) and adjusted dividend yield (q_adj)
    return bs_price(S, K, T, r, q_adj, sigma_adj, option_type)
