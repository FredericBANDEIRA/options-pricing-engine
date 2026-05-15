"""
Multi-leg options strategies builder.

Combines multiple option legs to construct strategies like straddles,
spreads, butterflies, and iron condors. Computes combined P&L curves
and aggregated Greeks.
"""

from dataclasses import dataclass
import numpy as np

from pricer.models.black_scholes import price as bs_price, all_greeks


@dataclass
class Leg:
    """A single option leg in a strategy."""
    option_type: str  # "call" or "put"
    strike: float
    lots: int         # Number of contracts (positive int)
    mult: float       # Multiplier per contract (e.g., 100)
    is_long: bool     # True = bought, False = sold

    def quantity(self) -> float:
        """Signed quantity (negative for short positions)."""
        return float(self.lots * self.mult * (1 if self.is_long else -1))


@dataclass
class Strategy:
    """A multi-leg option strategy."""
    name: str
    legs: list[Leg]

    def add_leg(self, leg: Leg) -> None:
        self.legs.append(leg)


# ---------------------------------------------------------------------------
# Pre-built Strategy Templates
# ---------------------------------------------------------------------------

def bull_call_spread(K_long: float, K_short: float, lots: int = 1, mult: float = 100.0) -> Strategy:
    """Long a lower strike call, short a higher strike call."""
    return Strategy("Bull Call Spread", [
        Leg("call", K_long, lots, mult, True),
        Leg("call", K_short, lots, mult, False)
    ])


def bear_put_spread(K_long: float, K_short: float, lots: int = 1, mult: float = 100.0) -> Strategy:
    """Long a higher strike put, short a lower strike put."""
    return Strategy("Bear Put Spread", [
        Leg("put", K_long, lots, mult, True),
        Leg("put", K_short, lots, mult, False)
    ])


def straddle(K: float, lots: int = 1, mult: float = 100.0) -> Strategy:
    """Long a call and long a put at the same strike."""
    return Strategy("Straddle", [
        Leg("call", K, lots, mult, True),
        Leg("put", K, lots, mult, True)
    ])


def strangle(K_put: float, K_call: float, lots: int = 1, mult: float = 100.0) -> Strategy:
    """Long an OTM put and long an OTM call."""
    return Strategy("Strangle", [
        Leg("put", K_put, lots, mult, True),
        Leg("call", K_call, lots, mult, True)
    ])


def iron_condor(
    K_short_put: float, K_long_put: float,
    K_short_call: float, K_long_call: float,
    lots: int = 1, mult: float = 100.0
) -> Strategy:
    """Short an OTM put, long further OTM put; Short an OTM call, long further OTM call."""
    return Strategy("Iron Condor", [
        Leg("put", K_short_put, lots, mult, False),
        Leg("put", K_long_put, lots, mult, True),
        Leg("call", K_short_call, lots, mult, False),
        Leg("call", K_long_call, lots, mult, True)
    ])


def butterfly_call(K_lower: float, K_middle: float, K_upper: float, lots: int = 1, mult: float = 100.0) -> Strategy:
    """Long 1 lower call, Short 2 middle calls, Long 1 upper call."""
    return Strategy("Call Butterfly", [
        Leg("call", K_lower, lots, mult, True),
        Leg("call", K_middle, lots * 2, mult, False),
        Leg("call", K_upper, lots, mult, True)
    ])


# ---------------------------------------------------------------------------
# Pricing and Analytics
# ---------------------------------------------------------------------------

def strategy_price(strategy: Strategy, S: float, T: float, r: float, q: float, sigma: float) -> float:
    """Compute the total present value (price) of the strategy."""
    total_price = 0.0
    for leg in strategy.legs:
        p = bs_price(S, leg.strike, T, r, q, sigma, leg.option_type)
        total_price += p * leg.quantity()
    return total_price


def strategy_greeks(strategy: Strategy, S: float, T: float, r: float, q: float, sigma: float) -> dict[str, float]:
    """Compute the combined Greeks for the strategy."""
    keys = ["delta", "gamma", "vega", "theta", "rho", "vanna", "charm"]
    total = {k: 0.0 for k in keys}
    
    for leg in strategy.legs:
        greeks = all_greeks(S, leg.strike, T, r, q, sigma, leg.option_type)
        qty = leg.quantity()
        for k in keys:
            total[k] += greeks[k] * qty
            
    return total


def strategy_payoff_at_expiry(strategy: Strategy, S_range: np.ndarray) -> np.ndarray:
    """Compute the strategy's intrinsic payoff value at T=0 across a range of spot prices."""
    payoff = np.zeros_like(S_range, dtype=float)
    
    for leg in strategy.legs:
        if leg.option_type == "call":
            intrinsic = np.maximum(S_range - leg.strike, 0.0)
        else:
            intrinsic = np.maximum(leg.strike - S_range, 0.0)
            
        payoff += intrinsic * leg.quantity()
        
    return payoff


def strategy_pnl_curve(
    strategy: Strategy, S_range: np.ndarray, 
    T: float, r: float, q: float, sigma: float,
    entry_cost: float = 0.0
) -> np.ndarray:
    """Compute the P&L curve before expiry across a range of spot prices.
    
    Parameters
    ----------
    entry_cost : float – The net cost paid to enter the position. 
                 P&L = Current Value - Entry Cost
    """
    current_val = np.zeros_like(S_range, dtype=float)
    
    # We can't use the vectorised _greeks_vectorised here easily because strikes vary per leg,
    # but the number of legs is small (max ~4), so a loop over S_range per leg is fine or we 
    # vectorize the BS formula directly. Let's vectorize it for speed.
    
    from scipy.stats import norm
    sqrt_T = np.sqrt(T)
    exp_qT = np.exp(-q * T)
    exp_rT = np.exp(-r * T)
    
    for leg in strategy.legs:
        d1 = (np.log(S_range / leg.strike) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        
        if leg.option_type == "call":
            p = S_range * exp_qT * norm.cdf(d1) - leg.strike * exp_rT * norm.cdf(d2)
        else:
            p = leg.strike * exp_rT * norm.cdf(-d2) - S_range * exp_qT * norm.cdf(-d1)
            
        current_val += p * leg.quantity()
        
    return current_val - entry_cost
