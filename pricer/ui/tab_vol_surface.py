"""
UI tab for the Volatility Surface visualization.

Features:
    - 3D interactive Plotly surface (strike × maturity → IV)
    - 2D vol smile slices for individual maturities
    - ATM term structure plot
    - Data source toggle: Synthetic (SVI) or Market (yfinance)
"""

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from pricer.analytics.vol_surface import (
    generate_synthetic_surface,
    fetch_market_surface,
    extract_smile,
    extract_term_structure,
)
from pricer.ui.components import section_header


# ---------------------------------------------------------------------------
# Colour constants
# ---------------------------------------------------------------------------
SURFACE_COLORSCALE = [
    [0.0, "#6366f1"],    # Indigo (low vol)
    [0.25, "#0ea5e9"],   # Sky
    [0.5, "#14b8a6"],    # Teal
    [0.75, "#f59e0b"],   # Amber
    [1.0, "#f43f5e"],    # Rose (high vol)
]

SMILE_COLORS = [
    "#6366f1", "#0ea5e9", "#14b8a6", "#f59e0b",
    "#f43f5e", "#8b5cf6", "#ec4899", "#10b981",
]


def _maturity_label(T: float) -> str:
    """Convert a maturity in years to a human-readable label."""
    days = T * 365
    if days < 14:
        return f"{days:.0f}d"
    elif days < 90:
        return f"{days / 7:.0f}w"
    elif days < 365:
        return f"{T * 12:.0f}m"
    else:
        return f"{T:.1f}y"


