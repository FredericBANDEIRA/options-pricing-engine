"""
Volatility Surface construction and analysis.

Provides two data sources:
    1. Synthetic — generates a realistic vol surface using a simplified SVI
       (Stochastic Volatility Inspired) parameterization.
    2. Market — fetches live option chain data from Yahoo Finance (yfinance)
       and computes implied vols using the Newton-Raphson / Brent solver.

The surface is represented as a structured dict containing:
    - strikes: 1D array of strike prices
    - maturities: 1D array of time-to-maturities (years)
    - ivs: 2D array (len(maturities) × len(strikes)) of implied vols
    - moneyness: 1D array of log(K/F) values for the smile plot
"""

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter
from pricer.models.black_scholes import price as bs_price
from pricer.models.implied_vol import implied_vol


# ---------------------------------------------------------------------------
# SVI parameterization (simplified)
# ---------------------------------------------------------------------------

def _svi_total_variance(k: np.ndarray, a: float, b: float, rho: float,
                        m: float, sigma_svi: float) -> np.ndarray:
    """Raw SVI total implied variance: w(k) = a + b * (rho*(k-m) + sqrt((k-m)^2 + sigma^2)).

    Parameters
    ----------
    k : array – log-moneyness ln(K/F)
    a, b, rho, m, sigma_svi : SVI parameters

    Returns
    -------
    w : array – total implied variance w = sigma^2 * T
    """
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma_svi ** 2))


def svi_implied_vol(k: np.ndarray, T: float, a: float, b: float,
                    rho: float, m: float, sigma_svi: float) -> np.ndarray:
    """Convert SVI total variance to implied vol (annualised).

    Returns σ(k, T) = sqrt(w(k) / T).
    """
    w = _svi_total_variance(k, a, b, rho, m, sigma_svi)
    # Clip to avoid negative variance from numerical noise
    w = np.maximum(w, 1e-8)
    return np.sqrt(w / T)


# ---------------------------------------------------------------------------
# Synthetic surface generator
# ---------------------------------------------------------------------------

def generate_synthetic_surface(
    S: float,
    r: float = 0.05,
    q: float = 0.02,
    atm_vol: float = 0.20,
    n_strikes: int = 25,
    n_maturities: int = 8,
    strike_range: tuple[float, float] = (0.70, 1.30),
) -> dict:
    """Generate a realistic synthetic implied volatility surface.

    Uses a simplified SVI parameterization with term-structure effects:
    - Short-dated options have steeper smiles (higher curvature)
    - Long-dated options have flatter smiles
    - Equity-style negative skew (rho < 0)
    - ATM vol increases slightly with maturity (vol term structure)

    Parameters
    ----------
    S : float – Current spot price
    r : float – Risk-free rate
    q : float – Dividend yield
    atm_vol : float – ATM implied vol (used to anchor the surface)
    n_strikes : int – Number of strike points
    n_maturities : int – Number of maturity slices
    strike_range : tuple – (min, max) as fraction of spot

    Returns
    -------
    dict with keys: strikes, maturities, ivs, moneyness, forwards
    """
    # Maturities: 1 week to 2 years
    maturities = np.array([
        7 / 365, 14 / 365, 1 / 12, 2 / 12, 3 / 12,
        6 / 12, 1.0, 2.0,
    ][:n_maturities])

    # Strikes as fraction of spot
    strike_fracs = np.linspace(strike_range[0], strike_range[1], n_strikes)
    strikes = S * strike_fracs

    # Build the surface
    ivs = np.zeros((len(maturities), len(strikes)))

    for i, T in enumerate(maturities):
        F = S * np.exp((r - q) * T)  # Forward price
        k = np.log(strikes / F)       # Log-moneyness

        # SVI params that vary with maturity (realistic term structure)
        # Short-dated: steep smile; long-dated: flatter
        decay = np.exp(-2.0 * T)  # Controls how fast skew flattens

        a = atm_vol ** 2 * T * 0.95             # Level (near ATM variance)
        b = 0.15 * T ** 0.3                       # Curvature
        rho = -0.40 * (0.5 + 0.5 * decay)         # Skew (more negative short-dated)
        m = -0.02 * decay                          # Minimum variance shift
        sigma_svi_param = 0.10 * (0.3 + 0.7 * T ** 0.5)  # SVI sigma

        iv_slice = svi_implied_vol(k, T, a, b, rho, m, sigma_svi_param)

        # Add a small term-structure tilt (vol slightly higher for longer dates)
        term_adj = atm_vol * 0.03 * np.log(1 + T)
        iv_slice = iv_slice + term_adj

        # Clip to reasonable range
        iv_slice = np.clip(iv_slice, 0.02, 1.50)

        ivs[i, :] = iv_slice

    # Moneyness grid for the first maturity (used in smile plots)
    F0 = S * np.exp((r - q) * maturities[0])
    moneyness = np.log(strikes / F0)

    forwards = np.array([S * np.exp((r - q) * T) for T in maturities])

    return {
        "strikes": strikes,
        "maturities": maturities,
        "ivs": ivs,           # shape: (n_maturities, n_strikes)
        "moneyness": moneyness,
        "forwards": forwards,
        "spot": S,
        "r": r,
        "q": q,
    }


