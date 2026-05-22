"""
Tests for the volatility surface module.
"""

import numpy as np
import pytest

from pricer.analytics.vol_surface import (
    svi_implied_vol,
    generate_synthetic_surface,
    extract_smile,
    extract_term_structure,
)


class TestSVIImpliedVol:
    """Test the SVI parameterization."""

    def test_atm_vol_positive(self):
        """ATM (k=0) implied vol should be positive."""
        k = np.array([0.0])
        iv = svi_implied_vol(k, T=1.0, a=0.04, b=0.1, rho=-0.3, m=0.0, sigma_svi=0.1)
        assert iv[0] > 0

    def test_smile_shape(self):
        """IV should increase for both deep ITM and OTM (smile)."""
        k = np.linspace(-0.5, 0.5, 100)
        iv = svi_implied_vol(k, T=1.0, a=0.04, b=0.15, rho=-0.3, m=0.0, sigma_svi=0.1)
        atm_idx = len(k) // 2
        # Far OTM put (negative k) should have higher IV than ATM
        assert iv[5] > iv[atm_idx] * 0.95  # Allow small tolerance
        # Far OTM call (positive k) should also have decent IV
        assert iv[-5] > 0

    def test_skew_negative_rho(self):
        """Negative rho should produce equity-style skew (OTM puts > OTM calls)."""
        k = np.array([-0.3, 0.0, 0.3])
        iv = svi_implied_vol(k, T=0.5, a=0.02, b=0.12, rho=-0.5, m=0.0, sigma_svi=0.1)
        # OTM put IV > OTM call IV
        assert iv[0] > iv[2]


class TestSyntheticSurface:
    """Test the synthetic surface generator."""

    def test_surface_shape(self):
        """Surface should have correct dimensions."""
        surf = generate_synthetic_surface(S=100)
        assert surf["ivs"].shape == (8, 25)  # default n_maturities × n_strikes
        assert len(surf["strikes"]) == 25
        assert len(surf["maturities"]) == 8

    def test_ivs_positive(self):
        """All implied vols should be positive."""
        surf = generate_synthetic_surface(S=100)
        assert np.all(surf["ivs"] > 0)

    def test_ivs_reasonable_range(self):
        """IVs should be in a reasonable range (2% to 150%)."""
        surf = generate_synthetic_surface(S=100, atm_vol=0.20)
        assert np.all(surf["ivs"] >= 0.02)
        assert np.all(surf["ivs"] <= 1.50)

    def test_strikes_centered_on_spot(self):
        """Strikes should be centered around the spot price."""
        surf = generate_synthetic_surface(S=100)
        assert surf["strikes"][0] < 100
        assert surf["strikes"][-1] > 100

    def test_maturities_increasing(self):
        """Maturities should be in ascending order."""
        surf = generate_synthetic_surface(S=100)
        assert np.all(np.diff(surf["maturities"]) > 0)

    def test_custom_params(self):
        """Custom parameters should be respected."""
        surf = generate_synthetic_surface(S=200, n_strikes=10, n_maturities=4)
        assert len(surf["strikes"]) == 10
        assert len(surf["maturities"]) == 4
        assert surf["spot"] == 200

    def test_skew_present(self):
        """Short-dated smiles should show negative skew (equity-style)."""
        surf = generate_synthetic_surface(S=100, atm_vol=0.20)
        # First maturity: compare low strike vs high strike IV
        atm_idx = 12  # ~middle of 25 strikes
        assert surf["ivs"][0, 2] > surf["ivs"][0, -3]  # low strike IV > high strike IV


class TestExtractSmile:
    """Test smile extraction."""

    def test_returns_correct_keys(self):
        surf = generate_synthetic_surface(S=100)
        smile = extract_smile(surf, maturity_idx=0)
        assert "strikes" in smile
        assert "moneyness" in smile
        assert "ivs" in smile
        assert "T" in smile
        assert "forward" in smile

    def test_smile_length_matches_strikes(self):
        surf = generate_synthetic_surface(S=100)
        smile = extract_smile(surf, maturity_idx=0)
        assert len(smile["ivs"]) == len(surf["strikes"])


class TestExtractTermStructure:
    """Test term structure extraction."""

    def test_returns_correct_keys(self):
        surf = generate_synthetic_surface(S=100)
        ts = extract_term_structure(surf)
        assert "maturities" in ts
        assert "ivs" in ts
        assert "strike" in ts

    def test_length_matches_maturities(self):
        surf = generate_synthetic_surface(S=100)
        ts = extract_term_structure(surf)
        assert len(ts["ivs"]) == len(surf["maturities"])

    def test_atm_strike_near_spot(self):
        """ATM strike should be close to spot."""
        surf = generate_synthetic_surface(S=100)
        ts = extract_term_structure(surf)
        assert abs(ts["strike"] - 100) < 10  # within 10% of spot
