"""
Cox-Ross-Rubinstein (CRR) binomial tree for American-style option pricing.

The CRR model discretises the underlying's price evolution into an
N-step recombining binomial tree, with up/down factors:
    u = exp(σ√Δt),  d = 1/u
    p = [exp((r-q)Δt) - d] / (u - d)

Backward induction checks for early exercise at every node,
which captures the American premium over the European price.
"""

import numpy as np

from pricer.models.black_scholes import price as bs_price


def price(S: float, K: float, T: float, r: float, q: float,
          sigma: float, option_type: str = "call",
          n_steps: int = 200, style: str = "american") -> float:
    """Price an option using the CRR binomial tree.

    Parameters
    ----------
    S : float – Spot price
    K : float – Strike price
    T : float – Time to maturity (years)
    r : float – Risk-free rate (decimal)
    q : float – Continuous dividend yield (decimal)
    sigma : float – Volatility (decimal)
    option_type : str – "call" or "put"
    n_steps : int – Number of tree steps (default 200)
    style : str – "american" or "european"

    Returns
    -------
    float – Option price
    """
    if T <= 0:
        # At expiry – return intrinsic value
        if option_type == "call":
            return max(S - K, 0.0)
        else:
            return max(K - S, 0.0)

    dt = T / n_steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)
    disc = np.exp(-r * dt)

    # --- Build the terminal payoff vector ---
    # At step n_steps, the spot prices are: S * u^j * d^(n_steps - j) for j = 0..n_steps
    j = np.arange(n_steps + 1)
    S_T = S * u**j * d**(n_steps - j)

    if option_type == "call":
        option_values = np.maximum(S_T - K, 0.0)
    else:
        option_values = np.maximum(K - S_T, 0.0)

    # --- Backward induction ---
    for i in range(n_steps - 1, -1, -1):
        # Continuation value
        option_values = disc * (p * option_values[1:] + (1 - p) * option_values[:-1])

        if style == "american":
            # Spot prices at step i
            S_i = S * u**np.arange(i + 1) * d**(i - np.arange(i + 1))
            if option_type == "call":
                exercise = np.maximum(S_i - K, 0.0)
            else:
                exercise = np.maximum(K - S_i, 0.0)
            option_values = np.maximum(option_values, exercise)

    return float(option_values[0])


def early_exercise_analysis(S: float, K: float, T: float, r: float, q: float,
                            sigma: float, option_type: str = "call",
                            n_steps: int = 200) -> dict:
    """Compare European vs American pricing and compute the early exercise premium.

    Returns
    -------
    dict with:
        european_bs : European price (Black-Scholes closed-form)
        european_tree : European price (CRR tree, for convergence check)
        american_tree : American price (CRR tree)
        early_exercise_premium : American - European (BS)
        premium_pct : Premium as % of European price
    """
    eu_bs = bs_price(S, K, T, r, q, sigma, option_type)
    eu_tree = price(S, K, T, r, q, sigma, option_type, n_steps, style="european")
    am_tree = price(S, K, T, r, q, sigma, option_type, n_steps, style="american")
    premium = am_tree - eu_bs
    premium_pct = (premium / eu_bs * 100) if abs(eu_bs) > 1e-12 else 0.0

    return {
        "european_bs": eu_bs,
        "european_tree": eu_tree,
        "american_tree": am_tree,
        "early_exercise_premium": premium,
        "premium_pct": premium_pct,
    }
