"""
Options Pricer — Streamlit Entry Point

A professional-grade vanilla options pricer featuring:
- Black-Scholes closed-form pricing with full analytical Greeks
- CRR binomial tree for American early exercise analysis
- Gamma PnL calculator and Gamma→Theta bill
- Interactive Plotly charts (Greeks vs Spot and vs Vol)
- Quant interview questions bank
"""

import json
import pathlib

import streamlit as st

from pricer.models import black_scholes as bs
from pricer.models import binomial
from pricer.ui.styles import inject_css
from pricer.ui.sidebar import render_sidebar
from pricer.ui.components import (
    section_header,
    metric_row,
    greek_table,
    gamma_pnl_row,
    early_exercise_table,
    gamma_theta_table,
)
from pricer.ui.charts import chart_vs_spot, chart_vs_vol, build_all_charts, ALL_GREEKS_LIST

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Options Pricer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ---------------------------------------------------------------------------
# Sidebar — Parameters
# ---------------------------------------------------------------------------
params = render_sidebar()
S = params["S"]
K = params["K"]
T = params["T"]
r = params["r"]
q = params["q"]
sigma = params["sigma"]
opt = params["option_type"]
lots = params["lots"]
mult = params["mult"]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="app-header">Options Pricer</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_pricer, tab_interview = st.tabs(["📊 Derivatives Pricer", "🎓 Interview Questions"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: Derivatives Pricer
# ═══════════════════════════════════════════════════════════════════════════
with tab_pricer:

    # Compute everything once
    cash = bs.cash_greeks(S, K, T, r, q, sigma, opt, lots, mult)
    unit = cash["unit"]

    # ── PRICING ───────────────────────────────────────────────────────────
    section_header("Pricing")
    metric_row([
        {"label": "BS PRICE", "value": f"{cash['bs_price']:.4f}"},
        {"label": "FORWARD", "value": f"{cash['forward']:.4f}", "color_class": "gold"},
        {"label": "CASH DELTA", "value": f"{cash['cash_delta']:,.2f}"},
        {"label": "DELTA HEDGE", "value": f"{cash['delta_hedge']:,.1f} shrs"},
        {"label": "Δ T+1D", "value": f"{cash['delta_t1d']:,.2f} shrs/day"},
    ])

    st.markdown("")

    # ── CASH GREEKS ───────────────────────────────────────────────────────
    section_header("Cash Greeks")
    metric_row([
        {"label": "GAMMA / 1%", "value": f"{cash['gamma_1pct']:,.2f}"},
        {"label": "THETA / DAY", "value": f"{cash['theta_day']:,.2f}"},
        {"label": "VEGA / 1%", "value": f"{cash['vega_1pct']:,.2f}"},
        {"label": "CHARM / DAY", "value": f"{cash['charm_day']:,.2f}"},
        {"label": "VANNA / 1%", "value": f"{cash['vanna_1pct']:,.2f}"},
        {"label": "RHO / 1%", "value": f"{cash['rho_1pct']:,.2f}"},
    ])

    st.markdown("")

    # ── GAMMA PNL CALCULATOR ──────────────────────────────────────────────
    with st.expander("📐 Gamma PnL Calculator", expanded=False):
        col_move, col_results = st.columns([1, 3])
        with col_move:
            st.markdown('<div class="param-label">Spot move %</div>', unsafe_allow_html=True)
            spot_move = st.number_input("Spot move %", value=1.0, step=0.25,
                                        format="%.2f", label_visibility="collapsed",
                                        key="spot_move")
        with col_results:
            gpnl = bs.gamma_pnl(S, K, T, r, q, sigma, opt, spot_move, lots, mult)
            gamma_pnl_row(gpnl)

    # ── TRADING SHORTCUTS ─────────────────────────────────────────────────
    with st.expander("⚡ Trading Shortcuts", expanded=False):
        daily_be = sigma / (252 ** 0.5) * 100
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | **Daily breakeven move** | {daily_be:.2f}% |
        | **Annual vol → Daily vol** | {sigma*100:.1f}% / √252 ≈ {daily_be:.2f}% |
        | **σ/16 rule** | {sigma*100:.1f}% / 16 ≈ {sigma*100/16:.2f}% |
        | **1-σ daily move ($)** | ${S * sigma / 252**0.5:,.2f} |
        """)

    # ── QUICK CALC — GAMMA → THETA BILL ──────────────────────────────────
    with st.expander("🧮 Quick Calc — Gamma → Theta Bill", expanded=False):
        gt = bs.gamma_theta_bill(S, K, T, r, q, sigma, opt, lots, mult)
        gamma_theta_table(gt)
        st.markdown("""
        > **Interpretation**: The ratio shows how much of your actual theta is
        > explained by your gamma exposure. For ATM short-dated options, this
        > ratio approaches 1.0, confirming that theta ≈ ½ Γ S² σ² / 365.
        """)

    # ── EARLY EXERCISE — AMERICAN STYLE ───────────────────────────────────
    with st.expander("🇺🇸 Early Exercise Analysis — American Style", expanded=False):
        if T > 0:
            ee = binomial.early_exercise_analysis(S, K, T, r, q, sigma, opt)
            early_exercise_table(ee)
            if ee["early_exercise_premium"] > 0.001:
                st.info(f"Early exercise premium of **{ee['early_exercise_premium']:.4f}** "
                        f"({ee['premium_pct']:.2f}% of European price). "
                        f"American-style pricing is relevant for this configuration.")
            else:
                st.success("Early exercise premium is negligible. "
                           "European and American prices are essentially equal.")
        else:
            st.warning("Option has expired (T = 0). No early exercise analysis available.")

    st.markdown("")

    # ── UNIT GREEKS ───────────────────────────────────────────────────────
    section_header("Unit Greeks")
    greek_table(unit)

    st.markdown("")

    # ── CHARTS ────────────────────────────────────────────────────────────
    section_header("Charts")

    # Column headers
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown('<div class="chart-section-title">vs Spot</div>', unsafe_allow_html=True)
    with col_h2:
        st.markdown('<div class="chart-section-title">vs Volatility</div>', unsafe_allow_html=True)

    # Build all charts in one efficient pass
    all_charts = build_all_charts(S, K, T, r, q, sigma)

    # Render 6 rows × 2 columns
    for greek_name in ALL_GREEKS_LIST:
        fig_spot, fig_vol = all_charts[greek_name]
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_spot, width="stretch", key=f"spot_{greek_name}")
        with col2:
            st.plotly_chart(fig_vol, width="stretch", key=f"vol_{greek_name}")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: Interview Questions
# ═══════════════════════════════════════════════════════════════════════════
with tab_interview:
    st.markdown("### 🎓 Quant Interview Questions")
    st.markdown("Test your knowledge with these derivatives and quantitative finance questions.")

    # Load questions
    questions_path = pathlib.Path(__file__).parent / "data" / "interview_questions.json"
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # Group by category
    categories: dict[str, list] = {}
    for q_item in questions:
        cat = q_item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(q_item)

    # Render
    for cat, items in categories.items():
        st.markdown(f'<div class="interview-category">{cat}</div>', unsafe_allow_html=True)
        for i, item in enumerate(items):
            with st.expander(f"Q: {item['question']}"):
                st.markdown(item["answer"])
