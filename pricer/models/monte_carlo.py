"""
Monte Carlo simulation engine for option pricing.

Implements GBM path simulation with variance reduction:
    dS = (r - q) S dt + σ S dW

Features:
    - Vectorised path generation (NumPy)
    - Antithetic variates
    - Control variate (BS analytical)
    - Generic payoff interface for exotic options
"""

import numpy as np
from typing import Callable
from pricer.models.black_scholes import price as bs_price


def simulate_paths(
    S: float, T: float, r: float, q: float, sigma: float,
    n_paths: int = 100_000, n_steps: int = 252,
    antithetic: bool = True, seed: int | None = None,
) -> np.ndarray:
    """Simulate GBM price paths.

    Returns shape (n_paths, n_steps + 1), each row starting at S.
    """
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    drift = (r - q - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt)

    if antithetic:
        half = n_paths // 2
        Z = rng.standard_normal((half, n_steps))
        Z = np.vstack([Z, -Z])
    else:
        Z = rng.standard_normal((n_paths, n_steps))

    log_returns = drift + diffusion * Z
    log_paths = np.cumsum(log_returns, axis=1)
    paths = np.zeros((Z.shape[0], n_steps + 1))
    paths[:, 0] = S
    paths[:, 1:] = S * np.exp(log_paths)
    return paths


# ---------------------------------------------------------------------------
# Payoff functions
# ---------------------------------------------------------------------------

def payoff_european_call(paths: np.ndarray, K: float) -> np.ndarray:
    return np.maximum(paths[:, -1] - K, 0.0)

def payoff_european_put(paths: np.ndarray, K: float) -> np.ndarray:
    return np.maximum(K - paths[:, -1], 0.0)

def payoff_asian_call(paths: np.ndarray, K: float) -> np.ndarray:
    return np.maximum(np.mean(paths[:, 1:], axis=1) - K, 0.0)

def payoff_asian_put(paths: np.ndarray, K: float) -> np.ndarray:
    return np.maximum(K - np.mean(paths[:, 1:], axis=1), 0.0)

def payoff_barrier_up_and_out_call(paths: np.ndarray, K: float, barrier: float = 120.0) -> np.ndarray:
    hit = np.any(paths[:, 1:] >= barrier, axis=1)
    pf = np.maximum(paths[:, -1] - K, 0.0)
    pf[hit] = 0.0
    return pf

def payoff_barrier_down_and_out_put(paths: np.ndarray, K: float, barrier: float = 80.0) -> np.ndarray:
    hit = np.any(paths[:, 1:] <= barrier, axis=1)
    pf = np.maximum(K - paths[:, -1], 0.0)
    pf[hit] = 0.0
    return pf

def payoff_barrier_up_and_in_call(paths: np.ndarray, K: float, barrier: float = 120.0) -> np.ndarray:
    hit = np.any(paths[:, 1:] >= barrier, axis=1)
    pf = np.maximum(paths[:, -1] - K, 0.0)
    pf[~hit] = 0.0
    return pf

def payoff_barrier_down_and_in_put(paths: np.ndarray, K: float, barrier: float = 80.0) -> np.ndarray:
    hit = np.any(paths[:, 1:] <= barrier, axis=1)
    pf = np.maximum(K - paths[:, -1], 0.0)
    pf[~hit] = 0.0
    return pf


# ---------------------------------------------------------------------------
# MC Pricer (generic)
# ---------------------------------------------------------------------------

def price_mc(
    S: float, K: float, T: float, r: float, q: float, sigma: float,
    payoff_fn: Callable, n_paths: int = 100_000, n_steps: int = 252,
    antithetic: bool = True, seed: int | None = None,
    payoff_kwargs: dict | None = None,
) -> dict:
    """Price an option via Monte Carlo with any payoff function.

    Returns dict: price, std_error, ci_lower, ci_upper, n_paths.
    """
    paths = simulate_paths(S, T, r, q, sigma, n_paths, n_steps, antithetic, seed)
    kwargs = payoff_kwargs or {}
    payoffs = payoff_fn(paths, K, **kwargs)
    disc = np.exp(-r * T)
    pv = disc * payoffs
    mc_price = float(np.mean(pv))
    std_err = float(np.std(pv, ddof=1) / np.sqrt(len(pv)))
    return {
        "price": mc_price,
        "std_error": std_err,
        "ci_lower": mc_price - 1.96 * std_err,
        "ci_upper": mc_price + 1.96 * std_err,
        "n_paths": len(pv),
    }


# ---------------------------------------------------------------------------
# European MC with control variate
# ---------------------------------------------------------------------------

def price_european_mc(
    S: float, K: float, T: float, r: float, q: float, sigma: float,
    option_type: str = "call", n_paths: int = 100_000, n_steps: int = 252,
    control_variate: bool = True, seed: int | None = None,
) -> dict:
    """Price European option via MC with optional control variate.

    Returns dict: price, std_error, ci_lower, ci_upper, n_paths, bs_price, bs_diff.
    """
    payoff_fn = payoff_european_call if option_type == "call" else payoff_european_put
    paths = simulate_paths(S, T, r, q, sigma, n_paths, n_steps, True, seed)
    payoffs = payoff_fn(paths, K)
    disc = np.exp(-r * T)
    pv = disc * payoffs
    bs_analytical = bs_price(S, K, T, r, q, sigma, option_type)

    if control_variate:
        # Use terminal stock price S_T as the control variate
        ST = paths[:, -1]
        expected_ST = S * np.exp((r - q) * T)
        
        # Calculate optimal c* = Cov(pv, S_T) / Var(S_T)
        cov = np.cov(pv, ST)[0, 1]
        var = np.var(ST, ddof=1)
        c_star = cov / var if var > 1e-10 else 0.0
        
        pv_cv = pv - c_star * (ST - expected_ST)
        
        mc_price = float(np.mean(pv_cv))
        std_err = float(np.std(pv_cv, ddof=1) / np.sqrt(len(pv)))
    else:
        mc_price = float(np.mean(pv))
        std_err = float(np.std(pv, ddof=1) / np.sqrt(len(pv)))
    return {
        "price": mc_price,
        "std_error": std_err,
        "ci_lower": mc_price - 1.96 * std_err,
        "ci_upper": mc_price + 1.96 * std_err,
        "n_paths": len(pv),
        "bs_price": bs_analytical,
        "bs_diff": mc_price - bs_analytical,
    }
