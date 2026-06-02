"""
Tests for the fixed-income bond pricer.
"""

import math
import numpy as np
import pytest

from pricer.models.bonds import (
    dirty_price,
    clean_price,
    yield_to_maturity,
    macaulay_duration,
    modified_duration,
    convexity,
    dv01,
    cash_flow_schedule,
    price_yield_curve,
    bond_analytics,
)


class TestBondPricing:
    """Test bond pricing fundamentals."""

    def test_par_bond_at_par_yield(self):
        """A par bond (coupon = yield) should price at par."""
        # 5% semi-annual coupon, 5% yield, 10 periods
        p = dirty_price(100, 0.05, 0.05, 10, 2)
        assert abs(p - 100.0) < 0.01

    def test_premium_bond(self):
        """Coupon > yield → price > par."""
        p = dirty_price(100, 0.08, 0.05, 10, 2)
        assert p > 100.0

    def test_discount_bond(self):
        """Coupon < yield → price < par."""
        p = dirty_price(100, 0.03, 0.05, 10, 2)
        assert p < 100.0

    def test_zero_coupon_bond(self):
        """Zero coupon bond: P = face / (1 + y/freq)^n."""
        p = dirty_price(100, 0.0, 0.06, 20, 2)
        expected = 100 / (1.03) ** 20
        assert abs(p - expected) < 0.01

    def test_single_period(self):
        """Bond with 1 period remaining: P = (coupon + face) / (1 + y/freq)."""
        p = dirty_price(100, 0.06, 0.04, 1, 2)
        expected = (3 + 100) / (1.02)
        assert abs(p - expected) < 0.01

    def test_price_decreases_with_yield(self):
        """Price should decrease as yield increases."""
        p1 = dirty_price(100, 0.05, 0.03, 20, 2)
        p2 = dirty_price(100, 0.05, 0.07, 20, 2)
        assert p1 > p2

    def test_annual_frequency(self):
        """Annual coupon frequency."""
        p = dirty_price(1000, 0.05, 0.05, 5, 1)
        assert abs(p - 1000.0) < 0.01

    def test_quarterly_frequency(self):
        """Quarterly coupon frequency."""
        p = dirty_price(100, 0.08, 0.08, 20, 4)
        assert abs(p - 100.0) < 0.01


class TestYTM:
    """Test yield to maturity solver."""

    def test_round_trip_par(self):
        """YTM of a par bond should equal the coupon rate."""
        ytm = yield_to_maturity(100, 100, 0.05, 20, 2)
        assert abs(ytm - 0.05) < 1e-6

    def test_round_trip_premium(self):
        """Price at yield y → solve YTM → should get y back."""
        y_input = 0.06
        p = dirty_price(100, 0.05, y_input, 20, 2)
        ytm = yield_to_maturity(p, 100, 0.05, 20, 2)
        assert abs(ytm - y_input) < 1e-6

    def test_round_trip_discount(self):
        """Price at yield y → solve YTM → should get y back."""
        y_input = 0.03
        p = dirty_price(100, 0.05, y_input, 30, 2)
        ytm = yield_to_maturity(p, 100, 0.05, 30, 2)
        assert abs(ytm - y_input) < 1e-6

    def test_zero_coupon_ytm(self):
        """YTM for a zero coupon bond."""
        # Price = 100/(1.03)^20 ≈ 55.37
        p = 100 / 1.03 ** 20
        ytm = yield_to_maturity(p, 100, 0.0, 20, 2)
        assert abs(ytm - 0.06) < 1e-4  # 6% annual = 3% semi-annual


