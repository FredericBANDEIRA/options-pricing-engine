"""
Unit tests for the CRR binomial tree pricing engine.

Tests validate:
- Convergence to BS price for European options
- American price ≥ European price
- Early exercise premium for ITM puts
"""

import pytest
import numpy as np

from pricer.models.binomial import price, early_exercise_analysis
from pricer.models.black_scholes import price as bs_price


# ---------------------------------------------------------------------------
# Test parameters
# ---------------------------------------------------------------------------
S, K, T, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.02, 0.20


class TestBinomialPricing:
    """Test CRR binomial tree pricing."""

    def test_european_call_converges_to_bs(self):
        """European call from tree should converge to BS price."""
        tree_price = price(S, K, T, r, q, sigma, "call", n_steps=500, style="european")
        bs = bs_price(S, K, T, r, q, sigma, "call")
        assert abs(tree_price - bs) < 0.05, (
            f"Tree price {tree_price:.4f} vs BS {bs:.4f} differ by more than 0.05"
        )

    def test_european_put_converges_to_bs(self):
        """European put from tree should converge to BS price."""
        tree_price = price(S, K, T, r, q, sigma, "put", n_steps=500, style="european")
        bs = bs_price(S, K, T, r, q, sigma, "put")
        assert abs(tree_price - bs) < 0.05

    def test_american_call_geq_european(self):
        """American call ≥ European call."""
        am = price(S, K, T, r, q, sigma, "call", n_steps=200, style="american")
        eu = price(S, K, T, r, q, sigma, "call", n_steps=200, style="european")
        assert am >= eu - 1e-6

    def test_american_put_geq_european(self):
        """American put ≥ European put."""
        am = price(S, K, T, r, q, sigma, "put", n_steps=200, style="american")
        eu = price(S, K, T, r, q, sigma, "put", n_steps=200, style="european")
        assert am >= eu - 1e-6

    def test_deep_itm_put_early_exercise_premium(self):
        """Deep ITM American put should have a meaningful early exercise premium."""
        # S=100, K=150, so put is deep ITM
        am = price(100, 150, 1.0, 0.05, 0.0, 0.20, "put", n_steps=200, style="american")
        eu = bs_price(100, 150, 1.0, 0.05, 0.0, 0.20, "put")
        premium = am - eu
        assert premium > 0.1, f"Expected meaningful early exercise premium, got {premium:.4f}"

    def test_no_dividend_call_no_early_exercise(self):
        """American call on non-dividend-paying stock ≈ European call."""
        am = price(S, K, T, r, 0.0, sigma, "call", n_steps=200, style="american")
        eu = bs_price(S, K, T, r, 0.0, sigma, "call")
        assert abs(am - eu) < 0.05, "American call without dividends should equal European"

    def test_at_expiry(self):
        """At T=0, price = intrinsic value."""
        assert abs(price(110, 100, 0.0, r, q, sigma, "call") - 10.0) < 1e-8
        assert abs(price(90, 100, 0.0, r, q, sigma, "put") - 10.0) < 1e-8
        assert abs(price(90, 100, 0.0, r, q, sigma, "call") - 0.0) < 1e-8


class TestEarlyExerciseAnalysis:
    """Test the early exercise analysis function."""

    def test_returns_all_keys(self):
        result = early_exercise_analysis(S, K, T, r, q, sigma, "put")
        expected_keys = {"european_bs", "european_tree", "american_tree",
                         "early_exercise_premium", "premium_pct"}
        assert set(result.keys()) == expected_keys

    def test_premium_non_negative(self):
        result = early_exercise_analysis(S, K, T, r, q, sigma, "put")
        assert result["early_exercise_premium"] >= -0.01  # Allow tiny numerical noise

    def test_tree_converges_to_bs(self):
        result = early_exercise_analysis(S, K, T, r, q, sigma, "call", n_steps=500)
        assert abs(result["european_tree"] - result["european_bs"]) < 0.05
