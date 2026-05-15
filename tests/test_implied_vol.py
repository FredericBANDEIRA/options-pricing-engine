import pytest
import math
from pricer.models.implied_vol import implied_vol, _validate_market_price
from pricer.models.black_scholes import price as bs_price

class TestImpliedVol:
    def test_round_trip_call(self):
        """Test that IV of a BS price returns the original volatility."""
        S, K, T, r, q, true_sigma = 100.0, 105.0, 1.0, 0.05, 0.01, 0.20
        market_price = bs_price(S, K, T, r, q, true_sigma, "call")
        iv = implied_vol(market_price, S, K, T, r, q, "call")
        assert math.isclose(iv, true_sigma, rel_tol=1e-5)

    def test_round_trip_put(self):
        S, K, T, r, q, true_sigma = 100.0, 95.0, 0.5, 0.03, 0.0, 0.35
        market_price = bs_price(S, K, T, r, q, true_sigma, "put")
        iv = implied_vol(market_price, S, K, T, r, q, "put")
        assert math.isclose(iv, true_sigma, rel_tol=1e-5)

    def test_arbitrage_violation_returns_nan(self):
        """Market price below intrinsic value should return NaN."""
        S, K, T, r, q = 100.0, 90.0, 1.0, 0.0, 0.0
        # Call intrinsic is 10. A price of 9 is arbitrage.
        iv = implied_vol(9.0, S, K, T, r, q, "call")
        assert math.isnan(iv)

    def test_zero_time(self):
        """Zero time to maturity should return NaN."""
        iv = implied_vol(1.0, 100.0, 100.0, 0.0, 0.05, 0.0)
        assert math.isnan(iv)
