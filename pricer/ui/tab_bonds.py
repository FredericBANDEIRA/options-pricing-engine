"""
UI tab for the Fixed-Income Bond Pricer.

Features:
    - Bond parameter inputs (face, coupon, yield, periods, frequency)
    - Key metrics: dirty price, duration, convexity, DV01
    - Price/yield curve chart
    - Cash-flow schedule table
    - YTM solver from market price
"""

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from pricer.models.bonds import (
    bond_analytics,
    dirty_price,
    yield_to_maturity,
    price_yield_curve,
)
from pricer.ui.components import section_header, metric_row


def render_bonds_tab():
    """Render the fixed-income bond pricer tab."""

    st.markdown("### 🏦 Fixed-Income Bond Pricer")
    st.markdown("Price and analyze plain-vanilla fixed-rate bonds.")

    # --- Bond Parameters ---
    col1, col2, col3 = st.columns(3)

    with col1:
        face = st.number_input("Face Value", value=1000.0, min_value=1.0,
                               step=100.0, format="%.0f", key="bond_face")
        coupon_pct = st.number_input("Coupon Rate (%)", value=5.0,
                                     min_value=0.0, max_value=30.0,
                                     step=0.25, format="%.2f", key="bond_coupon")

    with col2:
        ytm_pct = st.number_input("Yield to Maturity (%)", value=5.0,
                                   min_value=-5.0, max_value=30.0,
                                   step=0.25, format="%.2f", key="bond_ytm")
        freq = st.selectbox("Coupon Frequency",
                            options=[1, 2, 4],
                            format_func=lambda x: {1: "Annual", 2: "Semi-annual", 4: "Quarterly"}[x],
                            index=1, key="bond_freq")

    with col3:
        maturity_years = st.number_input("Maturity (years)", value=10.0,
                                         min_value=0.5, max_value=50.0,
                                         step=0.5, format="%.1f", key="bond_maturity")
        n_periods = int(maturity_years * freq)
        st.markdown(f'<span style="font-size:0.8rem; color:#6366f1;">→ {n_periods} coupon periods</span>',
                    unsafe_allow_html=True)

    # --- Compute analytics ---
    coupon_rate = coupon_pct / 100
    ytm = ytm_pct / 100
    analytics = bond_analytics(face, coupon_rate, ytm, n_periods, freq)

    st.markdown("")

    # --- Key Metrics ---
    section_header("Bond Valuation")

    metric_row([
        {"label": "DIRTY PRICE", "value": f"{analytics['dirty_price']:,.2f}",
         "color_class": "call" if analytics['dirty_price'] >= face else "put"},
        {"label": "CURRENT YIELD", "value": f"{analytics['current_yield']*100:.2f}%"},
        {"label": "ANNUAL COUPON", "value": f"{analytics['annual_coupon']:,.2f}", "color_class": "gold"},
        {"label": "YTM", "value": f"{ytm_pct:.2f}%"},
    ])

    st.markdown("")

    # --- Risk Metrics ---
    section_header("Duration & Risk")

    metric_row([
        {"label": "MACAULAY DUR.", "value": f"{analytics['macaulay_duration']:.4f} yrs"},
        {"label": "MODIFIED DUR.", "value": f"{analytics['modified_duration']:.4f}"},
        {"label": "CONVEXITY", "value": f"{analytics['convexity']:.4f}"},
        {"label": "DV01", "value": f"{analytics['dv01']:.4f}", "color_class": "teal"},
    ])

    st.markdown("")

    # --- Price sensitivity interpretation ---
    with st.expander("📖 Sensitivity Interpretation", expanded=False):
        dp_100bp = analytics['modified_duration'] * analytics['dirty_price'] * 0.01
        dp_conv = 0.5 * analytics['convexity'] * analytics['dirty_price'] * (0.01) ** 2
        st.markdown(f"""
        | Scenario | Approximate ΔPrice |
        |----------|-------------------|
        | **+100 bps** (yield ↑ 1%) | **{-dp_100bp + dp_conv:,.2f}** |
        | **−100 bps** (yield ↓ 1%) | **{+dp_100bp + dp_conv:,.2f}** |
        | **+1 bp** (yield ↑ 0.01%) | **{-analytics['dv01']:,.4f}** |

        > *Using: ΔP ≈ −D_mod × P × Δy + ½ × C × P × (Δy)²*
        """)

    # --- YTM Solver ---
    with st.expander("🔍 YTM Solver (from Market Price)", expanded=False):
        st.markdown("Enter a market price to back out the implied yield to maturity.")
        market_price = st.number_input("Market Price", value=float(analytics['dirty_price']),
                                        min_value=0.01, step=1.0, format="%.2f",
                                        key="bond_market_price")
        solved_ytm = yield_to_maturity(market_price, face, coupon_rate, n_periods, freq)
        if np.isnan(solved_ytm):
            st.error("No valid YTM found for this price.")
        else:
            st.success(f"Implied YTM: **{solved_ytm * 100:.4f}%**")

    st.markdown("")

    # --- Charts ---
    col_chart, col_cf = st.columns([3, 2])

    with col_chart:
        section_header("Price / Yield Curve")

        # Generate curve
        py_data = price_yield_curve(face, coupon_rate, n_periods, freq,
                                     yield_min=max(0, ytm - 0.05),
                                     yield_max=ytm + 0.05)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=py_data["yields"] * 100,
            y=py_data["prices"],
            mode="lines",
            name="Price",
            line=dict(color="#6366f1", width=3),
            fill="tozeroy",
            fillcolor="rgba(99,102,241,0.08)",
        ))

        # Mark current point
        fig.add_trace(go.Scatter(
            x=[ytm_pct],
            y=[analytics['dirty_price']],
            mode="markers",
            name="Current",
            marker=dict(size=10, color="#f43f5e", symbol="diamond"),
        ))

        # Mark par
        fig.add_hline(y=face, line_dash="dot", line_color="#94a3b8",
                      line_width=1, opacity=0.5,
                      annotation_text=f"Par ({face:,.0f})",
                      annotation_position="top right")

        fig.update_layout(
            xaxis=dict(title="Yield (%)", gridcolor="rgba(148,163,184,0.12)",
                       zeroline=False),
            yaxis=dict(title="Price", gridcolor="rgba(148,163,184,0.12)",
                       zeroline=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter", size=11, color="#334155"),
            margin=dict(l=50, r=15, t=10, b=40),
            height=380,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=10)),
        )

        st.plotly_chart(fig, width="stretch", key="bond_py_curve")

    # --- Cash Flow Schedule ---
    with col_cf:
        section_header("Cash Flow Schedule")

        cfs = analytics['cash_flows']
        if len(cfs) > 20:
            # Show first 5 and last 5 for very long bonds
            display_cfs = cfs[:5] + [{"period": "...", "time": "...", "coupon": "...",
                                       "principal": "...", "total": "..."}] + cfs[-5:]
        else:
            display_cfs = cfs

        # Build HTML table
        rows_html = ""
        for cf in display_cfs:
            if cf["period"] == "...":
                rows_html += '<tr><td colspan="4" style="text-align:center; color:#94a3b8;">⋮</td></tr>'
            else:
                rows_html += (
                    f'<tr>'
                    f'<td>{cf["period"]}</td>'
                    f'<td>{cf["time"]:.2f}</td>'
                    f'<td>{cf["coupon"]:,.2f}</td>'
                    f'<td style="font-weight:600;">{cf["total"]:,.2f}</td>'
                    f'</tr>'
                )

        st.markdown(f"""
        <table class="greek-table">
            <thead>
                <tr><th>#</th><th>Time (y)</th><th>Coupon</th><th>Total CF</th></tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """, unsafe_allow_html=True)
