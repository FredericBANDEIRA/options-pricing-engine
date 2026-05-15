"""
Implied Volatility Solver for European vanilla options.

Backs out the implied volatility (σ) from a market-observed option price
using the Black-Scholes model as the pricing function.

Two methods are available:
    1. Newton-Raphson (primary) — uses Vega as the derivative for fast
       quadratic convergence near the solution.
    2. Brent's method (fallback) — guaranteed convergence via bracketing,
       used when Newton-Raphson fails to converge.

Initial guess uses the Brenner-Subrahmanyam (1988) approximation:
    σ₀ ≈ √(2π / T) × C / S
"""

import numpy as np
from scipy.optimize import brentq

from pricer.models.black_scholes import price as bs_price, vega as bs_vega


# ---------------------------------------------------------------------------
# No-arbitrage bounds
# ---------------------------------------------------------------------------

def _validate_market_price(
    market_price: float, S: float, K: float, T: float,
    r: float, q: float, option_type: str,
) -> bool:
    """Check that the market price satisfies no-arbitrage bounds.

    Returns True if valid, False otherwise.
    """
    if market_price <= 0:
        return False

    # Intrinsic value (lower bound)
    if option_type == "call":
        intrinsic = max(S * np.exp(-q * T) - K * np.exp(-r * T), 0.0)
        upper = S * np.exp(-q * T)  # Call ≤ S·exp(-qT)
    else:
        intrinsic = max(K * np.exp(-r * T) - S * np.exp(-q * T), 0.0)
        upper = K * np.exp(-r * T)  # Put ≤ K·exp(-rT)

    if market_price < intrinsic - 1e-10:
        return False
    if market_price > upper + 1e-10:
        return False

    return True


# ---------------------------------------------------------------------------
# Initial guess
# ---------------------------------------------------------------------------

def _initial_guess(market_price: float, S: float, K: float, T: float) -> float:
    """Brenner-Subrahmanyam initial guess for implied vol.

    σ₀ ≈ √(2π / T) × price / S

    Clamped to [0.01, 5.0] for safety.
    """
    if T <= 0:
        return 0.20  # fallback

    sigma0 = np.sqrt(2 * np.pi / T) * market_price / S
    return float(np.clip(sigma0, 0.01, 5.0))


# ---------------------------------------------------------------------------
# Newton-Raphson solver
# ---------------------------------------------------------------------------

def _newton_raphson(
    market_price: float, S: float, K: float, T: float,
    r: float, q: float, option_type: str,
    tol: float = 1e-8, max_iter: int = 50,
) -> float | None:
    """Solve for implied vol using Newton-Raphson.

    Returns the implied vol, or None if convergence fails.
    """
    sigma = _initial_guess(market_price, S, K, T)

    for _ in range(max_iter):
        price_diff = bs_price(S, K, T, r, q, sigma, option_type) - market_price
        v = bs_vega(S, K, T, r, q, sigma)

        if abs(v) < 1e-15:
            # Vega too small — Newton step would be unstable
            return None

        sigma_new = sigma - price_diff / v

        # Ensure sigma stays positive
        if sigma_new <= 0:
            sigma_new = sigma * 0.5

        if abs(sigma_new - sigma) < tol:
            return float(sigma_new)

        sigma = sigma_new

    return None  # Did not converge


# ---------------------------------------------------------------------------
# Brent solver (fallback)
# ---------------------------------------------------------------------------

def _brent(
    market_price: float, S: float, K: float, T: float,
    r: float, q: float, option_type: str,
    tol: float = 1e-8,
) -> float | None:
    """Solve for implied vol using Brent's method (bracketing).

    Searches σ ∈ [0.001, 10.0].
    Returns the implied vol, or None if the root is not bracketed.
    """
    def objective(sigma: float) -> float:
        return bs_price(S, K, T, r, q, sigma, option_type) - market_price

    try:
        return float(brentq(objective, 0.001, 10.0, xtol=tol, maxiter=200))
    except ValueError:
        # Root not bracketed — no valid IV exists
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def implied_vol(
    market_price: float, S: float, K: float, T: float,
    r: float, q: float, option_type: str = "call",
    tol: float = 1e-8, max_iter: int = 50,
) -> float:
    """Compute the Black-Scholes implied volatility from a market price.

    Parameters
    ----------
    market_price : float – Observed option price
    S : float – Spot price
    K : float – Strike price
    T : float – Time to maturity (years)
    r : float – Risk-free rate (decimal)
    q : float – Continuous dividend yield (decimal)
    option_type : str – "call" or "put"
    tol : float – Convergence tolerance (default 1e-8)
    max_iter : int – Max Newton-Raphson iterations (default 50)

    Returns
    -------
    float – Implied volatility (decimal). Returns NaN if no valid IV exists.
    """
    # Validate inputs
    if T <= 0:
        return float("nan")

    if not _validate_market_price(market_price, S, K, T, r, q, option_type):
        return float("nan")

    # Try Newton-Raphson first (fast)
    result = _newton_raphson(market_price, S, K, T, r, q, option_type, tol, max_iter)

    if result is not None and result > 0:
        return result

    # Fallback to Brent (robust)
    result = _brent(market_price, S, K, T, r, q, option_type, tol)

    if result is not None and result > 0:
        return result

    return float("nan")
