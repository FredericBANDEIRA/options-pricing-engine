"""
Plotly chart builders for the Options Pricer.

Generates interactive charts showing option price and Greeks
as functions of Spot price and Volatility.
Each chart displays both Call (blue) and Put (red) curves
with a vertical dashed line at the current parameter value.

Charts are rendered in a 2-column × N-row grid showing all
Greeks simultaneously (Price, Delta, Gamma, Vega, Theta, Rho, Vanna, Charm).
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm

from pricer.models.black_scholes import price, all_greeks


# ---------------------------------------------------------------------------
# Colour constants — matches the vibrant light theme
# ---------------------------------------------------------------------------
CALL_COLOR = "#0ea5e9"       # Sky-500
PUT_COLOR = "#f43f5e"        # Rose-500
GRID_COLOR = "rgba(148,163,184,0.12)"
MARKER_COLOR = "#94a3b8"
BG_COLOR = "rgba(255,255,255,0)"   # Transparent to show page background
TITLE_COLOR = "#334155"


def _plotly_layout(title: str, xaxis_title: str, yaxis_title: str) -> dict:
    """Standard Plotly layout config with vibrant styling."""
    return dict(
        title=dict(
            text=title,
            font=dict(size=13, family="Inter", color=TITLE_COLOR, weight=700),
        ),
        xaxis=dict(
            title=xaxis_title,
            gridcolor=GRID_COLOR,
            zeroline=False,
            title_font=dict(size=11, color="#64748b"),
            tickfont=dict(size=10, color="#94a3b8"),
        ),
        yaxis=dict(
            title=yaxis_title,
            gridcolor=GRID_COLOR,
            zeroline=False,
            title_font=dict(size=11, color="#64748b"),
            tickfont=dict(size=10, color="#94a3b8"),
        ),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter", size=11, color=TITLE_COLOR),
        margin=dict(l=45, r=15, t=35, b=40),
        height=310,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10),
        ),
        hoverlabel=dict(bgcolor="white", font_size=11, font_family="Inter"),
    )


def _extract_greek(S: float, K: float, T: float, r: float, q: float,
                   sigma: float, greek_name: str, option_type: str) -> float:
    """Extract a single greek value, handling 'price' as a special case."""
    if greek_name == "price":
        return price(S, K, T, r, q, sigma, option_type)
    greeks = all_greeks(S, K, T, r, q, sigma, option_type)
    return greeks.get(greek_name, 0.0)


# ---------------------------------------------------------------------------
# Chart: Greek vs Spot
# ---------------------------------------------------------------------------

def chart_vs_spot(S: float, K: float, T: float, r: float, q: float,
                  sigma: float, greek_name: str = "price",
                  n_points: int = 150) -> go.Figure:
    """Generate a chart of the selected Greek as a function of Spot price.

    Sweeps Spot from 50% to 150% of current value.
    Shows both call and put curves.
    """
    S_range = np.linspace(S * 0.5, S * 1.5, n_points)

    call_values = [_extract_greek(s, K, T, r, q, sigma, greek_name, "call") for s in S_range]
    put_values = [_extract_greek(s, K, T, r, q, sigma, greek_name, "put") for s in S_range]

    display_name = greek_name.capitalize() if greek_name != "price" else "Price"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=S_range, y=call_values,
        mode="lines", name="Call",
        line=dict(color=CALL_COLOR, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=S_range, y=put_values,
        mode="lines", name="Put",
        line=dict(color=PUT_COLOR, width=2.5),
    ))

    # Vertical line at current spot
    fig.add_vline(x=S, line_dash="dash", line_color=MARKER_COLOR, line_width=1, opacity=0.6)

    # If plotting price, add intrinsic value
    if greek_name == "price":
        intrinsic_call = [max(s - K, 0) for s in S_range]
        intrinsic_put = [max(K - s, 0) for s in S_range]
        fig.add_trace(go.Scatter(
            x=S_range, y=intrinsic_call,
            mode="lines", name="Intrinsic (C)",
            line=dict(color=CALL_COLOR, width=1.2, dash="dot"),
            opacity=0.35,
        ))
        fig.add_trace(go.Scatter(
            x=S_range, y=intrinsic_put,
            mode="lines", name="Intrinsic (P)",
            line=dict(color=PUT_COLOR, width=1.2, dash="dot"),
            opacity=0.35,
        ))

    fig.update_layout(**_plotly_layout(
        f"{display_name} vs Spot",
        "Spot Price",
        display_name,
    ))

    return fig


# ---------------------------------------------------------------------------
# Chart: Greek vs Volatility
# ---------------------------------------------------------------------------

def chart_vs_vol(S: float, K: float, T: float, r: float, q: float,
                 sigma: float, greek_name: str = "price",
                 n_points: int = 150) -> go.Figure:
    """Generate a chart of the selected Greek as a function of Volatility.

    Sweeps σ from 1% to 80%.
    Shows both call and put curves.
    """
    vol_range = np.linspace(0.01, 0.80, n_points)

    call_values = [_extract_greek(S, K, T, r, q, v, greek_name, "call") for v in vol_range]
    put_values = [_extract_greek(S, K, T, r, q, v, greek_name, "put") for v in vol_range]

    display_name = greek_name.capitalize() if greek_name != "price" else "Price"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=vol_range * 100, y=call_values,
        mode="lines", name="Call",
        line=dict(color=CALL_COLOR, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=vol_range * 100, y=put_values,
        mode="lines", name="Put",
        line=dict(color=PUT_COLOR, width=2.5),
    ))

    # Vertical line at current vol
    fig.add_vline(x=sigma * 100, line_dash="dash", line_color=MARKER_COLOR, line_width=1, opacity=0.6)

    fig.update_layout(**_plotly_layout(
        f"{display_name} vs Vol",
        "Volatility (%)",
        display_name,
    ))

    return fig


# ---------------------------------------------------------------------------
# All-Greeks grid generator
# ---------------------------------------------------------------------------

ALL_GREEKS_LIST = ["price", "delta", "gamma", "vega", "theta", "rho", "vanna", "charm"]



def _greeks_vectorised(
    S_arr: np.ndarray, K: float, T: float, r: float, q: float,
    sigma_arr: np.ndarray,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Compute all Greeks for arrays of S and/or sigma using NumPy broadcasting.

    Either S_arr or sigma_arr (or both) can be arrays.
    Returns dict mapping greek_name -> (call_values, put_values).
    """
    sqrt_T = np.sqrt(T)
    d1 = (np.log(S_arr / K) + (r - q + 0.5 * sigma_arr**2) * T) / (sigma_arr * sqrt_T)
    d2 = d1 - sigma_arr * sqrt_T

    exp_qT = np.exp(-q * T)
    exp_rT = np.exp(-r * T)
    nd1 = norm.pdf(d1)
    Nd1 = norm.cdf(d1)
    Nd2 = norm.cdf(d2)
    Nmd1 = norm.cdf(-d1)
    Nmd2 = norm.cdf(-d2)

    # Price
    call_price = S_arr * exp_qT * Nd1 - K * exp_rT * Nd2
    put_price = K * exp_rT * Nmd2 - S_arr * exp_qT * Nmd1

    # Delta
    call_delta = exp_qT * Nd1
    put_delta = exp_qT * (Nd1 - 1.0)

    # Gamma (same for call/put)
    gamma_val = exp_qT * nd1 / (S_arr * sigma_arr * sqrt_T)

    # Vega (same)
    vega_val = S_arr * exp_qT * nd1 * sqrt_T

    # Theta
    term1 = -(S_arr * nd1 * sigma_arr * exp_qT) / (2 * sqrt_T)
    call_theta = term1 - r * K * exp_rT * Nd2 + q * S_arr * exp_qT * Nd1
    put_theta = term1 + r * K * exp_rT * Nmd2 - q * S_arr * exp_qT * Nmd1

    # Rho
    call_rho = K * T * exp_rT * Nd2
    put_rho = -K * T * exp_rT * Nmd2

    # Vanna (same)
    vanna_val = -exp_qT * nd1 * d2 / sigma_arr

    # Charm
    charm_common = -exp_qT * nd1 * (
        2 * (r - q) * T - d2 * sigma_arr * sqrt_T
    ) / (2 * T * sigma_arr * sqrt_T)
    call_charm = charm_common - q * exp_qT * Nd1
    put_charm = charm_common + q * exp_qT * Nmd1

    return {
        "price": (call_price, put_price),
        "delta": (call_delta, put_delta),
        "gamma": (gamma_val, gamma_val),
        "vega": (vega_val, vega_val),
        "theta": (call_theta, put_theta),
        "rho": (call_rho, put_rho),
        "vanna": (vanna_val, vanna_val),
        "charm": (call_charm, put_charm),
    }