class TestDuration:
    """Test duration calculations."""

    def test_macaulay_positive(self):
        """Macaulay duration should be positive."""
        d = macaulay_duration(100, 0.05, 0.05, 20, 2)
        assert d > 0

    def test_macaulay_less_than_maturity(self):
        """Macaulay duration should be less than total maturity for coupon bonds."""
        d = macaulay_duration(100, 0.05, 0.05, 20, 2)
        maturity_years = 20 / 2
        assert d < maturity_years

    def test_zero_coupon_macaulay_equals_maturity(self):
        """For a zero coupon bond, Macaulay duration = maturity."""
        d = macaulay_duration(100, 0.0, 0.05, 20, 2)
        maturity_years = 20 / 2
        assert abs(d - maturity_years) < 0.01

    def test_modified_less_than_macaulay(self):
        """Modified duration ≤ Macaulay duration."""
        d_mac = macaulay_duration(100, 0.05, 0.05, 20, 2)
        d_mod = modified_duration(100, 0.05, 0.05, 20, 2)
        assert d_mod <= d_mac

    def test_modified_duration_formula(self):
        """D_mod = D_mac / (1 + y/freq)."""
        d_mac = macaulay_duration(100, 0.05, 0.06, 20, 2)
        d_mod = modified_duration(100, 0.05, 0.06, 20, 2)
        expected = d_mac / (1 + 0.03)
        assert abs(d_mod - expected) < 1e-6

    def test_higher_coupon_lower_duration(self):
        """Higher coupon → lower duration (more weight on near cash flows)."""
        d_low = macaulay_duration(100, 0.02, 0.05, 20, 2)
        d_high = macaulay_duration(100, 0.08, 0.05, 20, 2)
        assert d_high < d_low


class TestConvexity:
    """Test convexity calculations."""

    def test_convexity_positive(self):
        """Convexity should be positive for a vanilla bond."""
        c = convexity(100, 0.05, 0.05, 20, 2)
        assert c > 0

    def test_zero_coupon_highest_convexity(self):
        """Zero coupon bond has highest convexity for its maturity."""
        c_zero = convexity(100, 0.0, 0.05, 20, 2)
        c_coupon = convexity(100, 0.05, 0.05, 20, 2)
        assert c_zero > c_coupon


class TestDV01:
    """Test DV01 calculation."""

    def test_dv01_positive(self):
        """DV01 should be positive."""
        d = dv01(100, 0.05, 0.05, 20, 2)
        assert d > 0

    def test_dv01_approximation(self):
        """DV01 should approximate the actual price change for 1bp."""
        p_base = dirty_price(100, 0.05, 0.050, 20, 2)
        p_up = dirty_price(100, 0.05, 0.0501, 20, 2)
        actual_change = abs(p_base - p_up)
        computed_dv01 = dv01(100, 0.05, 0.05, 20, 2)
        assert abs(computed_dv01 - actual_change) / actual_change < 0.05  # within 5%


class TestCashFlowSchedule:
    """Test cash flow schedule generation."""

    def test_schedule_length(self):
        """Schedule should have n_periods entries."""
        cf = cash_flow_schedule(100, 0.06, 10, 2)
        assert len(cf) == 10

    def test_last_period_has_principal(self):
        """Last period should include principal repayment."""
        cf = cash_flow_schedule(100, 0.06, 10, 2)
        assert cf[-1]["principal"] == 100.0

    def test_intermediate_no_principal(self):
        """Non-final periods should have zero principal."""
        cf = cash_flow_schedule(100, 0.06, 10, 2)
        for c in cf[:-1]:
            assert c["principal"] == 0.0

    def test_coupon_amount(self):
        """Coupon per period = face × coupon_rate / freq."""
        cf = cash_flow_schedule(1000, 0.06, 10, 2)
        assert cf[0]["coupon"] == 30.0  # 1000 × 0.06 / 2


class TestPriceYieldCurve:
    """Test price/yield curve generation."""

    def test_returns_arrays(self):
        data = price_yield_curve(100, 0.05, 20, 2)
        assert "yields" in data
        assert "prices" in data
        assert len(data["yields"]) == 150

    def test_inverse_relationship(self):
        """Prices should generally decrease as yields increase."""
        data = price_yield_curve(100, 0.05, 20, 2)
        assert data["prices"][0] > data["prices"][-1]


class TestBondAnalytics:
    """Test the combined analytics function."""

    def test_returns_all_keys(self):
        result = bond_analytics(100, 0.05, 0.05, 20, 2)
        expected_keys = [
            "dirty_price", "macaulay_duration", "modified_duration",
            "convexity", "dv01", "current_yield", "annual_coupon", "cash_flows",
        ]
        for key in expected_keys:
            assert key in result

    def test_par_bond_current_yield(self):
        """For a par bond, current yield ≈ coupon rate."""
        result = bond_analytics(100, 0.05, 0.05, 20, 2)
        assert abs(result["current_yield"] - 0.05) < 1e-4