def render_vol_surface_tab(S: float, r: float, q: float, sigma: float):
    """Render the volatility surface tab."""

    st.markdown("### 🌊 Volatility Surface")
    st.markdown("Explore the implied volatility surface across strikes and maturities.")

    # --- Data source selection ---
    col_src, col_ticker = st.columns([1, 2])
    with col_src:
        data_source = st.radio(
            "Data Source",
            ["Synthetic (SVI)", "Market (yfinance)"],
            horizontal=True,
            key="vol_surface_source",
        )

    surface = None

    if "Market" in data_source:
        with col_ticker:
            ticker = st.text_input("Ticker Symbol", value="SPY", key="vol_ticker")

        if st.button("Fetch Option Chain", key="fetch_vol"):
            with st.spinner(f"Fetching options data for {ticker}..."):
                surface = fetch_market_surface(ticker, r, q)
                if surface is None:
                    st.error(
                        "Could not fetch data. Make sure `yfinance` is installed "
                        "(`uv add yfinance`) and the ticker is valid."
                    )
                else:
                    st.session_state["vol_surface_data"] = surface
                    st.success(f"Loaded {len(surface['maturities'])} expiries, "
                               f"{len(surface['strikes'])} strikes for {ticker}.")

        # Retrieve cached surface if available
        if surface is None:
            surface = st.session_state.get("vol_surface_data")

    else:
        # Synthetic surface — always available
        surface = generate_synthetic_surface(S, r, q, atm_vol=sigma)

    if surface is None:
        st.info("Select **Synthetic** to view a demo surface, or enter a ticker and click **Fetch** for live data.")
        return

    # --- 3D Surface ---
    section_header("3D Implied Volatility Surface")

    # Prepare data for the 3D surface
    strikes = surface["strikes"]
    maturities = surface["maturities"]
    ivs = surface["ivs"] * 100  # Convert to percentage

    # Create maturity labels for the axis
    mat_labels = [_maturity_label(T) for T in maturities]

    fig_3d = go.Figure(data=[
        go.Surface(
            x=strikes,
            y=maturities * 365,  # Show in days for readability
            z=ivs,
            colorscale=SURFACE_COLORSCALE,
            colorbar=dict(
                title=dict(text="IV (%)", font=dict(size=11)),
                thickness=15,
                len=0.6,
            ),
            hovertemplate=(
                "Strike: %{x:.0f}<br>"
                "Maturity: %{y:.0f} days<br>"
                "IV: %{z:.1f}%<br>"
                "<extra></extra>"
            ),
            contours=dict(
                z=dict(show=True, usecolormap=True, highlightcolor="white", project_z=True),
            ),
        )
    ])

    fig_3d.update_layout(
        scene=dict(
            xaxis=dict(title=dict(text="Strike", font=dict(size=12, color="#475569")),
                       gridcolor="rgba(148,163,184,0.2)"),
            yaxis=dict(title=dict(text="Maturity (days)", font=dict(size=12, color="#475569")),
                       gridcolor="rgba(148,163,184,0.2)"),
            zaxis=dict(title=dict(text="IV (%)", font=dict(size=12, color="#475569")),
                       gridcolor="rgba(148,163,184,0.2)"),
            bgcolor="white",
            camera=dict(eye=dict(x=1.8, y=-1.8, z=1.0)),
        ),
        font=dict(family="Inter", size=11, color="#334155"),
        margin=dict(l=0, r=0, t=30, b=0),
        height=500,
        paper_bgcolor="white",
    )

    st.plotly_chart(fig_3d, width="stretch", key="vol_surface_3d")

    st.markdown("")

    # --- Vol Smile (2D slices) ---
    col_smile, col_term = st.columns(2)

    with col_smile:
        section_header("Volatility Smile")

        # Let user select which maturities to show
        mat_options = {_maturity_label(T): i for i, T in enumerate(maturities)}
        selected_mats = st.multiselect(
            "Maturities to display",
            options=list(mat_options.keys()),
            default=list(mat_options.keys())[:4],
            key="smile_mats",
        )

        fig_smile = go.Figure()

        for j, mat_label in enumerate(selected_mats):
            idx = mat_options[mat_label]
            smile = extract_smile(surface, idx)

            fig_smile.add_trace(go.Scatter(
                x=smile["strikes"],
                y=smile["ivs"] * 100,
                mode="lines",
                name=mat_label,
                line=dict(color=SMILE_COLORS[j % len(SMILE_COLORS)], width=2.5),
            ))

        # Mark current spot
        fig_smile.add_vline(
            x=S, line_dash="dash", line_color="#94a3b8",
            line_width=1, opacity=0.6,
            annotation_text="Spot", annotation_position="top",
        )

        fig_smile.update_layout(
            xaxis=dict(title="Strike", gridcolor="rgba(148,163,184,0.12)",
                       zeroline=False),
            yaxis=dict(title="Implied Vol (%)", gridcolor="rgba(148,163,184,0.12)",
                       zeroline=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter", size=11, color="#334155"),
            margin=dict(l=50, r=15, t=10, b=40),
            height=350,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=10)),
        )

        st.plotly_chart(fig_smile, width="stretch", key="vol_smile")

    # --- ATM Term Structure ---
    with col_term:
        section_header("ATM Term Structure")

        ts = extract_term_structure(surface)
        mat_days = ts["maturities"] * 365

        fig_ts = go.Figure()

        fig_ts.add_trace(go.Scatter(
            x=mat_days,
            y=ts["ivs"] * 100,
            mode="lines+markers",
            name=f"K = {ts['strike']:.0f}",
            line=dict(color="#6366f1", width=2.5),
            marker=dict(size=7, color="#6366f1"),
        ))

        # Reference line at current flat vol
        fig_ts.add_hline(
            y=sigma * 100, line_dash="dot", line_color="#f59e0b",
            line_width=1.5, opacity=0.7,
            annotation_text=f"Flat σ = {sigma*100:.0f}%",
            annotation_position="top right",
        )

        fig_ts.update_layout(
            xaxis=dict(title="Maturity (days)", gridcolor="rgba(148,163,184,0.12)",
                       zeroline=False),
            yaxis=dict(title="Implied Vol (%)", gridcolor="rgba(148,163,184,0.12)",
                       zeroline=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter", size=11, color="#334155"),
            margin=dict(l=50, r=15, t=10, b=40),
            height=350,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=10)),
        )

        st.plotly_chart(fig_ts, width="stretch", key="vol_term_structure")

    # --- Surface statistics ---
    st.markdown("")
    section_header("Surface Statistics")

    ivs_pct = surface["ivs"] * 100
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Min IV", f"{np.nanmin(ivs_pct):.1f}%")
    col2.metric("Max IV", f"{np.nanmax(ivs_pct):.1f}%")
    col3.metric("ATM IV", f"{ivs_pct[0, len(strikes)//2]:.1f}%")

    # Skew: 25Δ put IV - 25Δ call IV (approximate via 90% and 110% strikes)
    atm_idx = len(strikes) // 2
    low_idx = max(0, atm_idx - atm_idx // 2)
    high_idx = min(len(strikes) - 1, atm_idx + atm_idx // 2)
    skew_1m = ivs_pct[0, low_idx] - ivs_pct[0, high_idx]
    col4.metric("Skew (1st expiry)", f"{skew_1m:+.1f}%")

    # Term structure slope
    if len(maturities) >= 2:
        ts_slope = ivs_pct[-1, atm_idx] - ivs_pct[0, atm_idx]
        col5.metric("Term Spread", f"{ts_slope:+.1f}%")
    else:
        col5.metric("Term Spread", "N/A")