@st.cache_resource
def build_all_charts(S: float, K: float, T: float, r: float, q: float,
                     sigma: float) -> dict[str, tuple[go.Figure, go.Figure]]:
    """Pre-compute all charts for the grid display.

    Returns a dict mapping greek_name -> (fig_vs_spot, fig_vs_vol).
    Computation is fully vectorised with NumPy — all Greeks are
    computed across the entire sweep in a single pass.
    """
    n_points = 120

    # --- Spot sweep (vectorised) ---
    S_range = np.linspace(S * 0.5, S * 1.5, n_points)
    spot_data = _greeks_vectorised(S_range, K, T, r, q, sigma)

    # --- Vol sweep (vectorised) ---
    vol_range = np.linspace(0.01, 0.80, n_points)
    vol_data = _greeks_vectorised(S, K, T, r, q, vol_range)

    # --- Intrinsic values (vectorised) ---
    intrinsic_call = np.maximum(S_range - K, 0)
    intrinsic_put = np.maximum(K - S_range, 0)

    # --- Build figures ---
    result = {}
    for g in ALL_GREEKS_LIST:
        display = g.capitalize() if g != "price" else "Price"
        call_spot, put_spot = spot_data[g]
        call_vol, put_vol = vol_data[g]

        # vs Spot
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=S_range, y=call_spot, mode="lines",
                                   name="Call", line=dict(color=CALL_COLOR, width=2.5),
                                   showlegend=(g == "price")))
        fig_s.add_trace(go.Scatter(x=S_range, y=put_spot, mode="lines",
                                   name="Put", line=dict(color=PUT_COLOR, width=2.5),
                                   showlegend=(g == "price")))
        fig_s.add_vline(x=S, line_dash="dash", line_color=MARKER_COLOR, line_width=1, opacity=0.5)

        if g == "price":
            fig_s.add_trace(go.Scatter(x=S_range, y=intrinsic_call, mode="lines",
                                       name="Intrinsic (C)",
                                       line=dict(color=CALL_COLOR, width=1, dash="dot"),
                                       opacity=0.3, showlegend=False))
            fig_s.add_trace(go.Scatter(x=S_range, y=intrinsic_put, mode="lines",
                                       name="Intrinsic (P)",
                                       line=dict(color=PUT_COLOR, width=1, dash="dot"),
                                       opacity=0.3, showlegend=False))

        fig_s.update_layout(**_plotly_layout(f"{display} vs Spot", "Spot", display))

        # vs Vol
        fig_v = go.Figure()
        fig_v.add_trace(go.Scatter(x=vol_range * 100, y=call_vol, mode="lines",
                                   name="Call", line=dict(color=CALL_COLOR, width=2.5),
                                   showlegend=(g == "price")))
        fig_v.add_trace(go.Scatter(x=vol_range * 100, y=put_vol, mode="lines",
                                   name="Put", line=dict(color=PUT_COLOR, width=2.5),
                                   showlegend=(g == "price")))
        fig_v.add_vline(x=sigma * 100, line_dash="dash", line_color=MARKER_COLOR, line_width=1, opacity=0.5)
        fig_v.update_layout(**_plotly_layout(f"{display} vs Vol", "Vol (%)", display))

        result[g] = (fig_s, fig_v)

    return result