# ---------------------------------------------------------------------------
# Surface smoothing & upsampling
# ---------------------------------------------------------------------------

def smooth_surface(
    surface: dict,
    upsample_strikes: int = 50,
    upsample_maturities: int = 20,
    sigma_smooth: float = 1.2,
    outlier_std: float = 2.5,
) -> dict:
    """Smooth and upsample a vol surface for better 3D rendering.

    Steps:
        1. Remove outlier IVs (beyond outlier_std standard deviations)
        2. Interpolate NaN gaps row-by-row
        3. Upsample to a denser grid using bilinear interpolation
        4. Apply Gaussian smoothing

    Parameters
    ----------
    surface : dict — raw surface from generate_synthetic_surface or fetch_market_surface
    upsample_strikes : int — target number of strike points in output
    upsample_maturities : int — target number of maturity points in output
    sigma_smooth : float — Gaussian kernel sigma (higher = smoother)
    outlier_std : float — remove IVs beyond this many std devs from row median

    Returns
    -------
    dict — new surface with smoothed, upsampled ivs and corresponding grids
    """
    ivs = surface["ivs"].copy()
    strikes = surface["strikes"]
    maturities = surface["maturities"]
    S = surface["spot"]

    # --- Step 1: Outlier removal per maturity row ---
    for i in range(ivs.shape[0]):
        row = ivs[i, :]
        valid = row[~np.isnan(row)]
        if len(valid) < 3:
            continue
        med = np.median(valid)
        std = np.std(valid)
        if std > 0:
            outlier_mask = np.abs(row - med) > outlier_std * std
            ivs[i, outlier_mask] = np.nan

    # --- Step 2: Fill NaN gaps via row-wise linear interpolation ---
    for i in range(ivs.shape[0]):
        row = ivs[i, :]
        valid = ~np.isnan(row)
        if np.sum(valid) >= 2:
            ivs[i, :] = np.interp(
                np.arange(len(row)),
                np.where(valid)[0],
                row[valid],
            )
        elif np.sum(valid) == 1:
            ivs[i, :] = row[valid][0]

    # If surface is too small to interpolate, just smooth and return
    if len(maturities) < 2 or len(strikes) < 4:
        ivs = gaussian_filter(ivs, sigma=sigma_smooth)
        ivs = np.clip(ivs, 0.02, 2.0)
        surface_out = surface.copy()
        surface_out["ivs"] = ivs
        return surface_out

    # --- Step 3: Upsample via 2D interpolation ---
    new_strikes = np.linspace(strikes[0], strikes[-1], upsample_strikes)
    new_maturities = np.linspace(maturities[0], maturities[-1], upsample_maturities)

    interp = RegularGridInterpolator(
        (maturities, strikes), ivs,
        method="linear", bounds_error=False, fill_value=None,
    )

    # Build the upsampled grid
    mat_grid, strike_grid = np.meshgrid(new_maturities, new_strikes, indexing="ij")
    points = np.column_stack([mat_grid.ravel(), strike_grid.ravel()])
    ivs_upsampled = interp(points).reshape(mat_grid.shape)

    # --- Step 4: Gaussian smoothing ---
    ivs_smooth = gaussian_filter(ivs_upsampled, sigma=sigma_smooth)
    ivs_smooth = np.clip(ivs_smooth, 0.02, 2.0)

    # Rebuild derived arrays
    r = surface.get("r", 0.05)
    q = surface.get("q", 0.0)
    F0 = S * np.exp((r - q) * new_maturities[0])
    new_moneyness = np.log(new_strikes / F0)
    new_forwards = np.array([S * np.exp((r - q) * T) for T in new_maturities])

    return {
        "strikes": new_strikes,
        "maturities": new_maturities,
        "ivs": ivs_smooth,
        "moneyness": new_moneyness,
        "forwards": new_forwards,
        "spot": S,
        "r": r,
        "q": q,
        **({"ticker": surface["ticker"]} if "ticker" in surface else {}),
    }


# ---------------------------------------------------------------------------
# Market data surface (yfinance)
# ---------------------------------------------------------------------------

