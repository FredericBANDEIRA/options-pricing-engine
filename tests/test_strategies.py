import pytest
import numpy as np
import math
from pricer.models.strategies import (
    bull_call_spread, straddle, iron_condor, 
    strategy_price, strategy_payoff_at_expiry
)

class TestStrategies:
    def test_straddle_price(self):
        """Test that a straddle price equals Call + Put price."""
        from pricer.models.black_scholes import price as bs_price
        S, K, T, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.01, 0.20
        
        strat = straddle(K)
        strat_p = strategy_price(strat, S, T, r, q, sigma)
        
        call_p = bs_price(S, K, T, r, q, sigma, "call")
        put_p = bs_price(S, K, T, r, q, sigma, "put")
        
        # Default multiplier is 100
        assert math.isclose(strat_p, (call_p + put_p) * 100, rel_tol=1e-5)

    def test_bull_call_spread_payoff(self):
        """Test max payoff of a bull call spread is (K_short - K_long) * multiplier."""
        strat = bull_call_spread(100.0, 110.0, lots=1, mult=1.0)
        
        # Below K_long -> 0
        assert strategy_payoff_at_expiry(strat, np.array([90.0]))[0] == 0.0
        
        # Above K_short -> Max profit = 110 - 100 = 10
        assert strategy_payoff_at_expiry(strat, np.array([120.0]))[0] == 10.0

    def test_iron_condor_max_loss(self):
        """Test the bounds of an iron condor payoff."""
        # Iron Condor: Short Put 90, Long Put 80; Short Call 110, Long Call 120
        strat = iron_condor(90.0, 80.0, 110.0, 120.0, lots=1, mult=1.0)
        
        # In the middle (100) -> 0 intrinsic value at expiry (max profit = premium received)
        assert strategy_payoff_at_expiry(strat, np.array([100.0]))[0] == 0.0
        
        # Way below (70) -> Long Put kicks in, capping loss to (90-80) = -10
        assert strategy_payoff_at_expiry(strat, np.array([70.0]))[0] == -10.0
        
        # Way above (130) -> Long Call kicks in, capping loss to (120-110) = -10
        assert strategy_payoff_at_expiry(strat, np.array([130.0]))[0] == -10.0
