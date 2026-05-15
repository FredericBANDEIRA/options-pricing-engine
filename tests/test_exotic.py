import pytest
import math
from pricer.models.exotic import barrier_price, digital_price, asian_geometric_price
from pricer.models.black_scholes import price as bs_price

class TestExotics:
    def test_barrier_in_out_parity(self):
        """Test that Knock-in + Knock-out = Vanilla."""
        S, K, T, r, q, sigma, H = 100.0, 100.0, 1.0, 0.05, 0.01, 0.20, 120.0
        
        vanilla = bs_price(S, K, T, r, q, sigma, "call")
        up_in = barrier_price(S, K, T, r, q, sigma, H, "up-and-in", "call")
        up_out = barrier_price(S, K, T, r, q, sigma, H, "up-and-out", "call")
        
        assert math.isclose(up_in + up_out, vanilla, rel_tol=1e-5)

    def test_digital_put_call_parity(self):
        """Test that digital call + digital put = present value of cash payout."""
        S, K, T, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.01, 0.20
        payout = 1.0
        
        d_call = digital_price(S, K, T, r, q, sigma, "call", "cash-or-nothing", payout)
        d_put = digital_price(S, K, T, r, q, sigma, "put", "cash-or-nothing", payout)
        
        pv_cash = payout * math.exp(-r * T)
        assert math.isclose(d_call + d_put, pv_cash, rel_tol=1e-5)

    def test_asian_geometric_lower_than_vanilla(self):
        """Geometric Asian option should be cheaper than a vanilla European."""
        S, K, T, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.20
        
        vanilla = bs_price(S, K, T, r, q, sigma, "call")
        asian = asian_geometric_price(S, K, T, r, q, sigma, "call")
        
        assert asian < vanilla
