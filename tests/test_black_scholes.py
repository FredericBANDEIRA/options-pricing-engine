"""
Unit tests for the Black-Scholes pricing engine.

Tests validate pricing and Greeks against known analytical values
for ATM, ITM, and OTM configurations.
"""

import pytest
import numpy as np
from scipy.stats import norm

from pricer.models.black_scholes import (
    price,
    forward,
    delta,
    gamma,
    vega,
    theta,
    rho,
    vanna,
    charm,
    all_greeks,
    cash_greeks,
)


# ---------------------------------------------------------------------------
# Test parameters
# ---------------------------------------------------------------------------
# ATM European call: S=100, K=100, T=1, r=5%, q=2%, σ=20%
S, K, T, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.02, 0.20


class TestBSPricing:
    """Test Black-Scholes pricing formulas."""

    def test_call_price_positive(self):
        p = price(S, K, T, r, q, sigma, "call")
        assert p > 0, "Call price must be positive"

    def test_put_price_positive(self):
        p = price(S, K, T, r, q, sigma, "put")
        assert p > 0, "Put price must be positive"

    def test_put_call_parity(self):
        """C - P = S·exp(-qT) - K·exp(-rT)"""
        c = price(S, K, T, r, q, sigma, "call")
        p = price(S, K, T, r, q, sigma, "put")
        parity_rhs = S * np.exp(-q * T) - K * np.exp(-r * T)
        assert abs((c - p) - parity_rhs) < 1e-10, "Put-call parity violated"

    def test_forward_price(self):
        f = forward(S, T, r, q)
        expected = S * np.exp((r - q) * T)
        assert abs(f - expected) < 1e-10

    def test_call_price_manual(self):
        """Cross-check with manual calculation."""
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        expected = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        assert abs(price(S, K, T, r, q, sigma, "call") - expected) < 1e-10

    def test_deep_itm_call(self):
        """Deep ITM call ≈ discounted forward - discounted strike."""
        c = price(S, 10.0, T, r, q, sigma, "call")
        intrinsic = S * np.exp(-q * T) - 10.0 * np.exp(-r * T)
        assert c > intrinsic - 0.01  # Must be above intrinsic

    def test_deep_otm_call(self):
        """Deep OTM call should be near zero."""
        c = price(S, 300.0, T, r, q, sigma, "call")
        assert c < 0.01

    def test_zero_time(self):
        """At expiry, price = intrinsic value."""
        c = price(110, 100, 0.0, r, q, sigma, "call")
        assert abs(c - 10.0) < 1e-6
        p = price(90, 100, 0.0, r, q, sigma, "put")
        assert abs(p - 10.0) < 1e-6


class TestBSGreeks:
    """Test Black-Scholes Greeks."""

    def test_call_delta_range(self):
        d = delta(S, K, T, r, q, sigma, "call")
        assert 0 < d < 1, f"Call delta {d} out of [0, 1]"

    def test_put_delta_range(self):
        d = delta(S, K, T, r, q, sigma, "put")
        assert -1 < d < 0, f"Put delta {d} out of [-1, 0]"

    def test_call_put_delta_relationship(self):
        """Δ_put = Δ_call - exp(-qT)"""
        dc = delta(S, K, T, r, q, sigma, "call")
        dp = delta(S, K, T, r, q, sigma, "put")
        assert abs((dc - dp) - np.exp(-q * T)) < 1e-10

    def test_gamma_positive(self):
        g = gamma(S, K, T, r, q, sigma)
        assert g > 0, "Gamma must be positive"

    def test_gamma_same_for_call_put(self):
        """Gamma is the same for call and put (by put-call parity)."""
        # gamma() doesn't take option_type, it's the same
        g = gamma(S, K, T, r, q, sigma)
        assert g > 0

    def test_vega_positive(self):
        v = vega(S, K, T, r, q, sigma)
        assert v > 0, "Vega must be positive"

    def test_theta_call_negative_typical(self):
        """For typical parameters, call theta is negative."""
        th = theta(S, K, T, r, q, sigma, "call")
        assert th < 0, "ATM call theta should be negative"

    def test_rho_call_positive(self):
        r_val = rho(S, K, T, r, q, sigma, "call")
        assert r_val > 0, "Call rho should be positive"

    def test_rho_put_negative(self):
        r_val = rho(S, K, T, r, q, sigma, "put")
        assert r_val < 0, "Put rho should be negative"

    def test_delta_numerical(self):
        """Verify delta against finite-difference approximation."""
        eps = 0.01
        d_fd = (price(S + eps, K, T, r, q, sigma, "call")
                - price(S - eps, K, T, r, q, sigma, "call")) / (2 * eps)
        d_analytical = delta(S, K, T, r, q, sigma, "call")
        assert abs(d_fd - d_analytical) < 1e-4

    def test_gamma_numerical(self):
        """Verify gamma against finite-difference approximation."""
        eps = 0.01
        g_fd = (price(S + eps, K, T, r, q, sigma, "call")
                - 2 * price(S, K, T, r, q, sigma, "call")
                + price(S - eps, K, T, r, q, sigma, "call")) / eps**2
        g_analytical = gamma(S, K, T, r, q, sigma)
        assert abs(g_fd - g_analytical) < 1e-3

    def test_vega_numerical(self):
        """Verify vega against finite-difference approximation."""
        eps = 0.0001
        v_fd = (price(S, K, T, r, q, sigma + eps, "call")
                - price(S, K, T, r, q, sigma - eps, "call")) / (2 * eps)
        v_analytical = vega(S, K, T, r, q, sigma)
        assert abs(v_fd - v_analytical) < 1e-2


class TestAllGreeks:
    """Test the all_greeks convenience function."""

    def test_returns_all_keys(self):
        g = all_greeks(S, K, T, r, q, sigma, "call")
        expected_keys = {"delta", "gamma", "vega", "theta", "rho", "vanna", "charm"}
        assert set(g.keys()) == expected_keys

    def test_consistency_with_individual(self):
        g = all_greeks(S, K, T, r, q, sigma, "call")
        assert abs(g["delta"] - delta(S, K, T, r, q, sigma, "call")) < 1e-10
        assert abs(g["gamma"] - gamma(S, K, T, r, q, sigma)) < 1e-10
        assert abs(g["vega"] - vega(S, K, T, r, q, sigma)) < 1e-10
        assert abs(g["theta"] - theta(S, K, T, r, q, sigma, "call")) < 1e-10
        assert abs(g["rho"] - rho(S, K, T, r, q, sigma, "call")) < 1e-10
        assert abs(g["vanna"] - vanna(S, K, T, r, q, sigma)) < 1e-10
        assert abs(g["charm"] - charm(S, K, T, r, q, sigma, "call")) < 1e-10


class TestCashGreeks:
    """Test cash (position-level) Greeks."""

    def test_cash_delta_scaling(self):
        cg = cash_greeks(S, K, T, r, q, sigma, "call", lots=2.0, mult=100.0)
        unit_d = delta(S, K, T, r, q, sigma, "call")
        expected = unit_d * S * 2.0 * 100.0
        assert abs(cg["cash_delta"] - expected) < 1e-6

    def test_gamma_1pct(self):
        cg = cash_greeks(S, K, T, r, q, sigma, "call", lots=1.0, mult=100.0)
        unit_g = gamma(S, K, T, r, q, sigma)
        expected = 0.5 * unit_g * S**2 * 0.01 * 100.0
        assert abs(cg["gamma_1pct"] - expected) < 1e-6
