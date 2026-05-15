import pytest
import numpy as np
import math
from pricer.models.monte_carlo import price_european_mc
from pricer.models.black_scholes import price as bs_price

class TestMonteCarlo:
    def test_european_mc_converges_to_bs(self):
        """Test that MC price is within 95% CI of the analytical BS price."""
        S, K, T, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.01, 0.20
        res = price_european_mc(S, K, T, r, q, sigma, "call", n_paths=50000, control_variate=False, seed=42)
        
        # Check that BS price falls within the 95% CI (or very close)
        assert res["ci_lower"] <= res["bs_price"] <= res["ci_upper"]

    def test_control_variate_reduces_variance(self):
        """Test that the standard error with CV is smaller than without."""
        S, K, T, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.01, 0.20
        res_raw = price_european_mc(S, K, T, r, q, sigma, "call", n_paths=10000, control_variate=False, seed=42)
        res_cv = price_european_mc(S, K, T, r, q, sigma, "call", n_paths=10000, control_variate=True, seed=42)
        
        # CV should significantly reduce standard error (typically 2x-5x)
        assert res_cv["std_error"] < res_raw["std_error"] * 0.5