def fetch_market_surface(ticker: str, r: float = 0.05, q: float = 0.0) -> dict | None:
    """Fetch option chain data from Yahoo Finance and build an IV surface.

    Requires yfinance to be installed. Returns None if yfinance is not
    available or the ticker has no options data.

    Parameters
    ----------
    ticker : str – Yahoo Finance ticker symbol (e.g. "AAPL", "SPY")
    r : float – Risk-free rate assumption
    q : float – Dividend yield assumption

    Returns
    -------
    dict with keys: strikes, maturities, ivs, moneyness, forwards, spot, ticker
    or None if data could not be fetched.
    """
    try:
        import yfinance as yf
    except ImportError:
        return None

    try:
        stock = yf.Ticker(ticker)
        S = stock.info.get("currentPrice") or stock.info.get("regularMarketPrice")
        if S is None:
            # Try fast_info as fallback
            S = stock.fast_info.get("lastPrice", None)
        if S is None:
            return None

        expiration_dates = stock.options
        if not expiration_dates:
            return None

        # Take up to 8 expiration dates
        exp_dates = list(expiration_dates[:8])

        from datetime import datetime

        all_strikes = set()
        chain_data = []

        for exp_str in exp_dates:
            try:
                chain = stock.option_chain(exp_str)
                calls = chain.calls
                puts = chain.puts

                exp_date = datetime.strptime(exp_str, "%Y-%m-%d")
                T = max((exp_date - datetime.now()).days / 365.0, 1 / 365)

                for _, row in calls.iterrows():
                    K = row["strike"]
                    mid = (row.get("bid", 0) + row.get("ask", 0)) / 2
                    if mid > 0.01 and 0.5 * S < K < 2.0 * S:
                        all_strikes.add(K)
                        chain_data.append({
                            "K": K, "T": T, "price": mid,
                            "option_type": "call",
                        })

                for _, row in puts.iterrows():
                    K = row["strike"]
                    mid = (row.get("bid", 0) + row.get("ask", 0)) / 2
                    if mid > 0.01 and 0.5 * S < K < 2.0 * S:
                        all_strikes.add(K)
                        chain_data.append({
                            "K": K, "T": T, "price": mid,
                            "option_type": "put",
                        })
            except Exception:
                continue

        if not chain_data:
            return None

        # Build a regular grid
        strikes = np.array(sorted(all_strikes))
        maturities_set = sorted(set(d["T"] for d in chain_data))
        maturities = np.array(maturities_set)

        ivs = np.full((len(maturities), len(strikes)), np.nan)

        for d in chain_data:
            t_idx = np.argmin(np.abs(maturities - d["T"]))
            k_idx = np.argmin(np.abs(strikes - d["K"]))

            iv = implied_vol(d["price"], S, d["K"], d["T"], r, q, d["option_type"])
            if not np.isnan(iv) and 0.01 < iv < 3.0:
                # If we already have a value, average (calls + puts)
                existing = ivs[t_idx, k_idx]
                if np.isnan(existing):
                    ivs[t_idx, k_idx] = iv
                else:
                    ivs[t_idx, k_idx] = (existing + iv) / 2

        # Interpolate NaN gaps in each row
        for i in range(len(maturities)):
            row = ivs[i, :]
            valid = ~np.isnan(row)
            if np.sum(valid) >= 2:
                ivs[i, :] = np.interp(
                    np.arange(len(row)),
                    np.where(valid)[0],
                    row[valid],
                )
            elif np.sum(valid) == 1:
                ivs[i, :] = row[valid][0]
            else:
                ivs[i, :] = 0.20  # fallback

        F0 = S * np.exp((r - q) * maturities[0])
        moneyness = np.log(strikes / F0)
        forwards = np.array([S * np.exp((r - q) * T) for T in maturities])

        raw_surface = {
            "strikes": strikes,
            "maturities": maturities,
            "ivs": ivs,
            "moneyness": moneyness,
            "forwards": forwards,
            "spot": S,
            "r": r,
            "q": q,
            "ticker": ticker,
        }

        return smooth_surface(raw_surface, sigma_smooth=1.5)

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Smile extraction helpers
# ---------------------------------------------------------------------------

def extract_smile(surface: dict, maturity_idx: int = 0) -> dict:
    """Extract a single vol smile (one maturity slice) from the surface.

    Returns dict with: strikes, moneyness, ivs, T, forward
    """
    T = surface["maturities"][maturity_idx]
    ivs = surface["ivs"][maturity_idx, :]
    F = surface["forwards"][maturity_idx]
    k = np.log(surface["strikes"] / F)

    return {
        "strikes": surface["strikes"],
        "moneyness": k,
        "ivs": ivs,
        "T": T,
        "forward": F,
    }


def extract_term_structure(surface: dict, strike_idx: int | None = None) -> dict:
    """Extract the ATM (or specified strike) term structure.

    Returns dict with: maturities, ivs, strike
    """
    if strike_idx is None:
        # Find ATM strike (closest to spot)
        strike_idx = np.argmin(np.abs(surface["strikes"] - surface["spot"]))

    return {
        "maturities": surface["maturities"],
        "ivs": surface["ivs"][:, strike_idx],
        "strike": surface["strikes"][strike_idx],
    }
