"""
Plotly chart builders for the Options Pricer.

Generates interactive charts showing option price and Greeks
as functions of Spot price and Volatility.
Each chart displays both Call (blue) and Put (red) curves
with a vertical dashed line at the current parameter value.
"""

import numpy as np
import plotly.graph_objects as go

from pricer.models.black_scholes import price, all_greeks


# ---------------------------------------------------------------------------
# Colour constants
# ---------------------------------------------------------------------------
CALL_COLOR = "#2563eb"
PUT_COLOR = "#dc2626"
GRID_COLOR = "#f0f0f0"
MARKER_COLOR = "#9ca3af"


def _plotly_layout(title: str, xaxis_title: str, yaxis_title: str) -> dict:
    """Standard Plotly layout config."""
    return dict(
        title=dict(text=title, font=dict(size=14, family="Inter", color="#1f2937")),
        xaxis=dict(title=xaxis_title, gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(title=yaxis_title, gridcolor=GRID_COLOR, zeroline=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter", size=12, color="#1f2937"),
        margin=dict(l=50, r=20, t=40, b=50),
        height=350,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
                  n_points: int = 200) -> go.Figure:
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
    fig.add_vline(x=S, line_dash="dash", line_color=MARKER_COLOR, line_width=1)

    # If plotting price, add intrinsic value
    if greek_name == "price":
        intrinsic_call = [max(s - K, 0) for s in S_range]
        intrinsic_put = [max(K - s, 0) for s in S_range]
        fig.add_trace(go.Scatter(
            x=S_range, y=intrinsic_call,
            mode="lines", name="Intrinsic (Call)",
            line=dict(color=CALL_COLOR, width=1, dash="dot"),
            opacity=0.4,
        ))
        fig.add_trace(go.Scatter(
            x=S_range, y=intrinsic_put,
            mode="lines", name="Intrinsic (Put)",
            line=dict(color=PUT_COLOR, width=1, dash="dot"),
            opacity=0.4,
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
                 n_points: int = 200) -> go.Figure:
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
    fig.add_vline(x=sigma * 100, line_dash="dash", line_color=MARKER_COLOR, line_width=1)

    fig.update_layout(**_plotly_layout(
        f"{display_name} vs Vol",
        "Volatility (%)",
        display_name,
    ))

    return fig
